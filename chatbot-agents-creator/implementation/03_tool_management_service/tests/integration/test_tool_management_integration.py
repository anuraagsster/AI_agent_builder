import unittest
import os
import sys
import tempfile
import shutil
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from tool_interface import ToolInterface, FunctionTool, ParameterSchema, ResultSchema
from tool_registry import ToolRegistry, ToolCategory
from tool_development_kit import ToolTemplate, ToolValidator, ToolPackager
from tool_execution import ToolExecutor, ExecutionResult, ExecutionStatus


class SimpleCalculatorTool(ToolInterface):
    """A simple calculator tool for testing."""
    
    def __init__(self):
        self.name = "simple_calculator"
        self.description = "A simple calculator tool for basic arithmetic operations"
        self.category = ToolCategory.UTILITY
        
    def execute(self, parameters):
        """Execute the calculator operation."""
        operation = parameters.get("operation")
        a = parameters.get("a")
        b = parameters.get("b")
        
        if not all([operation, a is not None, b is not None]):
            raise ValueError("Missing required parameters")
            
        if operation == "add":
            return {"result": a + b}
        elif operation == "subtract":
            return {"result": a - b}
        elif operation == "multiply":
            return {"result": a * b}
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            return {"result": a / b}
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    def get_parameter_schema(self):
        """Get the parameter schema for the calculator tool."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The arithmetic operation to perform"
                },
                "a": {
                    "type": "number",
                    "description": "The first operand"
                },
                "b": {
                    "type": "number",
                    "description": "The second operand"
                }
            },
            "required": ["operation", "a", "b"]
        }
        
    def get_result_schema(self):
        """Get the result schema for the calculator tool."""
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "number",
                    "description": "The result of the arithmetic operation"
                }
            },
            "required": ["result"]
        }


def add_numbers(a, b):
    """Add two numbers and return the result."""
    return {"result": a + b}


class TestToolManagementIntegration(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create instances of the components
        self.registry = ToolRegistry()
        self.template = ToolTemplate()
        self.validator = ToolValidator()
        self.packager = ToolPackager()
        self.executor = ToolExecutor(self.registry)
        
        # Create a calculator tool for testing
        self.calculator_tool = SimpleCalculatorTool()
        
        # Create a function tool for testing
        param_schema = {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["a", "b"]
        }
        
        result_schema = {
            "type": "object",
            "properties": {
                "result": {"type": "number"}
            },
            "required": ["result"]
        }
        
        self.function_tool = FunctionTool(
            name="add_numbers",
            description="Add two numbers",
            function=add_numbers,
            parameter_schema=param_schema,
            result_schema=result_schema,
            category=ToolCategory.UTILITY
        )
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)
        
    def test_end_to_end_tool_lifecycle(self):
        """Test the complete lifecycle of a tool from creation to execution."""
        
        # 1. Register the calculator tool
        self.registry.register_tool(self.calculator_tool)
        
        # 2. Verify the tool is registered
        self.assertIn("simple_calculator", self.registry.get_tool_names())
        
        # 3. Get tool metadata
        metadata = self.registry.get_tool_metadata("simple_calculator")
        self.assertEqual(metadata["name"], "simple_calculator")
        self.assertEqual(metadata["category"], ToolCategory.UTILITY)
        
        # 4. Execute the tool
        parameters = {"operation": "add", "a": 5, "b": 3}
        result = self.executor.execute_tool("simple_calculator", parameters)
        
        # 5. Verify the execution result
        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertEqual(result.result["result"], 8)
        
        # 6. Try different operations
        parameters = {"operation": "multiply", "a": 5, "b": 3}
        result = self.executor.execute_tool("simple_calculator", parameters)
        self.assertEqual(result.result["result"], 15)
        
        # 7. Test error handling
        parameters = {"operation": "divide", "a": 5, "b": 0}
        result = self.executor.execute_tool("simple_calculator", parameters)
        self.assertEqual(result.status, ExecutionStatus.ERROR)
        self.assertIn("Division by zero", str(result.error))
        
        # 8. Package the tool
        package_path = self.packager.package_tool(self.calculator_tool, output_dir=self.temp_dir)
        
        # 9. Verify the package
        self.assertTrue(os.path.exists(package_path))
        self.assertTrue(os.path.exists(os.path.join(package_path, "manifest.json")))
        
        # 10. Unregister the tool
        self.registry.unregister_tool("simple_calculator")
        self.assertNotIn("simple_calculator", self.registry.get_tool_names())
        
    def test_function_tool_integration(self):
        """Test the integration of a function-based tool."""
        
        # 1. Register the function tool
        self.registry.register_tool(self.function_tool)
        
        # 2. Verify the tool is registered
        self.assertIn("add_numbers", self.registry.get_tool_names())
        
        # 3. Execute the tool
        parameters = {"a": 10, "b": 20}
        result = self.executor.execute_tool("add_numbers", parameters)
        
        # 4. Verify the execution result
        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertEqual(result.result["result"], 30)
        
        # 5. Unregister the tool
        self.registry.unregister_tool("add_numbers")
        self.assertNotIn("add_numbers", self.registry.get_tool_names())
        
    def test_tool_search_and_categorization(self):
        """Test tool search and categorization features."""
        
        # 1. Register multiple tools
        self.registry.register_tool(self.calculator_tool)  # UTILITY
        self.registry.register_tool(self.function_tool)    # UTILITY
        
        # Create and register a data processing tool
        data_tool = FunctionTool(
            name="process_data",
            description="Process data",
            function=lambda x: {"processed": x},
            parameter_schema={"type": "object", "properties": {"data": {"type": "string"}}},
            result_schema={"type": "object", "properties": {"processed": {"type": "string"}}},
            category=ToolCategory.DATA_PROCESSING
        )
        self.registry.register_tool(data_tool)
        
        # 2. Search for tools
        results = self.registry.search_tools("add")
        self.assertEqual(len(results), 2)  # Both calculator and add_numbers have "add" in name/description
        
        results = self.registry.search_tools("process")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "process_data")
        
        # 3. Get tools by category
        utility_tools = self.registry.get_tools_by_category(ToolCategory.UTILITY)
        self.assertEqual(len(utility_tools), 2)
        
        data_tools = self.registry.get_tools_by_category(ToolCategory.DATA_PROCESSING)
        self.assertEqual(len(data_tools), 1)
        self.assertEqual(data_tools[0].name, "process_data")
        
        # 4. Clean up
        self.registry.unregister_tool("simple_calculator")
        self.registry.unregister_tool("add_numbers")
        self.registry.unregister_tool("process_data")
        
    def test_tool_template_generation(self):
        """Test tool template generation."""
        
        # 1. Generate a tool template
        tool_code = self.template.generate_tool_template(
            name="test_tool",
            description="A test tool",
            parameters=[
                {"name": "param1", "type": "string", "description": "First parameter", "required": True},
                {"name": "param2", "type": "integer", "description": "Second parameter", "required": False}
            ],
            result_type="object"
        )
        
        # 2. Write the template to a file
        template_path = os.path.join(self.temp_dir, "test_tool.py")
        with open(template_path, "w") as f:
            f.write(tool_code)
            
        # 3. Verify the file exists
        self.assertTrue(os.path.exists(template_path))
        
        # 4. Check file content (basic check)
        with open(template_path, "r") as f:
            content = f.read()
            self.assertIn("class TestTool(ToolInterface):", content)
            self.assertIn("def execute(self, parameters):", content)


if __name__ == "__main__":
    unittest.main()