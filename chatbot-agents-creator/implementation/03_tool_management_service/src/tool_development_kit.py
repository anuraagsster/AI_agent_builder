from typing import Dict, Any, List, Optional, Callable, Type
import inspect
import json
import os
from .tool_interface import ToolInterface, ParameterSchema, ResultSchema, FunctionTool

class ToolTemplate:
    """
    Template for creating new tools.
    
    This class provides templates for common tool patterns to accelerate development.
    """
    
    @staticmethod
    def create_function_tool(func: Callable, name: str = None, description: str = None,
                            parameter_schema: Dict[str, Any] = None, 
                            result_schema: Dict[str, Any] = None,
                            version: str = "1.0.0") -> FunctionTool:
        """
        Create a tool from a function.
        
        Args:
            func: Function to wrap
            name: Optional name for the tool (default: function name)
            description: Optional description for the tool
            parameter_schema: Optional parameter schema (default: generated from function signature)
            result_schema: Optional result schema
            version: Optional version for the tool
            
        Returns:
            Function tool
        """
        # Use function name if not provided
        if name is None:
            name = func.__name__
            
        # Use function docstring if description not provided
        if description is None:
            description = inspect.getdoc(func) or f"Tool for {name}"
            
        # Generate parameter schema if not provided
        if parameter_schema is None:
            parameter_schema = ToolTemplate._generate_parameter_schema(func)
            
        # Generate basic result schema if not provided
        if result_schema is None:
            result_schema = {
                "type": "object",
                "additionalProperties": True
            }
            
        return FunctionTool(
            name=name,
            description=description,
            function=func,
            parameter_schema=parameter_schema,
            result_schema=result_schema,
            version=version
        )
        
    @staticmethod
    def _generate_parameter_schema(func: Callable) -> Dict[str, Any]:
        """
        Generate a parameter schema from a function signature.
        
        Args:
            func: Function to analyze
            
        Returns:
            Parameter schema
        """
        signature = inspect.signature(func)
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for name, param in signature.parameters.items():
            # Skip self parameter for methods
            if name == 'self':
                continue
                
            # Add parameter to schema
            schema["properties"][name] = {
                "type": "string",  # Default type
                "description": ""
            }
            
            # Add to required list if no default value
            if param.default == inspect.Parameter.empty:
                schema["required"].append(name)
                
            # Try to infer type from annotations
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == str:
                    schema["properties"][name]["type"] = "string"
                elif param.annotation == int:
                    schema["properties"][name]["type"] = "integer"
                elif param.annotation == float:
                    schema["properties"][name]["type"] = "number"
                elif param.annotation == bool:
                    schema["properties"][name]["type"] = "boolean"
                elif param.annotation == list or param.annotation == List:
                    schema["properties"][name]["type"] = "array"
                elif param.annotation == dict or param.annotation == Dict:
                    schema["properties"][name]["type"] = "object"
                    
        return schema


class ToolTester:
    """
    Tester for tools.
    
    This class provides functionality for testing tools.
    """
    
    def __init__(self, tool: ToolInterface):
        """
        Initialize the tool tester.
        
        Args:
            tool: Tool to test
        """
        self.tool = tool
        self.test_cases = []
        
    def add_test_case(self, parameters: Dict[str, Any], expected_result: Any = None,
                     expected_error: str = None, name: str = None) -> None:
        """
        Add a test case.
        
        Args:
            parameters: Parameters for the test case
            expected_result: Expected result (None if expecting error)
            expected_error: Expected error message (None if expecting success)
            name: Optional name for the test case
        """
        if name is None:
            name = f"Test case {len(self.test_cases) + 1}"
            
        self.test_cases.append({
            'name': name,
            'parameters': parameters,
            'expected_result': expected_result,
            'expected_error': expected_error
        })
        
    def run_tests(self) -> Dict[str, Any]:
        """
        Run all test cases.
        
        Returns:
            Test results
        """
        results = {
            'tool': self.tool.name,
            'version': self.tool.version,
            'total': len(self.test_cases),
            'passed': 0,
            'failed': 0,
            'test_results': []
        }
        
        for test_case in self.test_cases:
            test_result = self._run_test_case(test_case)
            results['test_results'].append(test_result)
            
            if test_result['passed']:
                results['passed'] += 1
            else:
                results['failed'] += 1
                
        return results
        
    def _run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single test case.
        
        Args:
            test_case: Test case to run
            
        Returns:
            Test result
        """
        result = {
            'name': test_case['name'],
            'parameters': test_case['parameters'],
            'passed': False,
            'error': None,
            'actual_result': None
        }
        
        try:
            # Validate parameters
            param_errors = self.tool.validate_parameters(test_case['parameters'])
            if param_errors:
                if test_case['expected_error']:
                    # Expected an error, check if it matches
                    result['passed'] = any(error in test_case['expected_error'] for error in param_errors)
                    result['error'] = param_errors
                else:
                    # Not expecting an error
                    result['passed'] = False
                    result['error'] = param_errors
                return result
                
            # Execute the tool
            actual_result = self.tool.execute(test_case['parameters'])
            result['actual_result'] = actual_result
            
            if test_case['expected_error']:
                # Expected an error but didn't get one
                result['passed'] = False
                return result
                
            if test_case['expected_result'] is not None:
                # Compare with expected result
                if isinstance(test_case['expected_result'], dict) and isinstance(actual_result, dict):
                    # For dictionaries, check if expected keys are in actual result
                    result['passed'] = all(
                        k in actual_result and actual_result[k] == v
                        for k, v in test_case['expected_result'].items()
                    )
                else:
                    # Direct comparison
                    result['passed'] = actual_result == test_case['expected_result']
            else:
                # No expected result specified, just check for no errors
                result['passed'] = True
                
        except Exception as e:
            result['error'] = str(e)
            
            if test_case['expected_error']:
                # Expected an error, check if it matches
                result['passed'] = test_case['expected_error'] in str(e)
            else:
                # Not expecting an error
                result['passed'] = False
                
        return result


class DocumentationGenerator:
    """
    Generator for tool documentation.
    
    This class generates documentation for tools.
    """
    
    @staticmethod
    def generate_markdown(tool: ToolInterface) -> str:
        """
        Generate Markdown documentation for a tool.
        
        Args:
            tool: Tool to document
            
        Returns:
            Markdown documentation
        """
        parameter_schema = tool.get_parameter_schema()
        result_schema = tool.get_result_schema()
        
        # Build documentation
        doc = [
            f"# {tool.name}",
            "",
            f"**Version:** {tool.version}",
            "",
            f"## Description",
            "",
            tool.description,
            "",
            f"## Parameters",
            ""
        ]
        
        # Add parameters
        properties = parameter_schema.schema.get('properties', {})
        required = parameter_schema.schema.get('required', [])
        
        for name, prop in properties.items():
            req_str = " (required)" if name in required else " (optional)"
            doc.append(f"### `{name}`{req_str}")
            doc.append("")
            
            if 'description' in prop and prop['description']:
                doc.append(prop['description'])
                doc.append("")
                
            doc.append(f"**Type:** {prop.get('type', 'any')}")
            
            if 'default' in prop:
                doc.append(f"**Default:** `{prop['default']}`")
                
            doc.append("")
            
        # Add result schema
        doc.append("## Result")
        doc.append("")
        
        if 'description' in result_schema.schema and result_schema.schema['description']:
            doc.append(result_schema.schema['description'])
            doc.append("")
            
        doc.append("**Schema:**")
        doc.append("```json")
        doc.append(json.dumps(result_schema.schema, indent=2))
        doc.append("```")
        doc.append("")
        
        # Add example (if available)
        if hasattr(tool, 'example'):
            doc.append("## Example")
            doc.append("")
            doc.append("```json")
            doc.append(json.dumps(tool.example, indent=2))
            doc.append("```")
            
        return "\n".join(doc)
        
    @staticmethod
    def save_documentation(tool: ToolInterface, directory: str) -> str:
        """
        Generate and save documentation for a tool.
        
        Args:
            tool: Tool to document
            directory: Directory to save documentation in
            
        Returns:
            Path to the documentation file
        """
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate documentation
        doc = DocumentationGenerator.generate_markdown(tool)
        
        # Save to file
        filename = f"{tool.name.lower().replace(' ', '_')}.md"
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'w') as f:
            f.write(doc)
            
        return filepath