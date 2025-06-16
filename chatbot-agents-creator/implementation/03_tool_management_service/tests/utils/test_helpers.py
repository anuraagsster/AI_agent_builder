"""
Common test utilities and helpers for the Tool Management Service tests.
"""

import os
import json
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Dict, Any, Optional, List

class MockToolRegistry:
    """Mock tool registry for testing."""
    
    def __init__(self):
        self.tools = {}
        self.versions = {}
        
    def register_tool(self, tool_id: str, tool_data: Dict[str, Any]):
        """Register a mock tool."""
        self.tools[tool_id] = tool_data
        return MagicMock()
        
    def get_tool(self, tool_id: str, version: Optional[str] = None):
        """Get a mock tool."""
        if tool_id in self.tools:
            return self.tools[tool_id]
        return None

class MockToolExecutor:
    """Mock tool executor for testing."""
    
    def __init__(self):
        self.executions = []
        
    def execute(self, tool_id: str, params: Dict[str, Any]):
        """Mock tool execution."""
        execution = {
            'tool_id': tool_id,
            'params': params,
            'timestamp': '2024-01-01T00:00:00Z'
        }
        self.executions.append(execution)
        return MagicMock()

def load_test_config(config_path: str) -> Dict[str, Any]:
    """Load test configuration from YAML file."""
    config_file = Path(__file__).parent.parent / 'data' / config_path
    with open(config_file) as f:
        return yaml.safe_load(f)

def create_mock_tool(tool_type: str, **kwargs) -> MagicMock:
    """Create a mock tool for testing."""
    mock = MagicMock()
    mock.tool_type = tool_type
    for key, value in kwargs.items():
        setattr(mock, key, value)
    return mock

def setup_test_environment():
    """Set up test environment variables."""
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    os.environ['AWS_REGION'] = 'us-west-2'
    os.environ['TOOL_REGISTRY_PATH'] = 'data/tools'

def teardown_test_environment():
    """Clean up test environment variables."""
    for key in ['ENVIRONMENT', 'LOG_LEVEL', 'AWS_REGION', 'TOOL_REGISTRY_PATH']:
        os.environ.pop(key, None)

class TestDataGenerator:
    """Helper class for generating test data."""
    
    @staticmethod
    def create_tool_definition(
        name: str,
        version: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a tool definition for testing."""
        tool = {
            'name': name,
            'version': version,
            'parameters': parameters or {},
            'timestamp': '2024-01-01T00:00:00Z',
            **kwargs
        }
        return tool
    
    @staticmethod
    def create_tool_execution(
        tool_id: str,
        params: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Create a tool execution record for testing."""
        execution = {
            'tool_id': tool_id,
            'params': params,
            'timestamp': '2024-01-01T00:00:00Z',
            **kwargs
        }
        return execution

def assert_tool_execution(mock_executor: MockToolExecutor, tool_id: str, **kwargs):
    """Assert that a tool was executed with specific parameters."""
    for execution in mock_executor.executions:
        if execution['tool_id'] == tool_id:
            for key, value in kwargs.items():
                assert execution['params'].get(key) == value, \
                    f"Expected {key}={value}, got {execution['params'].get(key)}"
            return
    assert False, f"Tool {tool_id} was not executed with expected parameters" 