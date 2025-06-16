"""
Unit tests for the AWS Parameter Store configuration source
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from botocore.exceptions import ClientError

from src.config_management.config_manager import ParameterStoreConfigSource

class TestParameterStoreConfigSource(unittest.TestCase):
    """Test cases for ParameterStoreConfigSource"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.path_prefix = '/test/config'
        self.region = 'us-west-2'
        self.kms_key_id = 'arn:aws:kms:us-west-2:123456789012:key/1234abcd-12ab-34cd-56ef-1234567890ab'
        self.config_source = ParameterStoreConfigSource(
            path_prefix=self.path_prefix,
            region=self.region,
            kms_key_id=self.kms_key_id
        )
        
    @patch('boto3.client')
    def test_load_parameters(self, mock_boto3_client):
        """Test loading parameters from Parameter Store"""
        # Mock SSM client response
        mock_ssm = MagicMock()
        mock_boto3_client.return_value = mock_ssm
        
        # Set up mock response
        mock_ssm.get_parameters_by_path.return_value = {
            'Parameters': [
                {
                    'Name': '/test/config/database/host',
                    'Value': 'localhost',
                    'Type': 'String',
                    'Version': 1,
                    'LastModifiedDate': datetime.now()
                },
                {
                    'Name': '/test/config/database/password',
                    'Value': 'secret123',
                    'Type': 'SecureString',
                    'Version': 2,
                    'LastModifiedDate': datetime.now()
                }
            ]
        }
        
        # Load configuration
        config = self.config_source.load()
        
        # Verify parameters were loaded correctly
        self.assertIn('database', config)
        self.assertIn('host', config['database'])
        self.assertIn('password', config['database'])
        
        # Verify parameter metadata
        self.assertEqual(config['database']['host']['value'], 'localhost')
        self.assertEqual(config['database']['host']['type'], 'String')
        self.assertEqual(config['database']['password']['value'], 'secret123')
        self.assertEqual(config['database']['password']['type'], 'SecureString')
        
    @patch('boto3.client')
    def test_save_parameters(self, mock_boto3_client):
        """Test saving parameters to Parameter Store"""
        # Mock SSM client
        mock_ssm = MagicMock()
        mock_boto3_client.return_value = mock_ssm
        
        # Test configuration
        config = {
            'database': {
                'host': {
                    'value': 'localhost',
                    'type': 'String'
                },
                'password': {
                    'value': 'secret123',
                    'type': 'SecureString',
                    'tags': {
                        'environment': 'test',
                        'application': 'agent-builder'
                    }
                }
            }
        }
        
        # Save configuration
        result = self.config_source.save(config)
        
        # Verify parameters were saved correctly
        self.assertTrue(result)
        mock_ssm.put_parameter.assert_called()
        
        # Verify KMS key was used for secure parameters
        calls = mock_ssm.put_parameter.call_args_list
        for call in calls:
            args = call[1]
            if 'password' in args['Name']:
                self.assertEqual(args['Type'], 'SecureString')
                self.assertEqual(args['KeyId'], self.kms_key_id)
                
    @patch('boto3.client')
    def test_parameter_history(self, mock_boto3_client):
        """Test retrieving parameter history"""
        # Mock SSM client
        mock_ssm = MagicMock()
        mock_boto3_client.return_value = mock_ssm
        
        # Set up mock response
        mock_ssm.get_parameter_history.return_value = {
            'Parameters': [
                {
                    'Name': '/test/config/api/key',
                    'Value': 'old-key',
                    'Type': 'SecureString',
                    'Version': 1,
                    'LastModifiedDate': datetime.now(),
                    'LastModifiedUser': 'user1'
                },
                {
                    'Name': '/test/config/api/key',
                    'Value': 'new-key',
                    'Type': 'SecureString',
                    'Version': 2,
                    'LastModifiedDate': datetime.now(),
                    'LastModifiedUser': 'user2'
                }
            ]
        }
        
        # Get parameter history
        history = self.config_source.get_parameter_history('api/key')
        
        # Verify history was retrieved correctly
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['value'], 'old-key')
        self.assertEqual(history[0]['version'], 1)
        self.assertEqual(history[1]['value'], 'new-key')
        self.assertEqual(history[1]['version'], 2)
        
    @patch('boto3.client')
    def test_parameter_by_version(self, mock_boto3_client):
        """Test retrieving specific parameter version"""
        # Mock SSM client
        mock_ssm = MagicMock()
        mock_boto3_client.return_value = mock_ssm
        
        # Set up mock response
        mock_ssm.get_parameter_history.return_value = {
            'Parameters': [
                {
                    'Name': '/test/config/api/key',
                    'Value': 'old-key',
                    'Type': 'SecureString',
                    'Version': 1,
                    'LastModifiedDate': datetime.now()
                },
                {
                    'Name': '/test/config/api/key',
                    'Value': 'new-key',
                    'Type': 'SecureString',
                    'Version': 2,
                    'LastModifiedDate': datetime.now()
                }
            ]
        }
        
        # Get specific version
        param = self.config_source.get_parameter_by_version('api/key', 1)
        
        # Verify correct version was retrieved
        self.assertIsNotNone(param)
        self.assertEqual(param['value'], 'old-key')
        self.assertEqual(param['version'], 1)
        
    @patch('boto3.client')
    def test_error_handling(self, mock_boto3_client):
        """Test error handling for AWS API calls"""
        # Mock SSM client
        mock_ssm = MagicMock()
        mock_boto3_client.return_value = mock_ssm
        
        # Test access denied error
        mock_ssm.get_parameters_by_path.side_effect = ClientError(
            error_response={
                'Error': {
                    'Code': 'AccessDeniedException',
                    'Message': 'Access Denied'
                }
            },
            operation_name='GetParametersByPath'
        )
        
        # Attempt to load configuration
        config = self.config_source.load()
        
        # Verify empty config is returned on error
        self.assertEqual(config, {})
        
    @patch('boto3.client')
    def test_throttling_handling(self, mock_boto3_client):
        """Test handling of AWS API throttling"""
        # Mock SSM client
        mock_ssm = MagicMock()
        mock_boto3_client.return_value = mock_ssm
        
        # Set up responses
        mock_ssm.get_parameters_by_path.side_effect = [
            # First call returns some parameters
            {
                'Parameters': [
                    {
                        'Name': '/test/config/param1',
                        'Value': 'value1',
                        'Type': 'String',
                        'Version': 1
                    }
                ],
                'NextToken': 'token1'
            },
            # Second call gets throttled
            ClientError(
                error_response={
                    'Error': {
                        'Code': 'ThrottlingException',
                        'Message': 'Rate exceeded'
                    }
                },
                operation_name='GetParametersByPath'
            )
        ]
        
        # Load configuration
        config = self.config_source.load()
        
        # Verify partial config is returned
        self.assertIn('param1', config)
        self.assertEqual(config['param1']['value'], 'value1')

if __name__ == '__main__':
    unittest.main() 