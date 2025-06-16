"""
Example calculator tool demonstrating the usage of the Tool Development Kit.
"""

from typing import Dict, Any
from src.tool_interface import ToolInterface, ParameterSchema, ResultSchema

class CalculatorTool(ToolInterface):
    """
    A calculator tool that performs basic arithmetic operations.
    
    This tool demonstrates the usage of the Tool Development Kit, including:
    - Tool interface implementation
    - Parameter and result schema definition
    - Version management
    - Documentation
    - Example usage
    """
    
    def __init__(self):
        """Initialize the calculator tool."""
        super().__init__(
            name="calculator",
            description="A calculator tool that performs basic arithmetic operations",
            version="1.0.0"
        )
        
    def get_parameter_schema(self) -> ParameterSchema:
        """
        Get the parameter schema for the calculator tool.
        
        Returns:
            Parameter schema
        """
        return ParameterSchema({
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The arithmetic operation to perform",
                    "enum": ["add", "subtract", "multiply", "divide"]
                },
                "a": {
                    "type": "number",
                    "description": "First operand"
                },
                "b": {
                    "type": "number",
                    "description": "Second operand"
                }
            },
            "required": ["operation", "a", "b"]
        })
        
    def get_result_schema(self) -> ResultSchema:
        """
        Get the result schema for the calculator tool.
        
        Returns:
            Result schema
        """
        return ResultSchema({
            "type": "object",
            "properties": {
                "result": {
                    "type": "number",
                    "description": "The result of the arithmetic operation"
                }
            },
            "required": ["result"]
        })
        
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the calculator operation.
        
        Args:
            parameters: Dictionary containing:
                - operation: The arithmetic operation to perform
                - a: First operand
                - b: Second operand
                
        Returns:
            Dictionary containing the result
            
        Raises:
            ValueError: If the operation is invalid or division by zero
        """
        operation = parameters["operation"]
        a = parameters["a"]
        b = parameters["b"]
        
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            result = a / b
        else:
            raise ValueError(f"Invalid operation: {operation}")
            
        return {"result": result}
        
    # Example usage
    example = {
        "operation": "add",
        "a": 5,
        "b": 3
    }


# Example usage
if __name__ == "__main__":
    # Create the calculator tool
    calculator = CalculatorTool()
    
    # Test the tool
    test_cases = [
        {"operation": "add", "a": 5, "b": 3},
        {"operation": "subtract", "a": 10, "b": 4},
        {"operation": "multiply", "a": 6, "b": 7},
        {"operation": "divide", "a": 20, "b": 5}
    ]
    
    for test_case in test_cases:
        try:
            result = calculator.execute(test_case)
            print(f"{test_case['operation']}({test_case['a']}, {test_case['b']}) = {result['result']}")
        except ValueError as e:
            print(f"Error: {e}") 