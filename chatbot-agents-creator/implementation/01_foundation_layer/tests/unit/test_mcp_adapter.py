import unittest
from unittest.mock import patch, MagicMock
import sys
import importlib
from datetime import datetime
import json

# Add path to src directory
sys.path.append('chatbot-agents-creator/implementation/01_foundation_layer/src')

from agent_framework.framework_adapters.mcp_adapter import MCPAdapter

class TestMCPAdapter(unittest.TestCase):
    
    def setUp(self):
        # Create a mock config
        self.config = {
            'verbose': True
        }
        
    @patch('importlib.import_module')
    def test_init_mcp_available(self, mock_import):
        # Setup mock
        mock_import.return_value = MagicMock()
        
        # Create adapter
        adapter = MCPAdapter(self.config)
        
        # Verify
        self.assertTrue(adapter._mcp_available)
        mock_import.assert_called_once_with('mcp_sdk')
        
    @patch('importlib.import_module')
    def test_init_mcp_not_available(self, mock_import):
        # Setup mock to raise ImportError
        mock_import.side_effect = ImportError("No module named 'mcp_sdk'")
        
        # Create adapter
        adapter = MCPAdapter(self.config)
        
        # Verify
        self.assertFalse(adapter._mcp_available)
        
    @patch('importlib.import_module')
    def test_register_mcp_tool(self, mock_import):
        # Setup mocks
        mock_mcp_sdk = MagicMock()
        mock_tool_class = MagicMock()
        mock_mcp_sdk.Tool = mock_tool_class
        mock_import.return_value = mock_mcp_sdk
        
        # Create adapter
        adapter = MCPAdapter(self.config)
        adapter.mcp_tool_class = mock_tool_class
        
        # Test data
        tool_config = {
            'tool_id': 'test-tool-123',
            'name': 'Test Tool',
            'description': 'A test tool',
            'input_schema': {'type': 'object', 'properties': {}},
            'output_schema': {'type': 'object', 'properties': {}},
            'owner_id': 'test-owner',
            'ownership_type': 'system',
            'exportable': True
        }
        
        # Call method
        result = adapter.register_mcp_tool(tool_config)
        
        # Verify
        mock_tool_class.assert_called_once()
        self.assertEqual(result.original_tool_id, 'test-tool-123')
        self.assertEqual(result.owner_id, 'test-owner')
        self.assertEqual(result.ownership_type, 'system')
        self.assertEqual(result.exportable, True)
        
    @patch('importlib.import_module')
    def test_convert_to_mcp_resource(self, mock_import):
        # Setup mocks
        mock_mcp_sdk = MagicMock()
        mock_resource_class = MagicMock()
        mock_mcp_sdk.Resource = mock_resource_class
        mock_import.return_value = mock_mcp_sdk
        
        # Create adapter
        adapter = MCPAdapter(self.config)
        adapter.mcp_resource_class = mock_resource_class
        
        # Test data
        resource = {
            'resource_id': 'test-resource-123',
            'uri': 'resource://test',
            'content_type': 'application/json',
            'data': {'key': 'value'},
            'owner_id': 'test-owner',
            'ownership_type': 'system'
        }
        
        # Call method
        result = adapter.convert_to_mcp_resource(resource)
        
        # Verify
        mock_resource_class.assert_called_once()
        self.assertEqual(result.original_resource_id, 'test-resource-123')
        self.assertEqual(result.owner_id, 'test-owner')
        self.assertEqual(result.ownership_type, 'system')
        
    def test_handle_mcp_request(self):
        # Create adapter
        adapter = MCPAdapter(self.config)
        
        # Test data
        mock_request = MagicMock()
        mock_request.type = 'test_request'
        mock_request.data = {'param': 'value'}
        
        # Call method
        result = adapter.handle_mcp_request(mock_request)
        
        # Verify
        self.assertEqual(result['status'], 'success')
        self.assertTrue('result' in result)
        self.assertTrue('timestamp' in result)
        
    def test_handle_mcp_request_error(self):
        # Create adapter
        adapter = MCPAdapter(self.config)
        
        # Test data - will cause an error because it's missing required attributes
        mock_request = object()
        
        # Call method
        result = adapter.handle_mcp_request(mock_request)
        
        # Verify
        self.assertEqual(result['status'], 'error')
        self.assertTrue('error' in result)
        self.assertTrue('timestamp' in result)
        
    @patch('importlib.import_module')
    def test_create_mcp_server(self, mock_import):
        # Setup mocks
        mock_mcp_sdk = MagicMock()
        mock_server_class = MagicMock()
        mock_tool_class = MagicMock()
        mock_resource_class = MagicMock()
        mock_mcp_sdk.Server = mock_server_class
        mock_mcp_sdk.Tool = mock_tool_class
        mock_mcp_sdk.Resource = mock_resource_class
        mock_import.return_value = mock_mcp_sdk
        
        # Create adapter
        adapter = MCPAdapter(self.config)
        adapter.mcp_server_class = mock_server_class
        adapter.mcp_tool_class = mock_tool_class
        adapter.mcp_resource_class = mock_resource_class
        
        # Mock register_mcp_tool and convert_to_mcp_resource
        adapter.register_mcp_tool = MagicMock(return_value=MagicMock())
        adapter.convert_to_mcp_resource = MagicMock(return_value=MagicMock())
        
        # Test data
        server_config = {
            'server_id': 'test-server-123',
            'name': 'Test Server',
            'host': 'localhost',
            'port': 8000,
            'tools': [{'tool_id': 'tool1'}],
            'resources': [{'resource_id': 'resource1'}],
            'owner_id': 'test-owner',
            'ownership_type': 'system'
        }
        
        # Call method
        result = adapter.create_mcp_server(server_config)
        
        # Verify
        mock_server_class.assert_called_once()
        self.assertEqual(result.original_server_id, 'test-server-123')
        self.assertEqual(result.owner_id, 'test-owner')
        self.assertEqual(result.ownership_type, 'system')
        
    def test_convert_from_mcp_result_string(self):
        # Create adapter
        adapter = MCPAdapter(self.config)
        
        # Test data
        mock_result = MagicMock()
        mock_result.data = "Task completed successfully"
        
        # Call method
        processed = adapter.convert_from_mcp_result(mock_result)
        
        # Verify
        self.assertEqual(processed['status'], 'completed')
        self.assertEqual(processed['result'], "Task completed successfully")
        self.assertTrue('timestamp' in processed)
        
    def test_convert_from_mcp_result_dict(self):
        # Create adapter
        adapter = MCPAdapter(self.config)
        
        # Test data
        mock_result = MagicMock()
        mock_result.data = json.dumps({
            'output': 'Task output',
            'metadata': {'key': 'value'}
        })
        
        # Call method
        processed = adapter.convert_from_mcp_result(mock_result)
        
        # Verify
        self.assertEqual(processed['status'], 'completed')
        self.assertEqual(processed['result']['output'], 'Task output')
        self.assertEqual(processed['result']['metadata'], {'key': 'value'})
        self.assertTrue('timestamp' in processed)
        
    def test_validate_ownership_compatibility_success(self):
        # Create adapter
        adapter = MCPAdapter(self.config)
        
        # Test data - same owner
        mock_tool1 = MagicMock()
        mock_tool1.owner_id = 'owner1'
        mock_tool1.exportable = True
        
        mock_tool2 = MagicMock()
        mock_tool2.owner_id = 'owner1'
        mock_tool2.exportable = True
        
        # Should not raise exception
        adapter._validate_ownership_compatibility([mock_tool1, mock_tool2])
        
        # Test data - different owners but exportable
        mock_tool3 = MagicMock()
        mock_tool3.owner_id = 'owner2'
        mock_tool3.exportable = True
        
        # Should not raise exception
        adapter._validate_ownership_compatibility([mock_tool1, mock_tool3])
        
    def test_validate_ownership_compatibility_failure(self):
        # Create adapter
        adapter = MCPAdapter(self.config)
        
        # Test data - different owners, one not exportable
        mock_tool1 = MagicMock()
        mock_tool1.owner_id = 'owner1'
        mock_tool1.exportable = False
        mock_tool1.name = 'Tool1'
        
        mock_tool2 = MagicMock()
        mock_tool2.owner_id = 'owner2'
        mock_tool2.exportable = True
        mock_tool2.name = 'Tool2'
        
        # Should raise exception
        with self.assertRaises(ValueError):
            adapter._validate_ownership_compatibility([mock_tool1, mock_tool2])
            
    def test_prepare_for_export(self):
        # Create adapter
        adapter = MCPAdapter(self.config)
        
        # Test data
        mock_tool = MagicMock()
        mock_tool.exportable = True
        mock_tool.original_tool_id = 'test-tool-123'
        mock_tool.name = 'Test Tool'
        mock_tool.description = 'A test tool'
        mock_tool.input_schema = '{"type": "object", "properties": {}}'
        mock_tool.output_schema = '{"type": "object", "properties": {}}'
        mock_tool.owner_id = 'test-owner'
        mock_tool.ownership_type = 'client'
        
        # Call method
        result = adapter.prepare_for_export(mock_tool)
        
        # Verify
        self.assertEqual(result['tool_id'], 'test-tool-123')
        self.assertEqual(result['name'], 'Test Tool')
        self.assertEqual(result['description'], 'A test tool')
        self.assertEqual(result['owner_id'], 'test-owner')
        self.assertEqual(result['ownership_type'], 'client')
        self.assertEqual(result['exportable'], True)
        self.assertEqual(result['framework'], 'mcp')
        self.assertTrue('exported_at' in result)
        
    def test_prepare_for_export_not_exportable(self):
        # Create adapter
        adapter = MCPAdapter(self.config)
        
        # Test data
        mock_tool = MagicMock()
        mock_tool.exportable = False
        
        # Should raise exception
        with self.assertRaises(ValueError):
            adapter.prepare_for_export(mock_tool)

if __name__ == '__main__':
    unittest.main()