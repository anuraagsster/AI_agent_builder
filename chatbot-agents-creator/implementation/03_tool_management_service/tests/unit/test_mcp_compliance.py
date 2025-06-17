"""
Tests for the MCP compliance layer.
"""

import unittest
from unittest.mock import MagicMock, patch
import json
import time
from datetime import datetime
from src.mcp_compliance import SecurityManager, AuditLogger, AccessController, MCPComplianceLayer


class TestSecurityManager(unittest.TestCase):
    def setUp(self):
        """Set up the security manager for testing."""
        self.config = {
            'encryption_key_file': None,  # Use in-memory key for testing
            'kms_key_id': 'test-key-id',
            'token_expiry': 3600
        }
        self.security = SecurityManager(self.config)
        
    def test_encrypt_decrypt_data(self):
        """Test data encryption and decryption."""
        # Test data
        data = {
            'sensitive': 'test_data',
            'nested': {
                'key': 'value'
            }
        }
        
        # Encrypt data
        encrypted = self.security.encrypt_data(data)
        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(encrypted, json.dumps(data))
        
        # Decrypt data
        decrypted = self.security.decrypt_data(encrypted)
        self.assertEqual(decrypted, data)
        
    @patch('boto3.client')
    def test_generate_token(self, mock_boto3):
        """Test token generation."""
        # Mock KMS response
        mock_kms = MagicMock()
        mock_kms.sign.return_value = {
            'Signature': b'test_signature'
        }
        mock_boto3.return_value = mock_kms
        
        # Generate token
        token = self.security.generate_token('test_user', {'read', 'write'})
        
        # Verify token
        self.assertIsInstance(token, str)
        mock_kms.sign.assert_called_once()
        
    @patch('boto3.client')
    def test_verify_token(self, mock_boto3):
        """Test token verification."""
        # Mock KMS response
        mock_kms = MagicMock()
        mock_kms.verify.return_value = {
            'SignatureValid': True,
            'Message': json.dumps({
                'user_id': 'test_user',
                'permissions': ['read', 'write'],
                'exp': int(time.time()) + 3600
            }).encode()
        }
        mock_boto3.return_value = mock_kms
        
        # Verify token
        payload = self.security.verify_token('test_token')
        
        # Verify payload
        self.assertEqual(payload['user_id'], 'test_user')
        self.assertEqual(set(payload['permissions']), {'read', 'write'})
        mock_kms.verify.assert_called_once()


class TestAuditLogger(unittest.TestCase):
    def setUp(self):
        """Set up the audit logger for testing."""
        self.config = {
            'audit_stream_name': 'test-stream'
        }
        self.audit = AuditLogger(self.config)
        
    @patch('boto3.client')
    def test_log_event(self, mock_boto3):
        """Test event logging."""
        # Mock AWS clients
        mock_cloudwatch = MagicMock()
        mock_firehose = MagicMock()
        mock_boto3.side_effect = [mock_cloudwatch, mock_firehose]
        
        # Log event
        self.audit.log_event(
            'test_event',
            'test_user',
            'test_action',
            'test_resource',
            {'test': 'details'}
        )
        
        # Verify CloudWatch call
        mock_cloudwatch.put_metric_data.assert_called_once()
        call_args = mock_cloudwatch.put_metric_data.call_args[1]
        self.assertEqual(call_args['Namespace'], 'ToolManagementService/Audit')
        self.assertEqual(call_args['MetricData'][0]['MetricName'], 'test_event')
        
        # Verify Firehose call
        mock_firehose.put_record.assert_called_once()
        call_args = mock_firehose.put_record.call_args[1]
        self.assertEqual(call_args['DeliveryStreamName'], 'test-stream')
        record_data = json.loads(call_args['Record']['Data'])
        self.assertEqual(record_data['event_type'], 'test_event')
        self.assertEqual(record_data['user_id'], 'test_user')


class TestAccessController(unittest.TestCase):
    def setUp(self):
        """Set up the access controller for testing."""
        self.config = {
            'permissions_table': 'test-permissions',
            'user_groups_table': 'test-user-groups',
            'group_permissions_table': 'test-group-permissions'
        }
        self.access = AccessController(self.config)
        
    @patch('boto3.resource')
    def test_check_permission(self, mock_boto3):
        """Test permission checking."""
        # Mock DynamoDB tables
        mock_table = MagicMock()
        mock_table.get_item.side_effect = [
            # User groups response
            {
                'Item': {
                    'user_id': 'test_user',
                    'groups': ['admin', 'user']
                }
            },
            # Group permissions response
            {
                'Item': {
                    'group': 'admin',
                    'permissions': ['read:resource', 'write:resource']
                }
            }
        ]
        mock_boto3.return_value.Table.return_value = mock_table
        
        # Check permission
        result = self.access.check_permission('test_user', 'read', 'resource')
        self.assertTrue(result)
        
        # Check denied permission
        result = self.access.check_permission('test_user', 'delete', 'resource')
        self.assertFalse(result)


class TestMCPComplianceLayer(unittest.TestCase):
    def setUp(self):
        """Set up the MCP compliance layer for testing."""
        self.config = {
            'security': {
                'encryption_key_file': None,
                'kms_key_id': 'test-key-id',
                'token_expiry': 3600
            },
            'audit': {
                'audit_stream_name': 'test-stream'
            },
            'access': {
                'permissions_table': 'test-permissions',
                'user_groups_table': 'test-user-groups',
                'group_permissions_table': 'test-group-permissions'
            }
        }
        self.compliance = MCPComplianceLayer(self.config)
        
    @patch('src.mcp_compliance.SecurityManager')
    @patch('src.mcp_compliance.AccessController')
    @patch('src.mcp_compliance.AuditLogger')
    def test_validate_request(self, mock_audit, mock_access, mock_security):
        """Test request validation."""
        # Mock security manager
        mock_security.return_value.verify_token.return_value = {
            'user_id': 'test_user',
            'permissions': ['read', 'write']
        }
        
        # Mock access controller
        mock_access.return_value.check_permission.return_value = True
        
        # Validate request
        result = self.compliance.validate_request('test_token', 'read', 'resource')
        self.assertTrue(result)
        
        # Verify calls
        mock_security.return_value.verify_token.assert_called_once_with('test_token')
        mock_access.return_value.check_permission.assert_called_once_with(
            'test_user', 'read', 'resource'
        )
        mock_audit.return_value.log_event.assert_called_once()
        
    def test_encrypt_decrypt_sensitive_data(self):
        """Test sensitive data encryption and decryption."""
        # Test data
        data = {
            'sensitive': 'test_data',
            'nested': {
                'key': 'value'
            }
        }
        
        # Encrypt data
        encrypted = self.compliance.encrypt_sensitive_data(data)
        self.assertIsInstance(encrypted, str)
        
        # Decrypt data
        decrypted = self.compliance.decrypt_sensitive_data(encrypted)
        self.assertEqual(decrypted, data)
        
    @patch('src.mcp_compliance.AuditLogger')
    def test_log_security_event(self, mock_audit):
        """Test security event logging."""
        # Log event
        self.compliance.log_security_event(
            'test_event',
            'test_user',
            'test_action',
            'test_resource',
            {'test': 'details'}
        )
        
        # Verify call
        mock_audit.return_value.log_event.assert_called_once_with(
            'test_event',
            'test_user',
            'test_action',
            'test_resource',
            {'test': 'details'}
        )


if __name__ == '__main__':
    unittest.main() 