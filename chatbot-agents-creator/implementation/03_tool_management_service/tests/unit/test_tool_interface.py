import unittest
from src.tool_interface import ParameterSchema, ResultSchema, ToolInterface, FunctionTool

class TestParameterSchema(unittest.TestCase):
    def test_valid_schema(self):
        # Create a valid schema
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        # This should not raise an exception
        param_schema = ParameterSchema(schema)
        self.assertEqual(param_schema.schema, schema)
        
    def test_invalid_schema(self):
        # Create an invalid schema (missing "type")
        schema = {
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        # This should raise a ValueError
        with self.assertRaises(ValueError):
            ParameterSchema(schema)
            
    def test_validate_parameters(self):
        # Create a schema
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        param_schema = ParameterSchema(schema)
        
        # Test valid parameters
        valid_params = {"name": "John", "age": 30}
        self.assertEqual(param_schema.validate(valid_params), [])
        
        # Test invalid parameters (missing required field)
        invalid_params = {"age": 30}
        self.assertTrue(len(param_schema.validate(invalid_params)) > 0)
        
        # Test invalid parameters (wrong type)
        invalid_params = {"name": "John", "age": "thirty"}
        self.assertTrue(len(param_schema.validate(invalid_params)) > 0)
        
    def test_get_required_parameters(self):
        # Create a schema
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        param_schema = ParameterSchema(schema)
        
        # Test getting required parameters
        self.assertEqual(param_schema.get_required_parameters(), ["name"])


class TestResultSchema(unittest.TestCase):
    def test_valid_schema(self):
        # Create a valid schema
        schema = {
            "type": "object",
            "properties": {
                "result": {"type": "string"},
                "status": {"type": "integer"}
            }
        }
        
        # This should not raise an exception
        result_schema = ResultSchema(schema)
        self.assertEqual(result_schema.schema, schema)
        
    def test_validate_result(self):
        # Create a schema
        schema = {
            "type": "object",
            "properties": {
                "result": {"type": "string"},
                "status": {"type": "integer"}
            },
            "required": ["result"]
        }
        result_schema = ResultSchema(schema)
        
        # Test valid result
        valid_result = {"result": "Success", "status": 200}
        self.assertEqual(result_schema.validate(valid_result), [])
        
        # Test invalid result (missing required field)
        invalid_result = {"status": 200}
        self.assertTrue(len(result_schema.validate(invalid_result)) > 0)


class TestFunctionTool(unittest.TestCase):
    def test_function_tool(self):
        # Create a function to wrap
        def add(a, b):
            return {"sum": a + b}
            
        # Create parameter and result schemas
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
                "sum": {"type": "number"}
            },
            "required": ["sum"]
        }
        
        # Create a function tool
        tool = FunctionTool(
            name="add",
            description="Add two numbers",
            function=add,
            parameter_schema=param_schema,
            result_schema=result_schema
        )
        
        # Test tool execution
        result = tool.execute({"a": 2, "b": 3})
        self.assertEqual(result, {"sum": 5})
        
        # Test parameter validation
        with self.assertRaises(ValueError):
            tool.execute({"a": 2})  # Missing required parameter
            
        with self.assertRaises(ValueError):
            tool.execute({"a": "2", "b": "3"})  # Wrong parameter types


if __name__ == "__main__":
    unittest.main()