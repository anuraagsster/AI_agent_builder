from typing import Dict, Any, List, Optional, Union, Callable
from abc import ABC, abstractmethod
import json
import jsonschema

class ParameterSchema:
    """
    Defines the schema for tool parameters.
    
    This class validates that parameters passed to a tool conform to the expected schema.
    """
    
    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize the parameter schema.
        
        Args:
            schema: JSON Schema definition for the parameters
        """
        self.schema = schema
        
        # Validate that the schema itself is valid
        try:
            jsonschema.validators.validate(schema, jsonschema.Draft7Validator.META_SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            raise ValueError(f"Invalid parameter schema: {str(e)}")
            
    def validate(self, parameters: Dict[str, Any]) -> List[str]:
        """
        Validate parameters against the schema.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        try:
            jsonschema.validators.validate(parameters, self.schema)
            return []
        except jsonschema.exceptions.ValidationError as e:
            return [str(e)]
            
    def get_required_parameters(self) -> List[str]:
        """
        Get the list of required parameters.
        
        Returns:
            List of required parameter names
        """
        return self.schema.get('required', [])
        
    def get_parameter_description(self, parameter_name: str) -> str:
        """
        Get the description of a parameter.
        
        Args:
            parameter_name: Name of the parameter
            
        Returns:
            Description of the parameter
        """
        properties = self.schema.get('properties', {})
        if parameter_name in properties:
            return properties[parameter_name].get('description', '')
        return ''
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the schema to a dictionary.
        
        Returns:
            Dictionary representation of the schema
        """
        return self.schema


class ResultSchema:
    """
    Defines the schema for tool results.
    
    This class validates that results returned by a tool conform to the expected schema.
    """
    
    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize the result schema.
        
        Args:
            schema: JSON Schema definition for the results
        """
        self.schema = schema
        
        # Validate that the schema itself is valid
        try:
            jsonschema.validators.validate(schema, jsonschema.Draft7Validator.META_SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            raise ValueError(f"Invalid result schema: {str(e)}")
            
    def validate(self, result: Any) -> List[str]:
        """
        Validate a result against the schema.
        
        Args:
            result: Result to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        try:
            jsonschema.validators.validate(result, self.schema)
            return []
        except jsonschema.exceptions.ValidationError as e:
            return [str(e)]
            
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the schema to a dictionary.
        
        Returns:
            Dictionary representation of the schema
        """
        return self.schema


class ToolInterface(ABC):
    """
    Abstract base class for all tools.
    
    This class defines the interface that all tools must implement.
    """
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        """
        Initialize the tool.
        
        Args:
            name: Name of the tool
            description: Description of the tool
            version: Version of the tool
        """
        self.name = name
        self.description = description
        self.version = version
        
    @abstractmethod
    def get_parameter_schema(self) -> ParameterSchema:
        """
        Get the parameter schema for the tool.
        
        Returns:
            Parameter schema
        """
        pass
        
    @abstractmethod
    def get_result_schema(self) -> ResultSchema:
        """
        Get the result schema for the tool.
        
        Returns:
            Result schema
        """
        pass
        
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Any:
        """
        Execute the tool with the given parameters.
        
        Args:
            parameters: Parameters for the tool
            
        Returns:
            Result of the tool execution
        """
        pass
        
    def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """
        Validate parameters against the schema.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        schema = self.get_parameter_schema()
        return schema.validate(parameters)
        
    def validate_result(self, result: Any) -> List[str]:
        """
        Validate a result against the schema.
        
        Args:
            result: Result to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        schema = self.get_result_schema()
        return schema.validate(result)
        
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the tool.
        
        Returns:
            Dictionary with tool metadata
        """
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'parameter_schema': self.get_parameter_schema().to_dict(),
            'result_schema': self.get_result_schema().to_dict()
        }


class FunctionTool(ToolInterface):
    """
    Tool implementation that wraps a function.
    
    This class allows creating tools from existing functions.
    """
    
    def __init__(self, name: str, description: str, function: Callable, 
                 parameter_schema: Dict[str, Any], result_schema: Dict[str, Any],
                 version: str = "1.0.0"):
        """
        Initialize the function tool.
        
        Args:
            name: Name of the tool
            description: Description of the tool
            function: Function to execute
            parameter_schema: JSON Schema for parameters
            result_schema: JSON Schema for results
            version: Version of the tool
        """
        super().__init__(name, description, version)
        self.function = function
        self._parameter_schema = ParameterSchema(parameter_schema)
        self._result_schema = ResultSchema(result_schema)
        
    def get_parameter_schema(self) -> ParameterSchema:
        """
        Get the parameter schema for the tool.
        
        Returns:
            Parameter schema
        """
        return self._parameter_schema
        
    def get_result_schema(self) -> ResultSchema:
        """
        Get the result schema for the tool.
        
        Returns:
            Result schema
        """
        return self._result_schema
        
    def execute(self, parameters: Dict[str, Any]) -> Any:
        """
        Execute the function with the given parameters.
        
        Args:
            parameters: Parameters for the function
            
        Returns:
            Result of the function execution
        """
        # Validate parameters
        errors = self.validate_parameters(parameters)
        if errors:
            raise ValueError(f"Invalid parameters: {', '.join(errors)}")
            
        # Execute the function
        result = self.function(**parameters)
        
        # Validate result
        errors = self.validate_result(result)
        if errors:
            raise ValueError(f"Invalid result: {', '.join(errors)}")
            
        return result