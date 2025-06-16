"""
Unit tests for the Resource Monitor component
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import numpy as np
from botocore.exceptions import ClientError

from src.workload_management.resource_monitor import ResourceMonitor

class TestResourceMonitor(unittest.TestCase):
    """Test cases for ResourceMonitor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'use_aws': True,
            'aws_region': 'us-west-2'
        }
        self.monitor = ResourceMonitor(config=self.config)
        
    @patch('boto3.client')
    def test_register_resource(self, mock_boto3_client):
        """Test registering a resource"""
        # Mock AWS clients
        mock_cloudwatch = MagicMock()
        mock_autoscaling = MagicMock()
        mock_boto3_client.side_effect = [mock_cloudwatch, mock_autoscaling]
        
        # Register a resource
        self.monitor.register_resource(
            resource_id='test-resource',
            initial_capacity=100,
            warning_threshold=0.8,
            critical_threshold=0.95,
            client_id='test-client'
        )
        
        # Verify resource was registered
        self.assertIn('test-resource', self.monitor.resources)
        self.assertEqual(self.monitor.resources['test-resource']['capacity'], 100)
        self.assertEqual(self.monitor.resources['test-resource']['client_id'], 'test-client')
        
        # Verify client-specific tracking
        self.assertIn('test-client', self.monitor.client_resources)
        self.assertIn('test-resource', self.monitor.client_resources['test-client'])
        
    @patch('boto3.client')
    def test_update_resource_usage(self, mock_boto3_client):
        """Test updating resource usage"""
        # Mock AWS clients
        mock_cloudwatch = MagicMock()
        mock_autoscaling = MagicMock()
        mock_boto3_client.side_effect = [mock_cloudwatch, mock_autoscaling]
        
        # Register and update resource
        self.monitor.register_resource('test-resource', 100, client_id='test-client')
        self.monitor.update_resource_usage('test-resource', 80, client_id='test-client')
        
        # Verify usage was updated
        resource = self.monitor.resources['test-resource']
        self.assertEqual(resource['used'], 80)
        self.assertEqual(resource['utilization'], 0.8)
        self.assertEqual(resource['status'], 'warning')
        
        # Verify history was recorded
        self.assertEqual(len(resource['history']), 1)
        self.assertEqual(resource['history'][0][1], 80)
        
        # Verify client-specific history
        client_history = self.monitor.client_resources['test-client']['test-resource']
        self.assertEqual(len(client_history), 1)
        self.assertEqual(client_history[0][1], 80)
        
    @patch('boto3.client')
    def test_cloudwatch_metrics(self, mock_boto3_client):
        """Test CloudWatch metrics integration"""
        # Mock AWS clients
        mock_cloudwatch = MagicMock()
        mock_autoscaling = MagicMock()
        mock_boto3_client.side_effect = [mock_cloudwatch, mock_autoscaling]
        
        # Set up the monitor with mocked clients
        self.monitor.cloudwatch_client = mock_cloudwatch
        
        # Register and update resource
        self.monitor.register_resource('test-resource', 100, client_id='test-client')
        self.monitor.update_resource_usage('test-resource', 80, client_id='test-client')
        
        # Verify CloudWatch metrics were sent
        mock_cloudwatch.put_metric_data.assert_called_once()
        call_args = mock_cloudwatch.put_metric_data.call_args[1]
        self.assertEqual(call_args['Namespace'], 'AgentBuilder/Resources')
        self.assertEqual(len(call_args['MetricData']), 1)
        metric = call_args['MetricData'][0]
        self.assertEqual(metric['MetricName'], 'ResourceUtilization')
        self.assertEqual(metric['Value'], 0.8)
        self.assertEqual(metric['Unit'], 'Percent')
        
    @patch('boto3.client')
    def test_auto_scaling(self, mock_boto3_client):
        """Test auto-scaling functionality"""
        # Mock AWS clients
        mock_cloudwatch = MagicMock()
        mock_autoscaling = MagicMock()
        mock_boto3_client.side_effect = [mock_cloudwatch, mock_autoscaling]
        
        # Set up the monitor with mocked clients
        self.monitor.cloudwatch_client = mock_cloudwatch
        self.monitor.auto_scaling_client = mock_autoscaling
        
        # Mock auto scaling group response
        mock_autoscaling.describe_auto_scaling_groups.return_value = {
            'AutoScalingGroups': [{
                'AutoScalingGroupName': 'test-asg',
                'DesiredCapacity': 2,
                'MinSize': 1,
                'MaxSize': 5
            }]
        }
        
        # Register resource with auto scaling group
        self.monitor.register_resource('test-resource', 100)
        self.monitor.set_auto_scaling_group('test-resource', 'test-asg')
        
        # Test scale up
        self.monitor.update_resource_usage('test-resource', 95)  # Above critical threshold
        mock_autoscaling.set_desired_capacity.assert_called_with(
            AutoScalingGroupName='test-asg',
            DesiredCapacity=3
        )
        
        # Test scale down
        mock_autoscaling.reset_mock()
        self.monitor.update_resource_usage('test-resource', 30)  # Below warning threshold
        mock_autoscaling.set_desired_capacity.assert_called_with(
            AutoScalingGroupName='test-asg',
            DesiredCapacity=1
        )
        
    def test_resource_forecasting(self):
        """Test resource usage forecasting"""
        # Register resource
        self.monitor.register_resource('test-resource', 100)
        
        # Generate some historical data
        base_time = datetime.now()
        for i in range(24):
            usage = 50 + 20 * np.sin(i * np.pi / 12)  # Simulate daily pattern
            self.monitor.resources['test-resource']['history'].append(
                (base_time + timedelta(hours=i), usage)
            )
        
        # Get forecast
        forecast = self.monitor.get_resource_forecast('test-resource', hours_ahead=12)
        
        # Verify forecast structure
        self.assertIn('forecasts', forecast)
        self.assertIn('confidence_intervals', forecast)
        self.assertEqual(len(forecast['forecasts']), 12)
        self.assertEqual(len(forecast['confidence_intervals']), 12)
        
    @patch('boto3.client')
    def test_client_specific_monitoring(self, mock_boto3_client):
        """Test client-specific resource monitoring"""
        # Mock AWS clients
        mock_cloudwatch = MagicMock()
        mock_autoscaling = MagicMock()
        mock_boto3_client.side_effect = [mock_cloudwatch, mock_autoscaling]
        
        # Set up the monitor with mocked clients
        self.monitor.cloudwatch_client = mock_cloudwatch
        
        # Register resources for different clients
        self.monitor.register_resource('resource1', 100, client_id='client1')
        self.monitor.register_resource('resource2', 200, client_id='client2')
        
        # Update usage
        self.monitor.update_resource_usage('resource1', 80, client_id='client1')
        self.monitor.update_resource_usage('resource2', 150, client_id='client2')
        
        # Get client-specific usage
        client1_usage = self.monitor.get_client_resource_usage('client1')
        client2_usage = self.monitor.get_client_resource_usage('client2')
        
        # Verify client-specific data
        self.assertIn('resource1', client1_usage)
        self.assertNotIn('resource2', client1_usage)
        self.assertIn('resource2', client2_usage)
        self.assertNotIn('resource1', client2_usage)
        
        self.assertEqual(client1_usage['resource1'][0], 80)
        self.assertEqual(client2_usage['resource2'][0], 150)
        
    @patch('boto3.client')
    def test_error_handling(self, mock_boto3_client):
        """Test error handling in AWS operations"""
        # Mock AWS clients with errors
        mock_cloudwatch = MagicMock()
        mock_autoscaling = MagicMock()
        mock_boto3_client.side_effect = [mock_cloudwatch, mock_autoscaling]
        
        # Set up the monitor with mocked clients
        self.monitor.cloudwatch_client = mock_cloudwatch
        self.monitor.auto_scaling_client = mock_autoscaling
        
        # Simulate CloudWatch error
        mock_cloudwatch.put_metric_data.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDeniedException'}},
            operation_name='PutMetricData'
        )
        
        # Register and update resource
        self.monitor.register_resource('test-resource', 100)
        self.monitor.update_resource_usage('test-resource', 80)
        
        # Verify resource was still updated despite CloudWatch error
        self.assertEqual(self.monitor.resources['test-resource']['used'], 80)
        
        # Simulate Auto Scaling error
        mock_autoscaling.describe_auto_scaling_groups.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDeniedException'}},
            operation_name='DescribeAutoScalingGroups'
        )
        
        # Set auto scaling group and update usage
        self.monitor.set_auto_scaling_group('test-resource', 'test-asg')
        self.monitor.update_resource_usage('test-resource', 95)
        
        # Verify resource was still updated despite Auto Scaling error
        self.assertEqual(self.monitor.resources['test-resource']['used'], 95)

if __name__ == '__main__':
    unittest.main() 