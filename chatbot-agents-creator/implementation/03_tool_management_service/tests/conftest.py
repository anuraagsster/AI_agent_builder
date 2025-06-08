import pytest
import tempfile
import os
import shutil
from unittest.mock import MagicMock

# Add the src directory to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from tool_interface import ToolInterface, FunctionTool
from tool_registry import ToolRegistry, ToolCategory
from tool_development_kit import ToolValidator, ToolPackager
from tool_execution import ToolExecutor


class MockTool(ToolInterface):
    """A mock tool for testing."""
    
    def __init__(self, name="mock_tool", description="A mock tool for testing", category=ToolCategory.UTILITY):
        self.name = name
        self.description = description
        self.category = category
        
    def execute(self, parameters):
        """Execute the mock tool."""
        return {"result": "mock_result"}
            
    def get_parameter_schema(self):
        """Get the parameter schema for the mock tool."""
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "integer"}
            },
            "required": ["param1"]
        }
        
    def get_result_schema(self):
        """Get the result schema for the mock tool."""
        return {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            },
            "required": ["result"]
        }


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after the test
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_tool():
    """Create a mock tool for testing."""
    return MockTool()


@pytest.fixture
def mock_function_tool():
    """Create a mock function tool for testing."""
    def mock_function(param1, param2=0):
        return {"result": f"{param1}_{param2}"}
        
    param_schema = {
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "integer"}
        },
        "required": ["param1"]
    }
    
    result_schema = {
        "type": "object",
        "properties": {
            "result": {"type": "string"}
        },
        "required": ["result"]
    }
    
    return FunctionTool(
        name="mock_function_tool",
        description="A mock function tool for testing",
        function=mock_function,
        parameter_schema=param_schema,
        result_schema=result_schema,
        category=ToolCategory.UTILITY
    )


@pytest.fixture
def tool_registry():
    """Create a tool registry for testing."""
    return ToolRegistry()


@pytest.fixture
def populated_registry(tool_registry, mock_tool, mock_function_tool):
    """Create a tool registry populated with mock tools."""
    tool_registry.register_tool(mock_tool)
    tool_registry.register_tool(mock_function_tool)
    
    # Create and register tools for different categories
    data_tool = MockTool(
        name="data_tool",
        description="A data processing tool",
        category=ToolCategory.DATA_PROCESSING
    )
    
    comm_tool = MockTool(
        name="comm_tool",
        description="A communication tool",
        category=ToolCategory.COMMUNICATION
    )
    
    tool_registry.register_tool(data_tool)
    tool_registry.register_tool(comm_tool)
    
    return tool_registry


@pytest.fixture
def tool_validator():
    """Create a tool validator for testing."""
    return ToolValidator()


@pytest.fixture
def tool_packager():
    """Create a tool packager for testing."""
    return ToolPackager()


@pytest.fixture
def tool_executor(tool_registry):
    """Create a tool executor for testing."""
    return ToolExecutor(tool_registry)


@pytest.fixture
def mock_registry_with_error():
    """Create a mock registry that raises an error when getting a tool."""
    mock_registry = MagicMock()
    mock_registry.get_tool.side_effect = KeyError("Tool not found")
    return mock_registry


@pytest.fixture
def mock_tool_with_error():
    """Create a mock tool that raises an error when executed."""
    mock_tool = MagicMock()
    mock_tool.name = "error_tool"
    mock_tool.description = "A tool that raises an error"
    mock_tool.execute.side_effect = ValueError("Execution error")
    return mock_tool