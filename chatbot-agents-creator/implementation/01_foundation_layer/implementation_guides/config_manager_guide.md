# Config Manager Implementation Guide

This guide provides detailed instructions for implementing the Config Manager component of the Foundation Layer. It serves as an example for junior developers to understand the implementation approach.

## Overview

The Config Manager is responsible for loading, storing, and providing access to configuration settings throughout the system. It supports hierarchical configuration, validation, environment-specific settings, and dynamic updates. The implementation follows the principles of Scalability, Modularity, Autonomy, Future-Proofing, and Client Ownership.

## Design Principles Implementation

### Scalability
- Configuration caching for frequently accessed values
- Asynchronous configuration updates
- Support for distributed configuration across multiple environments

### Modularity
- Clear separation between configuration storage and access
- Plugin system for different configuration sources
- Well-defined interfaces for integration with other components

### Autonomy
- Self-validation of configuration values
- Automatic reload on configuration changes
- Default values for missing configuration

### Future-Proofing
- Configuration versioning and migration
- Schema-based validation
- Support for multiple configuration formats

### Client Ownership
- Client-specific configuration isolation
- Configuration export/import capabilities
- Secure storage for sensitive configuration values

## Implementation Requirements

### Dependencies

```python
import os
import json
import yaml
import boto3
import jsonschema
import logging
from typing import Any, Dict, Optional, List, Union
from botocore.exceptions import ClientError
```

### Class Structure

```python
class ConfigSource:
    """Base class for configuration sources"""
    def load(self) -> Dict[str, Any]:
        """Load configuration from this source"""
        raise NotImplementedError
        
    def save(self, config: Dict[str, Any]) -> bool:
        """Save configuration to this source"""
        raise NotImplementedError

class FileConfigSource(ConfigSource):
    """File-based configuration source"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        
    def load(self) -> Dict[str, Any]:
        """Load configuration from file"""
        pass
        
    def save(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        pass

class ParameterStoreConfigSource(ConfigSource):
    """AWS Parameter Store configuration source"""
    def __init__(self, path_prefix: str, region: str = None):
        self.path_prefix = path_prefix
        self.region = region
        self.ssm_client = None
        
    def load(self) -> Dict[str, Any]:
        """Load configuration from Parameter Store"""
        pass
        
    def save(self, config: Dict[str, Any]) -> bool:
        """Save configuration to Parameter Store"""
        pass

class ConfigManager:
    def __init__(self, 
                 config_sources: List[ConfigSource] = None,
                 schema_file: Optional[str] = None,
                 owner_id: Optional[str] = None,
                 environment: str = "development"):
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
        pass
        
    def save_config(self) -> bool:
        """
        Save current configuration to all writable sources
        
        Returns:
            True if successful, False otherwise
        """
        pass
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key
        
        Args:
            key: Dot-notation key (e.g., "database.host")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        pass
        
    def set_config(self, key: str, value: Any) -> None:
        """
        Set configuration value
        
        Args:
            key: Dot-notation key (e.g., "database.host")
            value: Value to set
        """
        pass
        
    def validate_config(self) -> bool:
        """
        Validate configuration against schema
        
        Returns:
            True if valid, False otherwise
        """
        pass
        
    def load_from_env(self) -> None:
        """
        Load configuration from environment variables
        """
        pass
        
    def get_client_config(self, client_id: str) -> Dict[str, Any]:
        """
        Get configuration specific to a client
        
        Args:
            client_id: Client identifier
            
        Returns:
            Client-specific configuration
        """
        pass
        
    def export_config(self, format: str = "json") -> str:
        """
        Export configuration to a portable format
        
        Args:
            format: Export format (json, yaml)
            
        Returns:
            Configuration as a string in the specified format
        """
        pass
        
    def import_config(self, config_data: str, format: str = "json") -> bool:
        """
        Import configuration from a portable format
        
        Args:
            config_data: Configuration data as string
            format: Import format (json, yaml)
            
        Returns:
            True if successful, False otherwise
        """
        pass
        
    def _get_nested_value(self, config: Dict[str, Any], key_path: list) -> Any:
        """
        Get nested value from dictionary using key path
        
        Args:
            config: Configuration dictionary
            key_path: List of keys to traverse
            
        Returns:
            Value at the specified path
        """
        pass
        
    def _set_nested_value(self, config: Dict[str, Any], key_path: list, value: Any) -> None:
        """
        Set nested value in dictionary using key path
        
        Args:
            config: Configuration dictionary
            key_path: List of keys to traverse
            value: Value to set
        """
        pass
```

## Implementation Steps

### 1. Implement File Configuration Source

```python
class FileConfigSource(ConfigSource):
    """File-based configuration source"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.logger = logging.getLogger(__name__)
        
    def load(self) -> Dict[str, Any]:
        """Load configuration from file"""
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
        """Save configuration to file"""
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
```

### 2. Implement Parameter Store Configuration Source

```python
class ParameterStoreConfigSource(ConfigSource):
    """AWS Parameter Store configuration source"""
    def __init__(self, path_prefix: str, region: str = None):
        self.path_prefix = path_prefix
        self.region = region
        self.ssm_client = None
        self.logger = logging.getLogger(__name__)
        
    def _get_client(self):
        """Get or create SSM client"""
        if self.ssm_client is None:
            self.ssm_client = boto3.client('ssm', region_name=self.region)
        return self.ssm_client
        
    def _parameter_to_dict(self, parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert parameter list to nested dictionary"""
        result = {}
        
        for param in parameters:
            name = param['Name']
            value = param['Value']
            
            # Remove prefix from parameter name
            if name.startswith(self.path_prefix):
                name = name[len(self.path_prefix):]
            
            # Remove leading slash if present
            if name.startswith('/'):
                name = name[1:]
                
            # Convert path to nested keys
            keys = name.split('/')
            
            # Try to parse JSON value
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
                
            # Build nested dictionary
            current = result
            for i, key in enumerate(keys):
                if i == len(keys) - 1:
                    current[key] = value
                else:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                    
        return result
        
    def _dict_to_parameters(self, config: Dict[str, Any], prefix: str = '') -> List[Dict[str, str]]:
        """Convert nested dictionary to parameter list"""
        parameters = []
        
        for key, value in config.items():
            # Build parameter path
            param_path = f"{self.path_prefix}{prefix}/{key}"
            
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                parameters.extend(self._dict_to_parameters(value, f"{prefix}/{key}"))
            else:
                # Convert value to string
                if not isinstance(value, str):
                    value = json.dumps(value)
                    
                parameters.append({
                    'Name': param_path,
                    'Value': value,
                    'Type': 'SecureString' if 'secret' in key.lower() or 'password' in key.lower() or 'key' in key.lower() else 'String',
                    'Overwrite': True
                })
                
        return parameters
        
    def load(self) -> Dict[str, Any]:
        """Load configuration from Parameter Store"""
        try:
            client = self._get_client()
            
            # Get all parameters with the specified path prefix
            parameters = []
            next_token = None
            
            while True:
                kwargs = {
                    'Path': self.path_prefix,
                    'Recursive': True,
                    'WithDecryption': True,
                    'MaxResults': 10
                }
                
                if next_token:
                    kwargs['NextToken'] = next_token
                    
                response = client.get_parameters_by_path(**kwargs)
                parameters.extend(response.get('Parameters', []))
                
                next_token = response.get('NextToken')
                if not next_token:
                    break
                    
            return self._parameter_to_dict(parameters)
        except ClientError as e:
            self.logger.error(f"Error loading configuration from Parameter Store: {str(e)}")
            return {}
            
    def save(self, config: Dict[str, Any]) -> bool:
        """Save configuration to Parameter Store"""
        try:
            client = self._get_client()
            parameters = self._dict_to_parameters(config)
            
            # Put parameters in batches of 10 (Parameter Store limit)
            for i in range(0, len(parameters), 10):
                batch = parameters[i:i+10]
                for param in batch:
                    client.put_parameter(
                        Name=param['Name'],
                        Value=param['Value'],
                        Type=param['Type'],
                        Overwrite=param['Overwrite']
                    )
                    
            return True
        except ClientError as e:
            self.logger.error(f"Error saving configuration to Parameter Store: {str(e)}")
            return False
```

### 3. Implement `load_config` Method

```python
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
```

### 4. Implement `save_config` Method

```python
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
```

### 5. Implement `get_config` and `set_config` Methods

```python
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
```

### 6. Implement Helper Methods

```python
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
```

### 7. Implement Client-Specific Configuration Methods

```python
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
```

### 8. Implement Environment Variable Loading

```python
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
```

### 9. Implement Validation Method

```python
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
```

## Usage Example

### Basic Usage

```python
# Create file-based configuration source
file_source = FileConfigSource("config/config.json")

# Create Parameter Store configuration source for sensitive values
param_store_source = ParameterStoreConfigSource("/myapp/config", region="us-west-2")

# Create config manager with both sources
config_manager = ConfigManager(
    config_sources=[file_source, param_store_source],
    schema_file="config/schema.json",
    environment="development"
)

# Load configuration
config_manager.load_config()

# Get configuration values
database_host = config_manager.get_config("database.host", "localhost")
database_port = config_manager.get_config("database.port", 5432)

# Set configuration values
config_manager.set_config("logging.level", "DEBUG")

# Save configuration
config_manager.save_config()
```

### Client-Specific Configuration

```python
# Create config manager with client ownership
config_manager = ConfigManager(
    config_sources=[FileConfigSource("config/config.json")],
    schema_file="config/schema.json",
    owner_id="client123",
    environment="production"
)

# Load configuration (will automatically apply client-specific overrides)
config_manager.load_config()

# Get configuration for a different client
other_client_config = config_manager.get_client_config("client456")

# Export configuration for client deployment
exported_config = config_manager.export_config(format="yaml")
with open("client_export/config.yaml", "w") as f:
    f.write(exported_config)
```

### Serverless Integration

```python
def lambda_handler(event, context):
    # Create config manager with Parameter Store source
    config_manager = ConfigManager(
        config_sources=[ParameterStoreConfigSource("/myapp/config")],
        environment=os.environ.get("ENVIRONMENT", "development")
    )
    
    # Load configuration
    config = config_manager.load_config()
    
    # Use configuration in Lambda function
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Configuration loaded successfully",
            "appName": config.get("app_name", "Default App"),
            "environment": config_manager.environment
        })
    }
```

## Testing

Create unit tests to verify:

1. Loading configuration from different file formats (JSON, YAML)
2. Getting and setting nested configuration values
3. Validation against schema
4. Environment variable overrides
5. Client-specific configuration isolation
6. Configuration export/import
7. AWS Parameter Store integration

Example test:

```python
import unittest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from config_management.config_manager import ConfigManager, FileConfigSource

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        # Create temporary config file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = os.path.join(self.temp_dir.name, "config.json")
        self.schema_file = os.path.join(self.temp_dir.name, "schema.json")
        
        # Sample config
        self.sample_config = {
            "app_name": "Test App",
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "clients": {
                "client123": {
                    "app_name": "Client App",
                    "database": {
                        "host": "client-db"
                    }
                }
            },
            "environments": {
                "production": {
                    "database": {
                        "host": "prod-db"
                    }
                }
            }
        }
        
        # Sample schema
        self.sample_schema = {
            "type": "object",
            "required": ["app_name"],
            "properties": {
                "app_name": {"type": "string"},
                "database": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "number"}
                    }
                }
            }
        }
        
        # Write sample config and schema
        with open(self.config_file, "w") as f:
            json.dump(self.sample_config, f)
            
        with open(self.schema_file, "w") as f:
            json.dump(self.sample_schema, f)
            
        # Create config manager
        self.config_source = FileConfigSource(self.config_file)
        self.config_manager = ConfigManager(
            config_sources=[self.config_source],
            schema_file=self.schema_file
        )
        
    def tearDown(self):
        self.temp_dir.cleanup()
        
    def test_load_config(self):
        config = self.config_manager.load_config()
        self.assertEqual(config["app_name"], "Test App")
        self.assertEqual(config["database"]["host"], "localhost")
        self.assertEqual(config["database"]["port"], 5432)
        
    def test_get_config(self):
        self.config_manager.load_config()
        self.assertEqual(self.config_manager.get_config("app_name"), "Test App")
        self.assertEqual(self.config_manager.get_config("database.host"), "localhost")
        self.assertEqual(self.config_manager.get_config("database.port"), 5432)
        self.assertEqual(self.config_manager.get_config("nonexistent", "default"), "default")
        
    def test_set_config(self):
        self.config_manager.load_config()
        self.config_manager.set_config("database.host", "new-host")
        self.assertEqual(self.config_manager.get_config("database.host"), "new-host")
        
    def test_client_config(self):
        # Create config manager with client ID
        client_config_manager = ConfigManager(
            config_sources=[self.config_source],
            schema_file=self.schema_file,
            owner_id="client123"
        )
        
        client_config_manager.load_config()
        self.assertEqual(client_config_manager.get_config("app_name"), "Client App")
        self.assertEqual(client_config_manager.get_config("database.host"), "client-db")
        self.assertEqual(client_config_manager.get_config("database.port"), 5432)
        
    def test_environment_config(self):
        # Create config manager with environment
        env_config_manager = ConfigManager(
            config_sources=[self.config_source],
            schema_file=self.schema_file,
            environment="production"
        )
        
        env_config_manager.load_config()
        self.assertEqual(env_config_manager.get_config("app_name"), "Test App")
        self.assertEqual(env_config_manager.get_config("database.host"), "prod-db")
        self.assertEqual(env_config_manager.get_config("database.port"), 5432)
        
    @patch.dict(os.environ, {"APP_LOGGING_LEVEL": "DEBUG"})
    def test_env_override(self):
        self.config_manager.load_config()
        self.assertEqual(self.config_manager.get_config("logging.level"), "DEBUG")
        
    def test_export_import(self):
        self.config_manager.load_config()
        exported = self.config_manager.export_config()
        
        # Create new config manager
        new_config_manager = ConfigManager()
        new_config_manager.import_config(exported)
        
        self.assertEqual(new_config_manager.get_config("app_name"), "Test App")
        self.assertEqual(new_config_manager.get_config("database.host"), "localhost")
```

## Integration with Other Components

The Config Manager will be used by:

1. **Component Registry**: For component configuration and discovery
   ```python
   # In Component Registry
   def __init__(self, config_manager):
       self.config_manager = config_manager
       self.components = {}
       self.owner_id = config_manager.owner_id
   ```

2. **Base Agent**: For agent-specific settings and client ownership
   ```python
   # In Base Agent
   def __init__(self, config_manager):
       self.config_manager = config_manager
       self.owner_id = config_manager.owner_id
       self.agent_config = config_manager.get_config("agents.default", {})
   ```

3. **Task Distributor**: For workload management settings
   ```python
   # In Task Distributor
   def __init__(self, config_manager):
       self.config_manager = config_manager
       self.max_tasks = config_manager.get_config("workload.max_tasks", 100)
       self.priority_levels = config_manager.get_config("workload.priority_levels", 3)
   ```

4. **Resource Monitor**: For resource allocation thresholds
   ```python
   # In Resource Monitor
   def __init__(self, config_manager):
       self.config_manager = config_manager
       self.thresholds = config_manager.get_config("resources.thresholds", {})
       self