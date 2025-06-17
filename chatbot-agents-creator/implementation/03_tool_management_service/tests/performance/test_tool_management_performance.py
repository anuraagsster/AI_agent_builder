"""
Performance tests for the Tool Management Service.

These tests measure the performance characteristics of the service under
various conditions and loads.
"""

import unittest
import time
import statistics
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from src.tool_registry import ToolRegistry
from src.tool_execution_engine import ToolExecutionEngine
from src.mcp_compliance import MCPComplianceLayer
from src.tool_development_kit import ToolTemplate


class TestToolManagementPerformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the test environment for all tests."""
        # Initialize components
        cls.registry = ToolRegistry()
        cls.execution_engine = ToolExecutionEngine(cls.registry)
        
        # Initialize MCP compliance layer
        cls.compliance_config = {
            'security': {
                'encryption_key_file': None,
                'kms_key_id': 'test-key-id',
                'token_expiry': 3600
            },
            'audit': {
                'audit_stream_name': 'test-stream',
                'cloudwatch_namespace': 'ToolManagementService/Audit'
            },
            'access': {
                'permissions_table': 'test-permissions',
                'user_groups_table': 'test-user-groups',
                'group_permissions_table': 'test-group-permissions'
            }
        }
        cls.compliance = MCPComplianceLayer(cls.compliance_config)
        
        # Create test tools
        cls.tool_template = ToolTemplate()
        cls.create_test_tools()
        
    @classmethod
    def create_test_tools(cls):
        """Create test tools for performance testing."""
        # Create simple tool
        cls.simple_tool = cls.tool_template.create_tool(
            name="simple_tool",
            description="Simple tool for performance testing",
            version="1.0.0",
            parameter_schema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                }
            },
            result_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            },
            execute_func=lambda params: {
                "result": f"Processed: {params['input']}"
            }
        )
        
        # Create complex tool
        cls.complex_tool = cls.tool_template.create_tool(
            name="complex_tool",
            description="Complex tool for performance testing",
            version="1.0.0",
            parameter_schema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                    "options": {
                        "type": "object",
                        "properties": {
                            "process": {"type": "boolean"},
                            "format": {"type": "string"},
                            "iterations": {"type": "integer"}
                        }
                    }
                }
            },
            result_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "iterations": {"type": "integer"},
                            "processing_time": {"type": "number"}
                        }
                    }
                }
            },
            execute_func=lambda params: {
                "result": f"Processed: {params['input']}",
                "metadata": {
                    "iterations": params.get("options", {}).get("iterations", 1),
                    "processing_time": time.time()
                }
            }
        )
        
    def setUp(self):
        """Set up each test case."""
        # Clear registry before each test
        self.registry.clear()
        
        # Register tools
        self.registry.register_tool(self.simple_tool)
        self.registry.register_tool(self.complex_tool)
        
    def measure_execution_time(self, func, *args, **kwargs):
        """Measure the execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
        
    def test_registration_performance(self):
        """Test the performance of tool registration."""
        # Measure registration time for multiple tools
        registration_times = []
        for i in range(100):
            tool = self.tool_template.create_tool(
                name=f"test_tool_{i}",
                description=f"Test tool {i}",
                version="1.0.0",
                parameter_schema={"type": "object"},
                result_schema={"type": "object"},
                execute_func=lambda x: x
            )
            _, execution_time = self.measure_execution_time(
                self.registry.register_tool,
                tool
            )
            registration_times.append(execution_time)
            
        # Calculate statistics
        avg_time = statistics.mean(registration_times)
        max_time = max(registration_times)
        min_time = min(registration_times)
        
        # Assert performance requirements
        self.assertLess(avg_time, 0.1)  # Average registration time < 100ms
        self.assertLess(max_time, 0.5)  # Maximum registration time < 500ms
        
    def test_execution_performance(self):
        """Test the performance of tool execution."""
        # Measure execution time for simple tool
        simple_times = []
        for _ in range(1000):
            _, execution_time = self.measure_execution_time(
                self.execution_engine.execute_tool,
                "simple_tool",
                {"input": "test"}
            )
            simple_times.append(execution_time)
            
        # Calculate statistics for simple tool
        simple_avg = statistics.mean(simple_times)
        simple_max = max(simple_times)
        
        # Assert performance requirements for simple tool
        self.assertLess(simple_avg, 0.05)  # Average execution time < 50ms
        self.assertLess(simple_max, 0.2)   # Maximum execution time < 200ms
        
        # Measure execution time for complex tool
        complex_times = []
        for _ in range(100):
            _, execution_time = self.measure_execution_time(
                self.execution_engine.execute_tool,
                "complex_tool",
                {
                    "input": "test",
                    "options": {
                        "process": True,
                        "format": "json",
                        "iterations": 10
                    }
                }
            )
            complex_times.append(execution_time)
            
        # Calculate statistics for complex tool
        complex_avg = statistics.mean(complex_times)
        complex_max = max(complex_times)
        
        # Assert performance requirements for complex tool
        self.assertLess(complex_avg, 0.2)  # Average execution time < 200ms
        self.assertLess(complex_max, 0.5)  # Maximum execution time < 500ms
        
    def test_concurrent_execution(self):
        """Test the performance under concurrent execution."""
        def execute_tool(tool_name, params):
            return self.execution_engine.execute_tool(tool_name, params)
            
        # Execute multiple tools concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit 100 concurrent executions
            futures = []
            for i in range(100):
                if i % 2 == 0:
                    futures.append(
                        executor.submit(
                            execute_tool,
                            "simple_tool",
                            {"input": f"test_{i}"}
                        )
                    )
                else:
                    futures.append(
                        executor.submit(
                            execute_tool,
                            "complex_tool",
                            {
                                "input": f"test_{i}",
                                "options": {
                                    "process": True,
                                    "format": "json",
                                    "iterations": 5
                                }
                            }
                        )
                    )
                    
            # Measure completion times
            completion_times = []
            for future in futures:
                start_time = time.time()
                future.result()
                completion_times.append(time.time() - start_time)
                
            # Calculate statistics
            avg_time = statistics.mean(completion_times)
            max_time = max(completion_times)
            
            # Assert performance requirements
            self.assertLess(avg_time, 0.3)  # Average completion time < 300ms
            self.assertLess(max_time, 1.0)  # Maximum completion time < 1s
            
    def test_memory_usage(self):
        """Test memory usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and register many tools
        tools = []
        for i in range(1000):
            tool = self.tool_template.create_tool(
                name=f"memory_tool_{i}",
                description=f"Memory test tool {i}",
                version="1.0.0",
                parameter_schema={"type": "object"},
                result_schema={"type": "object"},
                execute_func=lambda x: x
            )
            tools.append(tool)
            self.registry.register_tool(tool)
            
        # Measure memory usage
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Assert memory requirements
        self.assertLess(memory_increase, 100)  # Memory increase < 100MB
        
    def test_audit_logging_performance(self):
        """Test the performance of audit logging."""
        # Measure logging time for multiple events
        logging_times = []
        for i in range(1000):
            _, execution_time = self.measure_execution_time(
                self.compliance.audit_logger.log_event,
                "test_event",
                "test_user",
                "test_action",
                "test_resource",
                {"index": i}
            )
            logging_times.append(execution_time)
            
        # Calculate statistics
        avg_time = statistics.mean(logging_times)
        max_time = max(logging_times)
        
        # Assert performance requirements
        self.assertLess(avg_time, 0.1)  # Average logging time < 100ms
        self.assertLess(max_time, 0.5)  # Maximum logging time < 500ms


if __name__ == '__main__':
    unittest.main() 