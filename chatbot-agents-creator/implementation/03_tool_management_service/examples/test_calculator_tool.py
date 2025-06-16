"""
Tests for the example calculator tool.
"""

import unittest
from calculator_tool import CalculatorTool

class TestCalculatorTool(unittest.TestCase):
    def setUp(self):
        """Set up the calculator tool for testing."""
        self.calculator = CalculatorTool()
        
    def test_parameter_schema(self):
        """Test the parameter schema."""
        schema = self.calculator.get_parameter_schema()
        
        # Check schema type
        self.assertEqual(schema.schema["type"], "object")
        
        # Check properties
        properties = schema.schema["properties"]
        self.assertIn("operation", properties)
        self.assertIn("a", properties)
        self.assertIn("b", properties)
        
        # Check operation enum
        self.assertEqual(properties["operation"]["type"], "string")
        self.assertEqual(properties["operation"]["enum"], ["add", "subtract", "multiply", "divide"])
        
        # Check number types
        self.assertEqual(properties["a"]["type"], "number")
        self.assertEqual(properties["b"]["type"], "number")
        
        # Check required fields
        self.assertEqual(schema.schema["required"], ["operation", "a", "b"])
        
    def test_result_schema(self):
        """Test the result schema."""
        schema = self.calculator.get_result_schema()
        
        # Check schema type
        self.assertEqual(schema.schema["type"], "object")
        
        # Check properties
        properties = schema.schema["properties"]
        self.assertIn("result", properties)
        
        # Check result type
        self.assertEqual(properties["result"]["type"], "number")
        
        # Check required fields
        self.assertEqual(schema.schema["required"], ["result"])
        
    def test_add(self):
        """Test addition operation."""
        result = self.calculator.execute({
            "operation": "add",
            "a": 5,
            "b": 3
        })
        self.assertEqual(result["result"], 8)
        
    def test_subtract(self):
        """Test subtraction operation."""
        result = self.calculator.execute({
            "operation": "subtract",
            "a": 10,
            "b": 4
        })
        self.assertEqual(result["result"], 6)
        
    def test_multiply(self):
        """Test multiplication operation."""
        result = self.calculator.execute({
            "operation": "multiply",
            "a": 6,
            "b": 7
        })
        self.assertEqual(result["result"], 42)
        
    def test_divide(self):
        """Test division operation."""
        result = self.calculator.execute({
            "operation": "divide",
            "a": 20,
            "b": 5
        })
        self.assertEqual(result["result"], 4)
        
    def test_divide_by_zero(self):
        """Test division by zero."""
        with self.assertRaises(ValueError) as context:
            self.calculator.execute({
                "operation": "divide",
                "a": 10,
                "b": 0
            })
        self.assertEqual(str(context.exception), "Division by zero")
        
    def test_invalid_operation(self):
        """Test invalid operation."""
        with self.assertRaises(ValueError) as context:
            self.calculator.execute({
                "operation": "power",
                "a": 2,
                "b": 3
            })
        self.assertEqual(str(context.exception), "Invalid operation: power")
        
    def test_missing_parameters(self):
        """Test missing parameters."""
        with self.assertRaises(KeyError):
            self.calculator.execute({
                "operation": "add",
                "a": 5
            })


if __name__ == "__main__":
    unittest.main() 