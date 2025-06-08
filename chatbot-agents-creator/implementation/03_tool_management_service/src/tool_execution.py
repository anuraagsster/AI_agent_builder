from typing import Dict, Any, List, Optional, Union, Callable
import time
import traceback
import logging
from .tool_interface import ToolInterface
from .tool_registry import ToolRegistry

class ParameterValidator:
    """
    Validator for tool parameters.
    
    This class validates parameters against a tool's parameter schema.
    """
    
    @staticmethod
    def validate(tool: ToolInterface, parameters: Dict[str, Any]) -> List[str]:
        """
        Validate parameters against a tool's schema.
        
        Args:
            tool: Tool to validate parameters for
            parameters: Parameters to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        return tool.validate_parameters(parameters)
        
    @staticmethod
    def validate_and_transform(tool: ToolInterface, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parameters and transform them to the correct types.
        
        Args:
            tool: Tool to validate parameters for
            parameters: Parameters to validate and transform
            
        Returns:
            Transformed parameters
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate parameters
        errors = ParameterValidator.validate(tool, parameters)
        if errors:
            raise ValueError(f"Invalid parameters: {', '.join(errors)}")
            
        # Get parameter schema
        schema = tool.get_parameter_schema().schema
        properties = schema.get('properties', {})
        
        # Transform parameters
        transformed = {}
        
        for name, value in parameters.items():
            if name in properties:
                prop = properties[name]
                
                # Transform based on type
                if 'type' in prop:
                    if prop['type'] == 'integer' and not isinstance(value, int):
                        try:
                            transformed[name] = int(value)
                            continue
                        except (ValueError, TypeError):
                            pass
                    elif prop['type'] == 'number' and not isinstance(value, (int, float)):
                        try:
                            transformed[name] = float(value)
                            continue
                        except (ValueError, TypeError):
                            pass
                    elif prop['type'] == 'boolean' and not isinstance(value, bool):
                        if isinstance(value, str):
                            if value.lower() in ('true', 'yes', '1'):
                                transformed[name] = True
                                continue
                            elif value.lower() in ('false', 'no', '0'):
                                transformed[name] = False
                                continue
                            
            # No transformation needed or possible
            transformed[name] = value
            
        return transformed


class ResultProcessor:
    """
    Processor for tool results.
    
    This class processes and validates results from tool execution.
    """
    
    @staticmethod
    def validate(tool: ToolInterface, result: Any) -> List[str]:
        """
        Validate a result against a tool's schema.
        
        Args:
            tool: Tool to validate result for
            result: Result to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        return tool.validate_result(result)
        
    @staticmethod
    def process(tool: ToolInterface, result: Any) -> Any:
        """
        Process a result from tool execution.
        
        Args:
            tool: Tool that produced the result
            result: Result to process
            
        Returns:
            Processed result
            
        Raises:
            ValueError: If result is invalid
        """
        # Validate result
        errors = ResultProcessor.validate(tool, result)
        if errors:
            raise ValueError(f"Invalid result: {', '.join(errors)}")
            
        # In a real implementation, this might do additional processing
        # For now, just return the result
        return result


class ExecutionEngine:
    """
    Engine for executing tools.
    
    This class handles the execution of tools, including parameter validation,
    execution, and result processing.
    """
    
    def __init__(self, registry: ToolRegistry = None):
        """
        Initialize the execution engine.
        
        Args:
            registry: Optional tool registry to use
        """
        self.registry = registry or ToolRegistry()
        self.logger = logging.getLogger(__name__)
        
    def execute(self, tool_name: str, parameters: Dict[str, Any], 
               version: str = None, timeout: float = None) -> Dict[str, Any]:
        """
        Execute a tool.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            version: Optional version of the tool (latest if not specified)
            timeout: Optional timeout in seconds
            
        Returns:
            Execution result
            
        Raises:
            ValueError: If tool not found or parameters are invalid
            TimeoutError: If execution times out
        """
        # Get the tool
        tool = self.registry.get_tool(tool_name, version)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}" + 
                           (f" (version {version})" if version else ""))
                           
        # Start execution
        start_time = time.time()
        
        try:
            # Validate and transform parameters
            transformed_params = ParameterValidator.validate_and_transform(tool, parameters)
            
            # Execute the tool
            if timeout:
                # In a real implementation, this would use a proper timeout mechanism
                # For now, just check time after execution
                result = tool.execute(transformed_params)
                
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Tool execution timed out after {timeout} seconds")
            else:
                result = tool.execute(transformed_params)
                
            # Process the result
            processed_result = ResultProcessor.process(tool, result)
            
            # Create execution result
            execution_time = time.time() - start_time
            
            return {
                'success': True,
                'result': processed_result,
                'execution_time': execution_time,
                'tool': {
                    'name': tool_name,
                    'version': tool.version
                }
            }
            
        except Exception as e:
            # Log the error
            self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
            self.logger.debug(traceback.format_exc())
            
            # Create error result
            execution_time = time.time() - start_time
            
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time': execution_time,
                'tool': {
                    'name': tool_name,
                    'version': tool.version if tool else None
                }
            }
            
    def execute_batch(self, executions: List[Dict[str, Any]], 
                     parallel: bool = False) -> List[Dict[str, Any]]:
        """
        Execute multiple tools in batch.
        
        Args:
            executions: List of execution specifications
            parallel: Whether to execute in parallel
            
        Returns:
            List of execution results
        """
        results = []
        
        if parallel:
            # In a real implementation, this would use parallel execution
            # For now, just execute sequentially
            self.logger.warning("Parallel execution not implemented, executing sequentially")
            
        for execution in executions:
            tool_name = execution.get('tool_name')
            parameters = execution.get('parameters', {})
            version = execution.get('version')
            timeout = execution.get('timeout')
            
            if not tool_name:
                results.append({
                    'success': False,
                    'error': "Missing tool_name in execution specification",
                    'error_type': "ValueError"
                })
                continue
                
            result = self.execute(tool_name, parameters, version, timeout)
            results.append(result)
            
        return results