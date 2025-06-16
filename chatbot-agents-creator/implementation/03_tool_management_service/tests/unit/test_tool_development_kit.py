import unittest
from unittest.mock import MagicMock, patch
import tempfile
import os
import json
from src.tool_development_kit import ToolTemplate, ToolValidator, ToolPackager, ToolUpdater, ToolMigrator, DocumentationGenerator


class TestToolTemplate(unittest.TestCase):
    def test_generate_tool_template(self):
        # Create a tool template
        template = ToolTemplate()
        
        # Generate a template for a simple tool
        tool_code = template.generate_tool_template(
            name="test_tool",
            description="A test tool",
            parameters=[
                {"name": "param1", "type": "string", "description": "First parameter", "required": True},
                {"name": "param2", "type": "integer", "description": "Second parameter", "required": False}
            ],
            result_type="object"
        )
        
        # Check if the generated code contains essential elements
        self.assertIn("class TestTool(ToolInterface):", tool_code)
        self.assertIn("def __init__(self):", tool_code)
        self.assertIn("self.name = \"test_tool\"", tool_code)
        self.assertIn("self.description = \"A test tool\"", tool_code)
        self.assertIn("def execute(self, parameters):", tool_code)
        self.assertIn("def get_parameter_schema(self):", tool_code)
        self.assertIn("def get_result_schema(self):", tool_code)
        self.assertIn("\"param1\"", tool_code)
        self.assertIn("\"param2\"", tool_code)
        self.assertIn("\"required\": [\"param1\"]", tool_code)
        
    def test_generate_function_tool_template(self):
        # Create a tool template
        template = ToolTemplate()
        
        # Generate a template for a function tool
        tool_code = template.generate_function_tool_template(
            name="add_numbers",
            description="Add two numbers",
            parameters=[
                {"name": "a", "type": "number", "description": "First number", "required": True},
                {"name": "b", "type": "number", "description": "Second number", "required": True}
            ],
            result_type="number"
        )
        
        # Check if the generated code contains essential elements
        self.assertIn("def add_numbers(a, b):", tool_code)
        self.assertIn("# TODO: Implement the function", tool_code)
        self.assertIn("FunctionTool(", tool_code)
        self.assertIn("name=\"add_numbers\"", tool_code)
        self.assertIn("description=\"Add two numbers\"", tool_code)
        self.assertIn("function=add_numbers", tool_code)
        self.assertIn("\"a\"", tool_code)
        self.assertIn("\"b\"", tool_code)
        self.assertIn("\"required\": [\"a\", \"b\"]", tool_code)


class TestToolValidator(unittest.TestCase):
    def setUp(self):
        # Create a mock tool for testing
        self.mock_tool = MagicMock()
        self.mock_tool.name = "test_tool"
        self.mock_tool.description = "A test tool"
        self.mock_tool.get_parameter_schema.return_value = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "integer"}
            },
            "required": ["param1"]
        }
        self.mock_tool.get_result_schema.return_value = {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            }
        }
        self.mock_tool.execute.return_value = {"result": "test_result"}
        
        # Create a validator
        self.validator = ToolValidator()
        
    def test_validate_tool_interface(self):
        # Validate a tool that implements the interface correctly
        result = self.validator.validate_tool_interface(self.mock_tool)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        
    def test_validate_tool_interface_missing_methods(self):
        # Create a tool with missing methods
        incomplete_tool = MagicMock()
        incomplete_tool.name = "incomplete_tool"
        incomplete_tool.description = "An incomplete tool"
        # Missing get_parameter_schema and get_result_schema methods
        
        # Validate the incomplete tool
        result = self.validator.validate_tool_interface(incomplete_tool)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        
    def test_validate_tool_execution(self):
        # Validate tool execution with valid parameters
        valid_params = {"param1": "test", "param2": 42}
        result = self.validator.validate_tool_execution(self.mock_tool, valid_params)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        
        # Validate tool execution with invalid parameters
        invalid_params = {"param2": "not_an_integer"}
        result = self.validator.validate_tool_execution(self.mock_tool, invalid_params)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)


class TestToolPackager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock tool for testing
        self.mock_tool = MagicMock()
        self.mock_tool.name = "test_tool"
        self.mock_tool.description = "A test tool"
        self.mock_tool.get_parameter_schema.return_value = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "integer"}
            },
            "required": ["param1"]
        }
        self.mock_tool.get_result_schema.return_value = {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            }
        }
        
        # Create a packager
        self.packager = ToolPackager()
        
    def tearDown(self):
        # Clean up the temporary directory
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.temp_dir)
        
    @patch('src.tool_development_kit.ToolValidator')
    def test_package_tool(self, mock_validator_class):
        # Mock the validator to return a valid result
        mock_validator = MagicMock()
        mock_validator.validate_tool_interface.return_value = MagicMock(is_valid=True, errors=[])
        mock_validator_class.return_value = mock_validator
        
        # Package the tool
        package_path = self.packager.package_tool(self.mock_tool, output_dir=self.temp_dir)
        
        # Check if the package was created
        self.assertTrue(os.path.exists(package_path))
        
        # Check if the package contains the necessary files
        self.assertTrue(os.path.exists(os.path.join(package_path, "manifest.json")))
        self.assertTrue(os.path.exists(os.path.join(package_path, "tool.py")))
        
        # Check the manifest content
        with open(os.path.join(package_path, "manifest.json"), "r") as f:
            manifest = json.load(f)
            self.assertEqual(manifest["name"], "test_tool")
            self.assertEqual(manifest["description"], "A test tool")
            self.assertIn("parameter_schema", manifest)
            self.assertIn("result_schema", manifest)
            
    @patch('src.tool_development_kit.ToolValidator')
    def test_package_invalid_tool(self, mock_validator_class):
        # Mock the validator to return an invalid result
        mock_validator = MagicMock()
        mock_validator.validate_tool_interface.return_value = MagicMock(
            is_valid=False, 
            errors=["Missing required method"]
        )
        mock_validator_class.return_value = mock_validator
        
        # Try to package an invalid tool
        with self.assertRaises(ValueError):
            self.packager.package_tool(self.mock_tool, output_dir=self.temp_dir)


class TestToolUpdater(unittest.TestCase):
    def setUp(self):
        # Create a mock registry
        self.mock_registry = MagicMock()
        self.mock_registry.tools = {
            'test_tool': {
                '1.0.0': (MagicMock(), MagicMock(description='Initial version')),
                '1.1.0': (MagicMock(), MagicMock(description='Minor update')),
                '2.0.0': (MagicMock(), MagicMock(description='Major update'))
            }
        }
        self.mock_registry.check_dependencies.return_value = {}
        
        # Create the updater
        self.updater = ToolUpdater(self.mock_registry)
        
    def test_check_for_updates(self):
        # Check for updates
        updates = self.updater.check_for_updates('test_tool')
        
        # Verify updates
        self.assertEqual(len(updates), 2)  # Should find 2 updates
        self.assertEqual(updates[0]['version'], '1.0.0')
        self.assertEqual(updates[1]['version'], '1.1.0')
        
    def test_update_tool(self):
        # Update tool
        result = self.updater.update_tool('test_tool', '2.0.0')
        
        # Verify update
        self.assertTrue(result)
        self.mock_registry.check_dependencies.assert_called_once()
        
    def test_update_tool_with_dependencies(self):
        # Mock dependency check failure
        self.mock_registry.check_dependencies.return_value = {
            'dep1': ['Version mismatch']
        }
        
        # Try to update tool
        result = self.updater.update_tool('test_tool', '2.0.0')
        
        # Verify update failed
        self.assertFalse(result)
        
    def test_update_nonexistent_tool(self):
        # Try to update nonexistent tool
        result = self.updater.update_tool('nonexistent_tool', '1.0.0')
        
        # Verify update failed
        self.assertFalse(result)


class TestToolMigrator(unittest.TestCase):
    def setUp(self):
        # Create a mock registry
        self.mock_registry = MagicMock()
        self.mock_registry.tools = {
            'test_tool': {
                '1.0.0': (MagicMock(), MagicMock()),
                '1.1.0': (MagicMock(), MagicMock()),
                '2.0.0': (MagicMock(), MagicMock())
            }
        }
        
        # Create the migrator
        self.migrator = ToolMigrator(self.mock_registry)
        
    def test_get_migration_path(self):
        # Get migration path
        path = self.migrator.get_migration_path('test_tool', '1.0.0', '2.0.0')
        
        # Verify path
        self.assertEqual(path, ['1.0.0', '1.1.0', '2.0.0'])
        
    def test_get_migration_path_reverse(self):
        # Get reverse migration path
        path = self.migrator.get_migration_path('test_tool', '2.0.0', '1.0.0')
        
        # Verify path
        self.assertEqual(path, ['2.0.0', '1.1.0', '1.0.0'])
        
    def test_migrate_data(self):
        # Mock migration function
        def mock_migration(data):
            data['version'] = '1.1.0'
            return data
            
        # Set up metadata with migration function
        metadata = MagicMock()
        metadata.migrations = {'1.0.0_to_1.1.0': mock_migration}
        self.mock_registry.get_metadata.return_value = metadata
        
        # Migrate data
        data = {'version': '1.0.0', 'value': 'test'}
        result = self.migrator.migrate_data('test_tool', data, '1.0.0', '1.1.0')
        
        # Verify migration
        self.assertEqual(result['version'], '1.1.0')
        self.assertEqual(result['value'], 'test')
        
    def test_migrate_data_no_migration(self):
        # Set up metadata without migration function
        metadata = MagicMock()
        metadata.migrations = {}
        self.mock_registry.get_metadata.return_value = metadata
        
        # Migrate data
        data = {'version': '1.0.0', 'value': 'test'}
        result = self.migrator.migrate_data('test_tool', data, '1.0.0', '1.1.0')
        
        # Verify data unchanged
        self.assertEqual(result, data)
        
    def test_migrate_data_nonexistent_tool(self):
        # Try to migrate data for nonexistent tool
        data = {'version': '1.0.0', 'value': 'test'}
        result = self.migrator.migrate_data('nonexistent_tool', data, '1.0.0', '1.1.0')
        
        # Verify data unchanged
        self.assertEqual(result, data)


class TestDocumentationGenerator(unittest.TestCase):
    def setUp(self):
        # Create a mock tool
        self.mock_tool = MagicMock()
        self.mock_tool.name = "test_tool"
        self.mock_tool.description = "A test tool"
        self.mock_tool.version = "1.0.0"
        self.mock_tool.get_parameter_schema.return_value = {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "First parameter"},
                "param2": {"type": "integer", "description": "Second parameter"}
            },
            "required": ["param1"]
        }
        self.mock_tool.get_result_schema.return_value = {
            "type": "object",
            "properties": {
                "result": {"type": "string", "description": "Result of the operation"}
            }
        }
        self.mock_tool.example = {"param1": "test", "param2": 42}
        
        # Create mock metadata
        self.mock_metadata = MagicMock()
        self.mock_metadata.dependencies = {
            "dep1": ">=1.0.0",
            "dep2": "~=2.0.0"
        }
        self.mock_metadata.changes = [
            "Added new feature X",
            "Fixed bug in Y",
            "Improved performance"
        ]
        
        # Create a mock migration function
        def mock_migration(data):
            """Migrates data from version 1.0.0 to 1.1.0."""
            data['version'] = '1.1.0'
            return data
            
        self.mock_metadata.migrations = {
            '1.0.0_to_1.1.0': mock_migration
        }
        
    def test_generate_markdown_basic(self):
        # Generate basic documentation
        doc = DocumentationGenerator.generate_markdown(self.mock_tool)
        
        # Verify basic sections
        self.assertIn("# test_tool", doc)
        self.assertIn("**Version:** 1.0.0", doc)
        self.assertIn("## Description", doc)
        self.assertIn("## Parameters", doc)
        self.assertIn("## Result", doc)
        self.assertIn("## Example", doc)
        
    def test_generate_markdown_with_metadata(self):
        # Generate documentation with metadata
        doc = DocumentationGenerator.generate_markdown(self.mock_tool, self.mock_metadata)
        
        # Verify metadata sections
        self.assertIn("## Dependencies", doc)
        self.assertIn("- dep1: >=1.0.0", doc)
        self.assertIn("- dep2: ~=2.0.0", doc)
        
        self.assertIn("## Changes", doc)
        self.assertIn("- Added new feature X", doc)
        self.assertIn("- Fixed bug in Y", doc)
        self.assertIn("- Improved performance", doc)
        
        self.assertIn("## Migrations", doc)
        self.assertIn("### 1.0.0 to 1.1.0", doc)
        self.assertIn("Migrates data from version 1.0.0 to 1.1.0", doc)
        
    def test_save_documentation(self):
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save documentation
            filepath = DocumentationGenerator.save_documentation(
                self.mock_tool, temp_dir, self.mock_metadata
            )
            
            # Verify file exists
            self.assertTrue(os.path.exists(filepath))
            
            # Read file content
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Verify content
            self.assertIn("# test_tool", content)
            self.assertIn("## Dependencies", content)
            self.assertIn("## Changes", content)
            self.assertIn("## Migrations", content)


if __name__ == "__main__":
    unittest.main()