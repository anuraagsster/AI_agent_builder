"""
Common test utilities and helpers for the Foundation Layer tests.
"""

import os
import json
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Dict, Any, Optional

class MockAWSClient:
    """Mock AWS client for testing."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.calls = []
        
    def __getattr__(self, name: str):
        """Create mock methods dynamically."""
        def mock_method(*args, **kwargs):
            self.calls.append({
                'method': name,
                'args': args,
                'kwargs': kwargs
            })
            return MagicMock()
        return mock_method

def load_test_config(config_path: str) -> Dict[str, Any]:
    """Load test configuration from YAML file."""
    config_file = Path(__file__).parent.parent / 'data' / config_path
    with open(config_file) as f:
        return yaml.safe_load(f)

def create_mock_component(component_type: str, **kwargs) -> MagicMock:
    """Create a mock component for testing."""
    mock = MagicMock()
    mock.component_type = component_type
    for key, value in kwargs.items():
        setattr(mock, key, value)
    return mock

def setup_test_environment():
    """Set up test environment variables."""
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    os.environ['AWS_REGION'] = 'us-west-2'

def teardown_test_environment():
    """Clean up test environment variables."""
    for key in ['ENVIRONMENT', 'LOG_LEVEL', 'AWS_REGION']:
        os.environ.pop(key, None)

class TestDataGenerator:
    """Helper class for generating test data."""
    
    @staticmethod
    def create_component_config(component_type: str, **kwargs) -> Dict[str, Any]:
        """Create a component configuration for testing."""
        config = {
            'type': component_type,
            'version': '1.0.0',
            'enabled': True,
            **kwargs
        }
        return config
    
    @staticmethod
    def create_resource_metrics(
        cpu_usage: float = 0.5,
        memory_usage: float = 0.6,
        **kwargs
    ) -> Dict[str, Any]:
        """Create resource metrics for testing."""
        metrics = {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'timestamp': '2024-01-01T00:00:00Z',
            **kwargs
        }
        return metrics

def assert_aws_call(mock_client: MockAWSClient, method: str, **kwargs):
    """Assert that an AWS method was called with specific arguments."""
    for call in mock_client.calls:
        if call['method'] == method:
            for key, value in kwargs.items():
                assert call['kwargs'].get(key) == value, \
                    f"Expected {key}={value}, got {call['kwargs'].get(key)}"
            return
    assert False, f"Method {method} was not called with expected arguments" 