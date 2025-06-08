"""
Sample implementation of the Config Manager component.
This serves as a reference for junior developers.
"""

import os
import json
import yaml
import logging
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod

class ConfigSource(ABC):
    """Base class for configuration sources"""
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from this source
        
        Returns:
            Dict containing the configuration
        """
        pass
        
    @abstractmethod
    def save(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to this source
        
        Args:
            config: Configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        pass


class FileConfigSource(ConfigSource):
    """File-based configuration source"""
    
    def __init__(self, file_path: str):
        """
        Initialize with file path
        
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


class ConfigManager:
    """
    Configuration manager for the system.
    Handles loading, storing, and providing access to configuration settings.
    """
    
    def __init__(self, 
                 config_sources: List[ConfigSource] = None,
                 schema_file: Optional[str] = None,
                 owner_id: Optional[str] = None,
                 environment: str = "development"):
        """
        Initialize the configuration manager
        
        Args:
            config_sources: List of configuration sources
            schema_file: Path to JSON schema file for validation
            owner_id: Owner identifier for client-specific configuration
            environment: Environment name (development, production, etc.)
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
            # Note: In a real implementation, you would use jsonschema.validate here
            # For this example, we'll just return True
            # jsonschema.validate(instance=self.config, schema=self.schema)
            return True
        except Exception as e:
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
                # In a real implementation, you would validate here
                pass
            
            # Update configuration
            self.config = imported_config
            
            return True
        except Exception as e:
            self.logger.error(f"Error importing configuration: {str(e)}")
            return False
            
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


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create config sources
    file_source = FileConfigSource("config/config.json")
    
    # Create config manager
    config_manager = ConfigManager(
        config_sources=[file_source],
        schema_file="config/schema.json",
        owner_id="client123",
        environment="development"
    )
    
    # Load configuration
    config = config_manager.load_config()
    
    # Get configuration values
    app_name = config_manager.get_config("app_name")
    db_host = config_manager.get_config("database.host")
    
    print(f"App Name: {app_name}")
    print(f"Database Host: {db_host}")
    
    # Set configuration values
    config_manager.set_config("logging.level", "DEBUG")
    
    # Save configuration
    config_manager.save_config()
    
    # Get client-specific configuration
    client_config = config_manager.get_client_config("client123")
    print(f"Client App Name: {client_config.get('app_name')}")