import unittest
from unittest.mock import patch, MagicMock
import json
import time
from botocore.exceptions import ClientError

from src.workload_management.task_distributor import TaskDistributor

class TestTaskDistributor(unittest.TestCase):
    """Test cases for the TaskDistributor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'use_step_functions': False
        }
        self.task_distributor = TaskDistributor(self.config)
        
    def test_register_agent(self):
        """Test registering an agent"""
        self.task_distributor.register_agent('agent1', ['capability1', 'capability2'], 5)
        
        self.assertIn('agent1', self.task_distributor.agents)
        self.assertEqual(self.task_distributor.agents['agent1']['capabilities'], ['capability1', 'capability2'])
        self.assertEqual(self.task_distributor.agents['agent1']['capacity'], 5)
        
    def test_submit_task(self):
        """Test submitting a task"""
        self.task_distributor.submit_task('task1', 'test_type', ['capability1'], priority=1)
        
        self.assertIn('task1', self.task_distributor.tasks)
        self.assertEqual(self.task_distributor.tasks['task1']['type'], 'test_type')
        self.assertEqual(self.task_distributor.tasks['task1']['requirements'], ['capability1'])
        self.assertEqual(self.task_distributor.tasks['task1']['priority'], 1)
        self.assertEqual(self.task_distributor.tasks['task1']['status'], 'pending')
        
    def test_distribute_tasks(self):
        """Test distributing tasks to agents"""
        # Register agents
        self.task_distributor.register_agent('agent1', ['capability1'], 1)
        self.task_distributor.register_agent('agent2', ['capability2'], 1)
        
        # Submit tasks
        self.task_distributor.submit_task('task1', 'test_type', ['capability1'], priority=1)
        self.task_distributor.submit_task('task2', 'test_type', ['capability2'], priority=2)
        
        # Distribute tasks
        assignments = self.task_distributor.distribute_tasks()
        
        # Check assignments
        self.assertEqual(len(assignments), 2)
        self.assertEqual(assignments['task1'], 'agent1')
        self.assertEqual(assignments['task2'], 'agent2')
        
    def test_complete_task(self):
        """Test completing a task"""
        # Register agent
        self.task_distributor.register_agent('agent1', ['capability1'], 1)
        
        # Submit task
        self.task_distributor.submit_task('task1', 'test_type', ['capability1'])
        
        # Distribute tasks
        self.task_distributor.distribute_tasks()
        
        # Complete task
        self.task_distributor.complete_task('task1')
        
        # Check task status
        self.assertEqual(self.task_distributor.tasks['task1']['status'], 'completed')
        
    @patch('boto3.client')
    def test_aws_initialization(self, mock_boto3_client):
        """Test AWS client initialization"""
        # Mock boto3 clients
        mock_step_functions = MagicMock()
        mock_dynamodb = MagicMock()
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'stepfunctions': mock_step_functions,
            'dynamodb': mock_dynamodb
        }[service]
        
        # Mock DynamoDB describe_table to simulate table exists
        mock_dynamodb.describe_table.return_value = {'Table': {'TableName': 'agent_tasks'}}
        
        # Create TaskDistributor with AWS enabled
        config = {
            'use_step_functions': True,
            'aws_region': 'us-west-2',
            'dynamodb_table': 'agent_tasks'
        }
        task_distributor = TaskDistributor(config)
        
        # Check AWS clients were initialized
        self.assertIsNotNone(task_distributor.step_functions_client)
        self.assertIsNotNone(task_distributor.dynamodb_client)
        
        # Verify boto3.client was called with correct parameters
        mock_boto3_client.assert_any_call('stepfunctions', region_name='us-west-2')
        mock_boto3_client.assert_any_call('dynamodb', region_name='us-west-2')
        
    @patch('boto3.client')
    def test_create_dynamodb_table(self, mock_boto3_client):
        """Test DynamoDB table creation if it doesn't exist"""
        # Mock boto3 clients
        mock_step_functions = MagicMock()
        mock_dynamodb = MagicMock()
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'stepfunctions': mock_step_functions,
            'dynamodb': mock_dynamodb
        }[service]
        
        # Mock DynamoDB describe_table to simulate table doesn't exist
        resource_not_found = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
            'describe_table'
        )
        mock_dynamodb.describe_table.side_effect = resource_not_found
        
        # Create TaskDistributor with AWS enabled
        config = {
            'use_step_functions': True,
            'aws_region': 'us-west-2',
            'dynamodb_table': 'agent_tasks'
        }
        task_distributor = TaskDistributor(config)
        
        # Verify create_table was called
        mock_dynamodb.create_table.assert_called_once()
        
    @patch('boto3.client')
    def test_start_workflow(self, mock_boto3_client):
        """Test starting a Step Functions workflow"""
        # Mock boto3 clients
        mock_step_functions = MagicMock()
        mock_dynamodb = MagicMock()
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'stepfunctions': mock_step_functions,
            'dynamodb': mock_dynamodb
        }[service]
        
        # Mock DynamoDB describe_table to simulate table exists
        mock_dynamodb.describe_table.return_value = {'Table': {'TableName': 'agent_tasks'}}
        
        # Mock Step Functions start_execution
        mock_step_functions.start_execution.return_value = {
            'executionArn': 'arn:aws:states:us-west-2:123456789012:execution:test-workflow:execution-id'
        }
        
        # Create TaskDistributor with AWS enabled
        config = {
            'use_step_functions': True,
            'aws_region': 'us-west-2',
            'step_functions_role_arn': 'arn:aws:iam::123456789012:role/StepFunctionsRole'
        }
        task_distributor = TaskDistributor(config)
        
        # Start workflow with existing state machine ARN
        workflow_arn = 'arn:aws:states:us-west-2:123456789012:stateMachine:test-workflow'
        input_data = {'key': 'value'}
        execution_arn = task_distributor.start_workflow(workflow_arn, input_data)
        
        # Verify start_execution was called with correct parameters
        mock_step_functions.start_execution.assert_called_with(
            stateMachineArn=workflow_arn,
            input=json.dumps(input_data)
        )
        
        # Verify execution ARN is returned
        self.assertEqual(execution_arn, 'arn:aws:states:us-west-2:123456789012:execution:test-workflow:execution-id')
        
    @patch('boto3.client')
    def test_check_workflow_status(self, mock_boto3_client):
        """Test checking a Step Functions workflow status"""
        # Mock boto3 clients
        mock_step_functions = MagicMock()
        mock_dynamodb = MagicMock()
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'stepfunctions': mock_step_functions,
            'dynamodb': mock_dynamodb
        }[service]
        
        # Mock DynamoDB describe_table to simulate table exists
        mock_dynamodb.describe_table.return_value = {'Table': {'TableName': 'agent_tasks'}}
        
        # Mock Step Functions describe_execution
        execution_time = time.time()
        mock_step_functions.describe_execution.return_value = {
            'executionArn': 'arn:aws:states:us-west-2:123456789012:execution:test-workflow:execution-id',
            'stateMachineArn': 'arn:aws:states:us-west-2:123456789012:stateMachine:test-workflow',
            'status': 'SUCCEEDED',
            'startDate': execution_time,
            'stopDate': execution_time + 10,
            'output': '{"result": "success"}'
        }
        
        # Create TaskDistributor with AWS enabled
        config = {
            'use_step_functions': True,
            'aws_region': 'us-west-2'
        }
        task_distributor = TaskDistributor(config)
        
        # Check workflow status
        execution_arn = 'arn:aws:states:us-west-2:123456789012:execution:test-workflow:execution-id'
        status = task_distributor.check_workflow_status(execution_arn)
        
        # Verify describe_execution was called with correct parameters
        mock_step_functions.describe_execution.assert_called_with(
            executionArn=execution_arn
        )
        
        # Verify status is returned correctly
        self.assertEqual(status['status'], 'SUCCEEDED')
        self.assertEqual(status['output'], {'result': 'success'})
        
    @patch('boto3.client')
    def test_dynamodb_operations(self, mock_boto3_client):
        """Test DynamoDB operations"""
        # Mock boto3 clients
        mock_step_functions = MagicMock()
        mock_dynamodb = MagicMock()
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'stepfunctions': mock_step_functions,
            'dynamodb': mock_dynamodb
        }[service]
        
        # Mock DynamoDB describe_table to simulate table exists
        mock_dynamodb.describe_table.return_value = {'Table': {'TableName': 'agent_tasks'}}
        
        # Mock DynamoDB get_item
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'task_id': {'S': 'task1'},
                'data': {'S': '{"type": "test_type", "status": "completed"}'}
            }
        }
        
        # Create TaskDistributor with AWS enabled
        config = {
            'use_step_functions': True,
            'aws_region': 'us-west-2',
            'dynamodb_table': 'agent_tasks'
        }
        task_distributor = TaskDistributor(config)
        
        # Store task in DynamoDB
        task_data = {'type': 'test_type', 'status': 'pending'}
        result = task_distributor.store_task_in_dynamodb('task1', task_data)
        
        # Verify put_item was called with correct parameters
        mock_dynamodb.put_item.assert_called_with(
            TableName='agent_tasks',
            Item={
                'task_id': {'S': 'task1'},
                'data': {'S': json.dumps(task_data)}
            }
        )
        
        # Verify result is True
        self.assertTrue(result)
        
        # Get task from DynamoDB
        task = task_distributor.get_task_from_dynamodb('task1')
        
        # Verify get_item was called with correct parameters
        mock_dynamodb.get_item.assert_called_with(
            TableName='agent_tasks',
            Key={'task_id': {'S': 'task1'}}
        )
        
        # Verify task data is returned correctly
        self.assertEqual(task['type'], 'test_type')
        self.assertEqual(task['status'], 'completed')

if __name__ == '__main__':
    unittest.main()