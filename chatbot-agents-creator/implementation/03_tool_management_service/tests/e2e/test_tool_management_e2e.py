"""
End-to-end tests for the Tool Management Service.

These tests verify the complete flow of the service from tool registration
to execution, including all components working together.
"""

import unittest
import json
import os
import time
from datetime import datetime

from src.tool_registry import ToolRegistry
from src.tool_execution_engine import ToolExecutionEngine
from src.mcp_compliance import MCPComplianceLayer
from src.tool_development_kit import ToolTemplate, ToolTester


class TestToolManagementE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the test environment for all tests."""
        # Initialize all components
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
        """Create a set of test tools for E2E testing."""
        # Create main tool
        cls.main_tool = cls.tool_template.create_tool(
            name="main_tool",
            description="Main tool for E2E testing",
            version="1.0.0",
            parameter_schema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                    "options": {
                        "type": "object",
                        "properties": {
                            "process": {"type": "boolean"},
                            "format": {"type": "string"}
                        }
                    }
                },
                "required": ["input"]
            },
            result_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "processed": {"type": "boolean"},
                            "format": {"type": "string"}
                        }
                    }
                }
            },
            execute_func=lambda params: {
                "result": f"Processed: {params['input']}",
                "metadata": {
                    "processed": params.get("options", {}).get("process", False),
                    "format": params.get("options", {}).get("format", "default")
                }
            }
        )
        
        # Create dependent tool
        cls.dependent_tool = cls.tool_template.create_tool(
            name="dependent_tool",
            description="Tool that depends on main_tool",
            version="1.0.0",
            dependencies={"main_tool": "1.0.0"},
            parameter_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "string"},
                    "use_main": {"type": "boolean"}
                }
            },
            result_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "source": {"type": "string"}
                }
            },
            execute_func=lambda params: {
                "result": f"Dependent: {params['data']}",
                "source": "main_tool" if params.get("use_main") else "self"
            }
        )
        
    def setUp(self):
        """Set up each test case."""
        # Clear registry before each test
        self.registry.clear()
        
        # Register tools
        self.registry.register_tool(self.main_tool)
        self.registry.register_tool(self.dependent_tool)
        
        # Generate test token
        self.token = self.compliance.security_manager.generate_token(
            "test_user",
            {"read", "write", "execute"}
        )
        
    def test_complete_tool_workflow(self):
        """Test the complete workflow of tool registration, execution, and monitoring."""
        # 1. Verify tool registration
        self.assertTrue(self.registry.is_tool_registered("main_tool"))
        self.assertTrue(self.registry.is_tool_registered("dependent_tool"))
        
        # 2. Verify dependencies
        dependencies = self.registry.get_tool_dependencies("dependent_tool")
        self.assertIn("main_tool", dependencies)
        
        # 3. Execute main tool
        main_result = self.execution_engine.execute_tool(
            "main_tool",
            {
                "input": "test_input",
                "options": {
                    "process": True,
                    "format": "json"
                }
            }
        )
        self.assertEqual(main_result["result"], "Processed: test_input")
        self.assertTrue(main_result["metadata"]["processed"])
        self.assertEqual(main_result["metadata"]["format"], "json")
        
        # 4. Execute dependent tool
        dep_result = self.execution_engine.execute_tool(
            "dependent_tool",
            {
                "data": "test_data",
                "use_main": True
            }
        )
        self.assertEqual(dep_result["result"], "Dependent: test_data")
        self.assertEqual(dep_result["source"], "main_tool")
        
        # 5. Verify audit logs
        audit_events = self.compliance.audit_logger.get_recent_events(
            "test_user",
            limit=2
        )
        self.assertEqual(len(audit_events), 2)
        self.assertEqual(audit_events[0]["event_type"], "tool_execution")
        self.assertEqual(audit_events[1]["event_type"], "tool_execution")
        
    def test_tool_update_workflow(self):
        """Test the complete workflow of tool updates and version management."""
        # 1. Create updated version
        updated_tool = self.tool_template.create_tool(
            name="main_tool",
            description="Updated main tool",
            version="1.1.0",
            parameter_schema={
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                    "options": {
                        "type": "object",
                        "properties": {
                            "process": {"type": "boolean"},
                            "format": {"type": "string"},
                            "new_option": {"type": "string"}
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
                            "processed": {"type": "boolean"},
                            "format": {"type": "string"},
                            "new_field": {"type": "string"}
                        }
                    }
                }
            },
            execute_func=lambda params: {
                "result": f"Updated: {params['input']}",
                "metadata": {
                    "processed": params.get("options", {}).get("process", False),
                    "format": params.get("options", {}).get("format", "default"),
                    "new_field": params.get("options", {}).get("new_option", "default")
                }
            }
        )
        
        # 2. Update tool
        self.registry.update_tool(updated_tool)
        
        # 3. Verify version update
        current_version = self.registry.get_tool_version("main_tool")
        self.assertEqual(current_version, "1.1.0")
        
        # 4. Execute updated tool
        result = self.execution_engine.execute_tool(
            "main_tool",
            {
                "input": "test_input",
                "options": {
                    "process": True,
                    "format": "json",
                    "new_option": "test"
                }
            }
        )
        self.assertEqual(result["result"], "Updated: test_input")
        self.assertEqual(result["metadata"]["new_field"], "test")
        
        # 5. Verify audit logs
        audit_events = self.compliance.audit_logger.get_recent_events(
            "test_user",
            limit=1
        )
        self.assertEqual(audit_events[0]["event_type"], "tool_update")
        
    def test_error_handling_workflow(self):
        """Test the complete workflow of error handling and recovery."""
        # 1. Create error-prone tool
        error_tool = self.tool_template.create_tool(
            name="error_tool",
            description="Tool that simulates errors",
            version="1.0.0",
            parameter_schema={
                "type": "object",
                "properties": {
                    "error_type": {"type": "string"},
                    "recover": {"type": "boolean"}
                }
            },
            result_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "error": {"type": "string"}
                }
            },
            execute_func=lambda params: {
                "result": "success" if params.get("recover") else None,
                "error": params.get("error_type", "unknown")
            }
        )
        
        # 2. Register and execute error tool
        self.registry.register_tool(error_tool)
        
        # 3. Test error case
        with self.assertRaises(Exception):
            self.execution_engine.execute_tool(
                "error_tool",
                {
                    "error_type": "test_error",
                    "recover": False
                }
            )
            
        # 4. Test recovery case
        result = self.execution_engine.execute_tool(
            "error_tool",
            {
                "error_type": "test_error",
                "recover": True
            }
        )
        self.assertEqual(result["result"], "success")
        
        # 5. Verify error logs
        audit_events = self.compliance.audit_logger.get_recent_events(
            "test_user",
            limit=2
        )
        self.assertEqual(audit_events[0]["event_type"], "tool_error")
        self.assertEqual(audit_events[1]["event_type"], "tool_execution")


if __name__ == '__main__':
    unittest.main() 