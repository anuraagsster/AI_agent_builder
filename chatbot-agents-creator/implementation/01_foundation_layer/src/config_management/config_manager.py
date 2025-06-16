"""
Configuration Management Module

This module provides classes for managing configuration settings throughout the system.
It supports hierarchical configuration, validation, environment-specific settings,
and dynamic updates.
"""

import os
import json
import yaml
import logging
import jsonschema
from typing import Any, Dict, Optional, List, Union

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False


class ConfigSource:
    """Base class for configuration sources"""
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from this source
        
        Returns:
            Dict containing the configuration
        """
        raise NotImplementedError
        
    def save(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to this source
        
        Args:
            config: Configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError


class FileConfigSource(ConfigSource):
    """File-based configuration source"""
    
    def __init__(self, file_path: str):
        """
        Initialize the file configuration source
        
        Args:
            file_path: Path to the configuration file
        """
        self.file_path = file_path
        self.logger = logging.getLogger(__name__)
        
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file
        
        Returns:
            Dict containing the configuration
        """
        if not os.path.exists(self.file_path):
            self.logger.warning(f"Configuration file not found: {self.file_path}")
            return {}
            
        file_extension = os.path.splitext(self.file_path)[1].lower()
        
        try:
            with open(self.file_path, 'r') as f:
                if file_extension == '.json':
                    return json.load(f)
                elif file_extension in ['.yml', '.yaml']:
                    return yaml.safe_load(f)
                else:
                    self.logger.error(f"Unsupported config file format: {file_extension}")
                    return {}
        except Exception as e:
            self.logger.error(f"Error loading configuration from file: {str(e)}")
            return {}
            
    def save(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to file
        
        Args:
            config: Configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self.file_path)), exist_ok=True)
            
            file_extension = os.path.splitext(self.file_path)[1].lower()
            
            with open(self.file_path, 'w') as f:
                if file_extension == '.json':
                    json.dump(config, f, indent=2)
                elif file_extension in ['.yml', '.yaml']:
                    yaml.dump(config, f)
                else:
                    self.logger.error(f"Unsupported config file format: {file_extension}")
                    return False
                    
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration to file: {str(e)}")
            return False


class ParameterStoreConfigSource(ConfigSource):
    """AWS Parameter Store configuration source with secure parameter handling"""
    
    def __init__(self, path_prefix: str, region: str = None, kms_key_id: str = None):
        """
        Initialize the Parameter Store configuration source
        
        Args:
            path_prefix: Path prefix for parameters
            region: AWS region
            kms_key_id: KMS key ID for parameter encryption (optional)
        """
        self.path_prefix = path_prefix
        self.region = region
        self.kms_key_id = kms_key_id
        self.ssm_client = None
        self.logger = logging.getLogger(__name__)
        
        if not AWS_AVAILABLE:
            self.logger.warning("AWS boto3 library not available. Parameter Store functionality disabled.")
        
    def _get_client(self):
        """
        Get or create SSM client
        
        Returns:
            boto3 SSM client
        """
        if not AWS_AVAILABLE:
            return None
            
        if self.ssm_client is None:
            self.ssm_client = boto3.client('ssm', region_name=self.region)
        return self.ssm_client
        
    def _parameter_to_dict(self, parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert parameter list to nested dictionary
        
        Args:
            parameters: List of parameters from Parameter Store
            
        Returns:
            Nested dictionary of configuration values
        """
        result = {}
        
        for param in parameters:
            name = param['Name']
            value = param['Value']
            param_type = param.get('Type', 'String')
            version = param.get('Version', 1)
            
            # Remove prefix from parameter name
            if name.startswith(self.path_prefix):
                name = name[len(self.path_prefix):]
            
            # Remove leading slash if present
            if name.startswith('/'):
                name = name[1:]
                
            # Convert path to nested keys
            keys = name.split('/')
            
            # Try to parse JSON value for non-secure strings
            if param_type != 'SecureString':
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass
                    
            # Build nested dictionary with metadata
            current = result
            for i, key in enumerate(keys):
                if i == len(keys) - 1:
                    current[key] = {
                        'value': value,
                        'type': param_type,
                        'version': version,
                        'last_modified': param.get('LastModifiedDate', None)
                    }
                else:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                    
        return result
        
    def _dict_to_parameters(self, config: Dict[str, Any], prefix: str = '') -> List[Dict[str, str]]:
        """
        Convert nested dictionary to parameter list
        
        Args:
            config: Configuration dictionary
            prefix: Path prefix for parameters
            
        Returns:
            List of parameters for Parameter Store
        """
        parameters = []
        
        for key, value in config.items():
            # Build parameter path
            param_path = f"{self.path_prefix}{prefix}/{key}"
            
            if isinstance(value, dict):
                if 'value' in value:
                    # Handle parameter with metadata
                    param_value = value['value']
                    param_type = value.get('type', 'String')
                    
                    # Convert value to string if needed
                    if not isinstance(param_value, str):
                        param_value = json.dumps(param_value)
                        
                    param = {
                        'Name': param_path,
                        'Value': param_value,
                        'Type': param_type,
                        'Overwrite': True
                    }
                    
                    # Add KMS key for encryption if specified
                    if param_type == 'SecureString' and self.kms_key_id:
                        param['KeyId'] = self.kms_key_id
                        
                    # Add tags if present
                    if 'tags' in value:
                        param['Tags'] = [{'Key': k, 'Value': v} for k, v in value['tags'].items()]
                        
                    parameters.append(param)
                else:
                    # Recursively process nested dictionaries
                    parameters.extend(self._dict_to_parameters(value, f"{prefix}/{key}"))
            else:
                # Handle simple values
                param_type = 'SecureString' if any(secret_word in key.lower() 
                    for secret_word in ['secret', 'password', 'key', 'token', 'credential']) else 'String'
                
                # Convert value to string
                if not isinstance(value, str):
                    value = json.dumps(value)
                    
                param = {
                    'Name': param_path,
                    'Value': value,
                    'Type': param_type,
                    'Overwrite': True
                }
                
                # Add KMS key for encryption if specified
                if param_type == 'SecureString' and self.kms_key_id:
                    param['KeyId'] = self.kms_key_id
                    
                parameters.append(param)
                
        return parameters
        
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from Parameter Store
        
        Returns:
            Dict containing the configuration
        """
        if not AWS_AVAILABLE:
            self.logger.warning("AWS boto3 library not available. Cannot load from Parameter Store.")
            return {}
            
        try:
            client = self._get_client()
            if client is None:
                return {}
            
            # Get all parameters with the specified path prefix
            parameters = []
            next_token = None
            
            while True:
                kwargs = {
                    'Path': self.path_prefix,
                    'Recursive': True,
                    'WithDecryption': True  # Always decrypt secure strings
                }
                
                if next_token:
                    kwargs['NextToken'] = next_token
                    
                try:
                    response = client.get_parameters_by_path(**kwargs)
                    parameters.extend(response.get('Parameters', []))
                    
                    next_token = response.get('NextToken')
                    if not next_token:
                        break
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'AccessDeniedException':
                        self.logger.error("Access denied to Parameter Store. Check IAM permissions.")
                    elif error_code == 'ThrottlingException':
                        self.logger.warning("AWS API throttling encountered. Some parameters may be missing.")
                        break
                    else:
                        raise
            
            return self._parameter_to_dict(parameters)
            
        except Exception as e:
            self.logger.error(f"Error loading configuration from Parameter Store: {str(e)}")
            return {}
            
    def save(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to Parameter Store
        
        Args:
            config: Configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        if not AWS_AVAILABLE:
            self.logger.warning("AWS boto3 library not available. Cannot save to Parameter Store.")
            return False
            
        try:
            client = self._get_client()
            if client is None:
                return False
                
            parameters = self._dict_to_parameters(config)
            
            # Save parameters in batches of 10 (AWS limit)
            for i in range(0, len(parameters), 10):
                batch = parameters[i:i + 10]
                
                try:
                    for param in batch:
                        # Put parameter with error handling
                        try:
                            client.put_parameter(**param)
                        except ClientError as e:
                            error_code = e.response['Error']['Code']
                            if error_code == 'AccessDeniedException':
                                self.logger.error(f"Access denied when saving parameter {param['Name']}")
                                return False
                            elif error_code == 'ParameterAlreadyExists':
                                # Parameter exists and Overwrite=False
                                self.logger.warning(f"Parameter {param['Name']} already exists and cannot be overwritten")
                            else:
                                raise
                                
                except Exception as e:
                    self.logger.error(f"Error saving parameters to Parameter Store: {str(e)}")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration to Parameter Store: {str(e)}")
            return False
            
    def get_parameter_history(self, parameter_name: str) -> List[Dict[str, Any]]:
        """
        Get the history of a parameter
        
        Args:
            parameter_name: Name of the parameter
            
        Returns:
            List of parameter versions with metadata
        """
        if not AWS_AVAILABLE:
            return []
            
        try:
            client = self._get_client()
            if client is None:
                return []
                
            # Add prefix if not present
            if not parameter_name.startswith(self.path_prefix):
                parameter_name = f"{self.path_prefix}/{parameter_name}"
                
            response = client.get_parameter_history(
                Name=parameter_name,
                WithDecryption=True
            )
            
            return [{
                'version': param['Version'],
                'value': param['Value'],
                'type': param['Type'],
                'last_modified': param['LastModifiedDate'],
                'last_modified_user': param.get('LastModifiedUser', '')
            } for param in response['Parameters']]
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ParameterNotFound':
                self.logger.warning(f"Parameter {parameter_name} not found")
            else:
                self.logger.error(f"Error getting parameter history: {str(e)}")
            return []
            
    def get_parameter_by_version(self, parameter_name: str, version: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific version of a parameter
        
        Args:
            parameter_name: Name of the parameter
            version: Version number to retrieve
            
        Returns:
            Parameter value and metadata, or None if not found
        """
        history = self.get_parameter_history(parameter_name)
        for param in history:
            if param['version'] == version:
                return param
        return None


class ConfigManager:
    """Configuration manager for the system"""
    
    def __init__(self, 
                 config_sources: List[ConfigSource] = None,
                 schema_file: Optional[str] = None,
                 owner_id: Optional[str] = None,
                 environment: str = "development"):
        """
        Initialize the configuration manager
        
        Args:
            config_sources: List of configuration sources
            schema_file: Path to schema file for validation
            owner_id: Owner ID for client-specific configuration
            environment: Environment name for environment-specific configuration
        """
        self.config_sources = config_sources or []
        self.schema_file = schema_file
        self.owner_id = owner_id
        self.environment = environment
        self.config = {}
        self.schema = {}
        self.env_prefix = "APP_"
        self.logger = logging.getLogger(__name__)
        
    def add_config_source(self, source: ConfigSource) -> None:
        """
        Add a configuration source
        
        Args:
            source: Configuration source to add
        """
        self.config_sources.append(source)
        
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from all sources
        
        Returns:
            Dict containing the configuration
        """
        # Start with empty configuration
        self.config = {}
        
        # Load schema if provided
        if self.schema_file and os.path.exists(self.schema_file):
            try:
                with open(self.schema_file, 'r') as f:
                    if os.path.splitext(self.schema_file)[1].lower() == '.json':
                        self.schema = json.load(f)
                    else:
                        self.logger.error("Schema file must be JSON format")
            except Exception as e:
                self.logger.error(f"Error loading schema: {str(e)}")
        
        # Load from each source in order (later sources override earlier ones)
        for source in self.config_sources:
            source_config = source.load()
            self._merge_configs(self.config, source_config)
        
        # Filter configuration by environment
        if self.environment and 'environments' in self.config:
            env_config = self.config.get('environments', {}).get(self.environment, {})
            # Merge environment-specific config with base config
            for key, value in env_config.items():
                if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                    self._merge_configs(self.config[key], value)
                else:
                    self.config[key] = value
        
        # Filter by owner if specified
        if self.owner_id and 'clients' in self.config:
            client_config = self.config.get('clients', {}).get(self.owner_id, {})
            # Merge client-specific config with base config
            for key, value in client_config.items():
                if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                    self._merge_configs(self.config[key], value)
                else:
                    self.config[key] = value
        
        # Override with environment variables
        self.load_from_env()
        
        # Validate configuration
        if self.schema:
            self.validate_config()
        
        return self.config
    
    def _merge_configs(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively merge source config into target config
        
        Args:
            target: Target configuration dictionary
            source: Source configuration dictionary
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_configs(target[key], value)
            else:
                target[key] = value
        
    def save_config(self) -> bool:
        """
        Save current configuration to all writable sources
        
        Returns:
            True if successful, False otherwise
        """
        # Validate before saving
        if self.schema and not self.validate_config():
            self.logger.error("Configuration validation failed, not saving")
            return False
        
        success = True
        
        # Save to each source
        for source in self.config_sources:
            if not source.save(self.config):
                success = False
        
        return success
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key
        
        Args:
            key: Dot-notation key (e.g., "database.host")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if not key:
            return self.config
            
        key_path = key.split('.')
        
        try:
            return self._get_nested_value(self.config, key_path)
        except (KeyError, TypeError):
            return default
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Set configuration value
        
        Args:
            key: Dot-notation key (e.g., "database.host")
            value: Value to set
        """
        if not key:
            raise ValueError("Key cannot be empty")
            
        key_path = key.split('.')
        self._set_nested_value(self.config, key_path, value)
        
        # Validate after change if schema exists
        if self.schema:
            self.validate_config()
            
    def validate_config(self) -> bool:
        """
        Validate configuration against schema
        
        Returns:
            True if valid, False otherwise
        """
        if not self.schema:
            return True
            
        try:
            jsonschema.validate(instance=self.config, schema=self.schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            self.logger.error(f"Configuration validation error: {str(e)}")
            return False
            
    def load_from_env(self) -> None:
        """
        Load configuration from environment variables
        
        Environment variables should be in the format:
        APP_SECTION_KEY=value (converts to section.key in config)
        """
        for env_key, env_value in os.environ.items():
            if env_key.startswith(self.env_prefix):
                # Convert APP_DATABASE_HOST to database.host
                config_key = env_key[len(self.env_prefix):].lower().replace('_', '.')
                
                # Try to parse the value as JSON, fall back to string if it fails
                try:
                    value = json.loads(env_value)
                except json.JSONDecodeError:
                    value = env_value
                    
                self.set_config(config_key, value)
                
    def get_client_config(self, client_id: str) -> Dict[str, Any]:
        """
        Get configuration specific to a client
        
        Args:
            client_id: Client identifier
            
        Returns:
            Client-specific configuration
        """
        # Start with a copy of the base configuration
        client_config = json.loads(json.dumps(self.config))
        
        # Remove clients section
        if 'clients' in client_config:
            del client_config['clients']
        
        # Apply client-specific overrides if they exist
        if 'clients' in self.config and client_id in self.config['clients']:
            client_overrides = self.config['clients'][client_id]
            self._merge_configs(client_config, client_overrides)
        
        return client_config
    
    def export_config(self, format: str = "json") -> str:
        """
        Export configuration to a portable format
        
        Args:
            format: Export format (json, yaml)
            
        Returns:
            Configuration as a string in the specified format
        """
        if format.lower() == "json":
            return json.dumps(self.config, indent=2)
        elif format.lower() in ["yaml", "yml"]:
            return yaml.dump(self.config)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_config(self, config_data: str, format: str = "json") -> bool:
        """
        Import configuration from a portable format
        
        Args:
            config_data: Configuration data as string
            format: Import format (json, yaml)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if format.lower() == "json":
                imported_config = json.loads(config_data)
            elif format.lower() in ["yaml", "yml"]:
                imported_config = yaml.safe_load(config_data)
            else:
                raise ValueError(f"Unsupported import format: {format}")
            
            # Validate imported configuration
            if self.schema:
                try:
                    jsonschema.validate(instance=imported_config, schema=self.schema)
                except jsonschema.exceptions.ValidationError as e:
                    self.logger.error(f"Imported configuration validation error: {str(e)}")
                    return False
            
            # Update configuration
            self.config = imported_config
            
            return True
        except Exception as e:
            self.logger.error(f"Error importing configuration: {str(e)}")
            return False
            
    def _get_nested_value(self, config: Dict[str, Any], key_path: list) -> Any:
        """
        Get nested value from dictionary using key path
        
        Args:
            config: Configuration dictionary
            key_path: List of keys to traverse
            
        Returns:
            Value at the specified path
        """
        if not key_path:
            return config
            
        key = key_path[0]
        if len(key_path) == 1:
            return config[key]
        else:
            return self._get_nested_value(config[key], key_path[1:])
    
    def _set_nested_value(self, config: Dict[str, Any], key_path: list, value: Any) -> None:
        """
        Set nested value in dictionary using key path
        
        Args:
            config: Configuration dictionary
            key_path: List of keys to traverse
            value: Value to set
        """
        key = key_path[0]
        
        if len(key_path) == 1:
            config[key] = value
        else:
            if key not in config:
                config[key] = {}
            elif not isinstance(config[key], dict):
                config[key] = {}
                
            self._set_nested_value(config[key], key_path[1:], value)


class DependencyManager:
    """Manager for system dependencies"""
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        Initialize the dependency manager
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
    def install_dependencies(self, requirements_file: str = None) -> bool:
        """
        Install required dependencies
        
        Args:
            requirements_file: Path to requirements file
            
        Returns:
            True if successful, False otherwise
        """
        # This is a placeholder for actual implementation
        self.logger.info("Installing dependencies...")
        return True
        
    def update_dependencies(self) -> bool:
        """
        Update dependencies to latest compatible versions
        
        Returns:
            True if successful, False otherwise
        """
        # This is a placeholder for actual implementation
        self.logger.info("Updating dependencies...")
        return True
        
    def check_compatibility(self, package_name: str, version: str) -> bool:
        """
        Verify dependency compatibility
        
        Args:
            package_name: Name of the package
            version: Version to check
            
        Returns:
            True if compatible, False otherwise
        """
        # This is a placeholder for actual implementation
        self.logger.info(f"Checking compatibility for {package_name} version {version}...")
        return True
        
    def handle_fallback(self, package_name: str, current_version: str, target_version: str) -> bool:
        """
        Handle fallback for failed updates
        
        Args:
            package_name: Name of the package
            current_version: Current version
            target_version: Target version that failed
            
        Returns:
            True if fallback successful, False otherwise
        """
        # This is a placeholder for actual implementation
        self.logger.info(f"Falling back to {current_version} for {package_name}...")
        return True