import unittest
from unittest.mock import MagicMock, patch
import tempfile
import os
import json
from src.tool_development_kit import ToolTemplate, ToolValidator, ToolPackager


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


if __name__ == "__main__":
    unittest.main()