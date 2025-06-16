from typing import Dict, Any, List, Optional, Callable, Type
import inspect
import json
import os
from .tool_interface import ToolInterface, ParameterSchema, ResultSchema, FunctionTool
import logging
import semver

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
    
    This class generates documentation for tools, including update and migration information.
    """
    
    @staticmethod
    def generate_markdown(tool: ToolInterface, metadata: ToolMetadata = None) -> str:
        """
        Generate Markdown documentation for a tool.
        
        Args:
            tool: Tool to document
            metadata: Optional tool metadata
            
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
            doc.append("")
            
        # Add update information if metadata is provided
        if metadata:
            # Add dependencies
            if metadata.dependencies:
                doc.append("## Dependencies")
                doc.append("")
                for dep_name, dep_version in metadata.dependencies.items():
                    doc.append(f"- {dep_name}: {dep_version}")
                doc.append("")
                
            # Add changes
            if hasattr(metadata, 'changes') and metadata.changes:
                doc.append("## Changes")
                doc.append("")
                for change in metadata.changes:
                    doc.append(f"- {change}")
                doc.append("")
                
            # Add migrations
            if hasattr(metadata, 'migrations') and metadata.migrations:
                doc.append("## Migrations")
                doc.append("")
                for migration_key, migration_func in metadata.migrations.items():
                    from_version, to_version = migration_key.split('_to_')
                    doc.append(f"### {from_version} to {to_version}")
                    doc.append("")
                    if hasattr(migration_func, '__doc__') and migration_func.__doc__:
                        doc.append(migration_func.__doc__)
                    doc.append("")
                    
        return "\n".join(doc)
        
    @staticmethod
    def save_documentation(tool: ToolInterface, directory: str, metadata: ToolMetadata = None) -> str:
        """
        Generate and save documentation for a tool.
        
        Args:
            tool: Tool to document
            directory: Directory to save documentation in
            metadata: Optional tool metadata
            
        Returns:
            Path to the documentation file
        """
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate documentation
        doc = DocumentationGenerator.generate_markdown(tool, metadata)
        
        # Save to file
        filename = f"{tool.name.lower().replace(' ', '_')}.md"
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'w') as f:
            f.write(doc)
            
        return filepath


class ToolUpdater:
    """
    Handles tool updates and version management.
    
    This class manages the process of updating tools to new versions,
    including dependency resolution and compatibility checking.
    """
    
    def __init__(self, registry: ToolRegistry):
        """
        Initialize the tool updater.
        
        Args:
            registry: Tool registry to use
        """
        self.registry = registry
        self.logger = logging.getLogger(__name__)
        
    def check_for_updates(self, tool_name: str) -> List[Dict[str, Any]]:
        """
        Check for available updates for a tool.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            List of available updates
        """
        if tool_name not in self.registry.tools:
            return []
            
        current_versions = list(self.registry.tools[tool_name].keys())
        current_versions.sort(key=lambda v: semver.VersionInfo.parse(v))
        latest_version = current_versions[-1]
        
        updates = []
        for version in current_versions:
            if semver.compare(version, latest_version) < 0:
                tool, metadata = self.registry.tools[tool_name][version]
                updates.append({
                    'version': version,
                    'description': metadata.description,
                    'changes': metadata.changes if hasattr(metadata, 'changes') else [],
                    'dependencies': metadata.dependencies
                })
                
        return updates
        
    def update_tool(self, tool_name: str, target_version: str) -> bool:
        """
        Update a tool to a specific version.
        
        Args:
            tool_name: Name of the tool to update
            target_version: Version to update to
            
        Returns:
            True if update was successful, False otherwise
        """
        if tool_name not in self.registry.tools:
            return False
            
        # Check if target version exists
        if target_version not in self.registry.tools[tool_name]:
            return False
            
        # Get current version
        current_versions = list(self.registry.tools[tool_name].keys())
        current_versions.sort(key=lambda v: semver.VersionInfo.parse(v))
        current_version = current_versions[-1]
        
        # Check if update is needed
        if semver.compare(current_version, target_version) >= 0:
            return True
            
        # Get tool and metadata
        tool, metadata = self.registry.tools[tool_name][target_version]
        
        # Check dependencies
        unsatisfied = self.registry.check_dependencies(tool_name, target_version)
        if unsatisfied:
            self.logger.error(f"Unsatisfied dependencies: {unsatisfied}")
            return False
            
        # Perform update
        try:
            # In a real implementation, this would handle the actual update process
            # For now, just log the update
            self.logger.info(f"Updating {tool_name} from {current_version} to {target_version}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update tool: {e}")
            return False


class ToolMigrator:
    """
    Handles tool migrations and compatibility.
    
    This class manages the process of migrating tools between versions,
    including schema changes and data transformations.
    """
    
    def __init__(self, registry: ToolRegistry):
        """
        Initialize the tool migrator.
        
        Args:
            registry: Tool registry to use
        """
        self.registry = registry
        self.logger = logging.getLogger(__name__)
        
    def get_migration_path(self, tool_name: str, from_version: str, to_version: str) -> List[str]:
        """
        Get the migration path between two versions.
        
        Args:
            tool_name: Name of the tool
            from_version: Source version
            to_version: Target version
            
        Returns:
            List of versions in the migration path
        """
        if tool_name not in self.registry.tools:
            return []
            
        # Get all versions
        versions = list(self.registry.tools[tool_name].keys())
        versions.sort(key=lambda v: semver.VersionInfo.parse(v))
        
        # Find indices of from and to versions
        try:
            from_idx = versions.index(from_version)
            to_idx = versions.index(to_version)
        except ValueError:
            return []
            
        # Return versions in the path
        if from_idx < to_idx:
            return versions[from_idx:to_idx + 1]
        else:
            return versions[to_idx:from_idx + 1][::-1]
            
    def migrate_data(self, tool_name: str, data: Dict[str, Any], 
                    from_version: str, to_version: str) -> Dict[str, Any]:
        """
        Migrate data between tool versions.
        
        Args:
            tool_name: Name of the tool
            data: Data to migrate
            from_version: Source version
            to_version: Target version
            
        Returns:
            Migrated data
        """
        if tool_name not in self.registry.tools:
            return data
            
        # Get migration path
        path = self.get_migration_path(tool_name, from_version, to_version)
        if not path:
            return data
            
        # Apply migrations in sequence
        current_data = data
        for i in range(len(path) - 1):
            current_version = path[i]
            next_version = path[i + 1]
            
            # Get migration function
            migration_func = self._get_migration_function(tool_name, current_version, next_version)
            if migration_func:
                try:
                    current_data = migration_func(current_data)
                except Exception as e:
                    self.logger.error(f"Migration failed: {e}")
                    return None
                    
        return current_data
        
    def _get_migration_function(self, tool_name: str, from_version: str, 
                              to_version: str) -> Optional[Callable]:
        """
        Get the migration function between two versions.
        
        Args:
            tool_name: Name of the tool
            from_version: Source version
            to_version: Target version
            
        Returns:
            Migration function, or None if not found
        """
        if tool_name not in self.registry.tools:
            return None
            
        # Get tool metadata
        metadata = self.registry.get_metadata(tool_name, to_version)
        if not metadata or not hasattr(metadata, 'migrations'):
            return None
            
        # Look for migration function
        migration_key = f"{from_version}_to_{to_version}"
        return metadata.migrations.get(migration_key)