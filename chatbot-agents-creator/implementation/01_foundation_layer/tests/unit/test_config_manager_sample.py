import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Import the module we want to test
# Note: This import path may need to be adjusted based on your project structure
from src.config_management.config_manager import ConfigManager, ConfigSource, FileConfigSource


class TestConfigSource(unittest.TestCase):
    """Test cases for the ConfigSource base class"""

    def test_abstract_methods(self):
        """Test that ConfigSource has required abstract methods"""
        # Should not be able to instantiate ConfigSource directly
        with self.assertRaises(TypeError):
            config_source = ConfigSource()


class TestFileConfigSource(unittest.TestCase):
    """Test cases for the FileConfigSource class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a test JSON config file
        self.json_config_path = os.path.join(self.temp_dir.name, "config.json")
        self.json_config_data = {
            "app_name": "Test App",
            "database": {
                "host": "localhost",
                "port": 5432
            }
        }
        with open(self.json_config_path, 'w') as f:
            json.dump(self.json_config_data, f)
            
        # Create a test YAML config file
        self.yaml_config_path = os.path.join(self.temp_dir.name, "config.yaml")
        with open(self.yaml_config_path, 'w') as f:
            f.write("""
app_name: Test App YAML
database:
  host: localhost
  port: 5432
            """)

    def tearDown(self):
        """Tear down test fixtures"""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of FileConfigSource"""
        source = FileConfigSource(self.json_config_path)
        self.assertEqual(source.file_path, self.json_config_path)

    def test_load_json(self):
        """Test loading configuration from JSON file"""
        source = FileConfigSource(self.json_config_path)
        config = source.load()
        
        self.assertEqual(config["app_name"], "Test App")
        self.assertEqual(config["database"]["host"], "localhost")
        self.assertEqual(config["database"]["port"], 5432)

    def test_load_yaml(self):
        """Test loading configuration from YAML file"""
        source = FileConfigSource(self.yaml_config_path)
        config = source.load()
        
        self.assertEqual(config["app_name"], "Test App YAML")
        self.assertEqual(config["database"]["host"], "localhost")
        self.assertEqual(config["database"]["port"], 5432)

    def test_load_nonexistent_file(self):
        """Test loading from a non-existent file returns empty dict"""
        source = FileConfigSource("nonexistent_file.json")
        config = source.load()
        self.assertEqual(config, {})

    def test_load_unsupported_format(self):
        """Test loading from unsupported file format returns empty dict"""
        # Create a file with unsupported extension
        unsupported_path = os.path.join(self.temp_dir.name, "config.txt")
        with open(unsupported_path, 'w') as f:
            f.write("This is not a supported format")
            
        source = FileConfigSource(unsupported_path)
        config = source.load()
        self.assertEqual(config, {})

    def test_save_json(self):
        """Test saving configuration to JSON file"""
        # Create a new file path for saving
        save_path = os.path.join(self.temp_dir.name, "save_config.json")
        source = FileConfigSource(save_path)
        
        # Save configuration
        config_to_save = {"app_name": "Saved App", "version": "1.0.0"}
        result = source.save(config_to_save)
        
        # Verify save was successful
        self.assertTrue(result)
        self.assertTrue(os.path.exists(save_path))
        
        # Verify saved content
        with open(save_path, 'r') as f:
            saved_config = json.load(f)
            
        self.assertEqual(saved_config["app_name"], "Saved App")
        self.assertEqual(saved_config["version"], "1.0.0")

    def test_save_yaml(self):
        """Test saving configuration to YAML file"""
        # Create a new file path for saving
        save_path = os.path.join(self.temp_dir.name, "save_config.yaml")
        source = FileConfigSource(save_path)
        
        # Save configuration
        config_to_save = {"app_name": "Saved App", "version": "1.0.0"}
        result = source.save(config_to_save)
        
        # Verify save was successful
        self.assertTrue(result)
        self.assertTrue(os.path.exists(save_path))
        
        # Load and verify saved content
        loaded_source = FileConfigSource(save_path)
        saved_config = loaded_source.load()
            
        self.assertEqual(saved_config["app_name"], "Saved App")
        self.assertEqual(saved_config["version"], "1.0.0")


class TestConfigManager(unittest.TestCase):
    """Test cases for the ConfigManager class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a test config file
        self.config_path = os.path.join(self.temp_dir.name, "config.json")
        self.config_data = {
            "app_name": "Test App",
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "environments": {
                "development": {
                    "debug": True
                },
                "production": {
                    "debug": False
                }
            },
            "clients": {
                "client123": {
                    "app_name": "Client App",
                    "database": {
                        "host": "client-db"
                    }
                }
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(self.config_data, f)
            
        # Create a test schema file
        self.schema_path = os.path.join(self.temp_dir.name, "schema.json")
        self.schema_data = {
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
        with open(self.schema_path, 'w') as f:
            json.dump(self.schema_data, f)
            
        # Create config source
        self.config_source = FileConfigSource(self.config_path)

    def tearDown(self):
        """Tear down test fixtures"""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of ConfigManager"""
        manager = ConfigManager(
            config_sources=[self.config_source],
            schema_file=self.schema_path,
            owner_id="client123",
            environment="development"
        )
        
        self.assertEqual(len(manager.config_sources), 1)
        self.assertEqual(manager.schema_file, self.schema_path)
        self.assertEqual(manager.owner_id, "client123")
        self.assertEqual(manager.environment, "development")

    def test_add_config_source(self):
        """Test adding a config source"""
        manager = ConfigManager()
        self.assertEqual(len(manager.config_sources), 0)
        
        manager.add_config_source(self.config_source)
        self.assertEqual(len(manager.config_sources), 1)

    def test_load_config(self):
        """Test loading configuration"""
        manager = ConfigManager(
            config_sources=[self.config_source]
        )
        
        config = manager.load_config()
        
        self.assertEqual(config["app_name"], "Test App")
        self.assertEqual(config["database"]["host"], "localhost")
        self.assertEqual(config["database"]["port"], 5432)

    def test_load_config_with_environment(self):
        """Test loading configuration with environment-specific settings"""
        manager = ConfigManager(
            config_sources=[self.config_source],
            environment="development"
        )
        
        config = manager.load_config()
        
        self.assertEqual(config["app_name"], "Test App")
        self.assertEqual(config["debug"], True)  # From development environment

    def test_load_config_with_owner(self):
        """Test loading configuration with client-specific settings"""
        manager = ConfigManager(
            config_sources=[self.config_source],
            owner_id="client123"
        )
        
        config = manager.load_config()
        
        self.assertEqual(config["app_name"], "Client App")  # Overridden by client config
        self.assertEqual(config["database"]["host"], "client-db")  # Overridden by client config
        self.assertEqual(config["database"]["port"], 5432)  # From base config

    def test_get_config(self):
        """Test getting configuration values"""
        manager = ConfigManager(
            config_sources=[self.config_source]
        )
        manager.load_config()
        
        # Get top-level value
        self.assertEqual(manager.get_config("app_name"), "Test App")
        
        # Get nested value
        self.assertEqual(manager.get_config("database.host"), "localhost")
        
        # Get with default for non-existent key
        self.assertEqual(manager.get_config("nonexistent", "default"), "default")

    def test_set_config(self):
        """Test setting configuration values"""
        manager = ConfigManager(
            config_sources=[self.config_source]
        )
        manager.load_config()
        
        # Set top-level value
        manager.set_config("app_name", "Updated App")
        self.assertEqual(manager.get_config("app_name"), "Updated App")
        
        # Set nested value
        manager.set_config("database.host", "new-host")
        self.assertEqual(manager.get_config("database.host"), "new-host")
        
        # Set new nested value
        manager.set_config("logging.level", "DEBUG")
        self.assertEqual(manager.get_config("logging.level"), "DEBUG")

    def test_get_client_config(self):
        """Test getting client-specific configuration"""
        manager = ConfigManager(
            config_sources=[self.config_source]
        )
        manager.load_config()
        
        client_config = manager.get_client_config("client123")
        
        # Client-specific overrides
        self.assertEqual(client_config["app_name"], "Client App")
        self.assertEqual(client_config["database"]["host"], "client-db")
        
        # Base config values not overridden
        self.assertEqual(client_config["database"]["port"], 5432)
        
        # Clients section should be removed
        self.assertNotIn("clients", client_config)

    @patch('os.environ', {
        'APP_LOGGING_LEVEL': 'DEBUG',
        'APP_DATABASE_PORT': '6543'
    })
    def test_load_from_env(self):
        """Test loading configuration from environment variables"""
        manager = ConfigManager(
            config_sources=[self.config_source]
        )
        manager.load_config()
        
        # Environment variables should override config
        self.assertEqual(manager.get_config("logging.level"), "DEBUG")
        self.assertEqual(manager.get_config("database.port"), 6543)  # Note: converted to int

    def test_export_import_config(self):
        """Test exporting and importing configuration"""
        manager = ConfigManager(
            config_sources=[self.config_source]
        )
        manager.load_config()
        
        # Export to JSON
        exported = manager.export_config(format="json")
        
        # Create new manager and import
        new_manager = ConfigManager()
        result = new_manager.import_config(exported, format="json")
        
        # Import should succeed
        self.assertTrue(result)
        
        # Imported config should match original
        self.assertEqual(new_manager.get_config("app_name"), "Test App")
        self.assertEqual(new_manager.get_config("database.host"), "localhost")
        self.assertEqual(new_manager.get_config("database.port"), 5432)


if __name__ == '__main__':
    unittest.main()