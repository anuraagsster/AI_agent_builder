import unittest
from unittest.mock import patch, MagicMock
import json
import time
from botocore.exceptions import ClientError
import boto3

from src.workload_management.task_distributor import TaskDistributor

class TestTaskDistributor(unittest.TestCase):
    """Test cases for the TaskDistributor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'use_step_functions': True,
            'aws_region': 'us-east-1',
            'dynamodb_table': 'test_agent_tasks'
        }
        self.distributor = TaskDistributor(self.config)
        
        # Mock AWS clients
        self.distributor.step_functions_client = MagicMock()
        self.distributor.dynamodb_client = MagicMock()
        
    def test_register_agent(self):
        """Test registering an agent"""
        self.distributor.register_agent('agent1', ['capability1', 'capability2'], 5)
        
        self.assertIn('agent1', self.distributor.agents)
        self.assertEqual(self.distributor.agents['agent1']['capabilities'], ['capability1', 'capability2'])
        self.assertEqual(self.distributor.agents['agent1']['capacity'], 5)
        
    def test_submit_task(self):
        """Test submitting a task"""
        self.distributor.submit_task('task1', 'test_type', ['capability1'], priority=1)
        
        self.assertIn('task1', self.distributor.tasks)
        self.assertEqual(self.distributor.tasks['task1']['type'], 'test_type')
        self.assertEqual(self.distributor.tasks['task1']['requirements'], ['capability1'])
        self.assertEqual(self.distributor.tasks['task1']['priority'], 1)
        self.assertEqual(self.distributor.tasks['task1']['status'], 'pending')
        
    def test_distribute_tasks(self):
        """Test distributing tasks to agents"""
        # Register agents
        self.distributor.register_agent('agent1', ['capability1'], 1)
        self.distributor.register_agent('agent2', ['capability2'], 1)
        
        # Submit tasks
        self.distributor.submit_task('task1', 'test_type', ['capability1'], priority=1)
        self.distributor.submit_task('task2', 'test_type', ['capability2'], priority=2)
        
        # Distribute tasks
        assignments = self.distributor.distribute_tasks()
        
        # Check assignments
        self.assertEqual(len(assignments), 2)
        self.assertEqual(assignments['task1'], 'agent1')
        self.assertEqual(assignments['task2'], 'agent2')
        
        # Check task status
        self.assertEqual(self.distributor.tasks['task1']['status'], 'assigned')
        self.assertEqual(self.distributor.tasks['task2']['status'], 'assigned')
        
    def test_complete_task(self):
        """Test completing a task"""
        # Register agent
        self.distributor.register_agent('agent1', ['capability1'], 1)
        
        # Submit task
        self.distributor.submit_task('task1', 'test_type', ['capability1'])
        
        # Distribute tasks
        self.distributor.distribute_tasks()
        
        # Complete task
        self.distributor.complete_task('task1')
        
        # Check task status
        self.assertEqual(self.distributor.tasks['task1']['status'], 'completed')
        
        # Check agent utilization
        self.assertEqual(self.distributor.agents['agent1']['utilization'], 0.0)
        
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
    def test_dynamodb_operations(self, mock_boto3_client):
        """Test DynamoDB operations"""
        mock_dynamodb = MagicMock()
        mock_boto3_client.return_value = mock_dynamodb
        distributor = TaskDistributor({'use_step_functions': True, 'aws_region': 'us-east-1'})
        distributor.dynamodb_client = mock_dynamodb
        # Store task
        distributor.store_task_in_dynamodb('task1', {'type': 'test_type', 'status': 'pending'})
        # Check call
        mock_dynamodb.put_item.assert_called_with(
            TableName='agent_tasks',
            Item={'task_id': {'S': 'task1'}, 'type': {'S': 'test_type'}, 'status': {'S': 'pending'}}
        )

    def test_register_agent_with_client(self):
        """Test registering an agent with a client ID"""
        # Register agent with client ID
        self.distributor.register_agent('agent1', ['cap1', 'cap2'], 2, 'client1')
        
        # Verify agent registration
        self.assertIn('agent1', self.distributor.agents)
        self.assertEqual(self.distributor.agents['agent1']['client_id'], 'client1')
        
        # Verify client-agent mapping
        self.assertIn('client1', self.distributor.client_agents)
        self.assertIn('agent1', self.distributor.client_agents['client1'])
        
    def test_submit_task_with_client(self):
        """Test submitting a task with a client ID"""
        # Submit task with client ID
        self.distributor.submit_task('task1', 'type1', ['cap1'], 1, 'client1')
        
        # Verify task submission
        self.assertIn('task1', self.distributor.tasks)
        self.assertEqual(self.distributor.tasks['task1']['client_id'], 'client1')
        
        # Verify task queue
        self.assertIn('client1', self.distributor.client_queues)
        self.assertIn('task1', self.distributor.client_queues['client1'])
        
    def test_distribute_tasks_with_client_isolation(self):
        """Test task distribution with client isolation"""
        # Register agents for different clients
        self.distributor.register_agent('agent1', ['cap1'], 2, 'client1')
        self.distributor.register_agent('agent2', ['cap1'], 2, 'client2')
        
        # Submit tasks for different clients
        self.distributor.submit_task('task1', 'type1', ['cap1'], 1, 'client1')
        self.distributor.submit_task('task2', 'type1', ['cap1'], 1, 'client2')
        
        # Distribute tasks
        assignments = self.distributor.distribute_tasks()
        
        # Verify task assignments
        self.assertEqual(assignments['task1'], 'agent1')
        self.assertEqual(assignments['task2'], 'agent2')
        
        # Verify task status
        self.assertEqual(self.distributor.tasks['task1']['status'], 'assigned')
        self.assertEqual(self.distributor.tasks['task2']['status'], 'assigned')
        
    def test_client_specific_task_distribution(self):
        """Test distributing tasks for a specific client"""
        # Register agents for different clients
        self.distributor.register_agent('agent1', ['cap1'], 2, 'client1')
        self.distributor.register_agent('agent2', ['cap1'], 2, 'client2')
        
        # Submit tasks for different clients
        self.distributor.submit_task('task1', 'type1', ['cap1'], 1, 'client1')
        self.distributor.submit_task('task2', 'type1', ['cap1'], 1, 'client2')
        
        # Distribute tasks for client1 only
        assignments = self.distributor.distribute_tasks('client1')
        
        # Verify only client1's task was assigned
        self.assertEqual(assignments['task1'], 'agent1')
        self.assertNotIn('task2', assignments)
        
        # Verify task status
        self.assertEqual(self.distributor.tasks['task1']['status'], 'assigned')
        self.assertEqual(self.distributor.tasks['task2']['status'], 'pending')
        
    def test_store_task_in_dynamodb_with_client(self):
        """Test storing task data in DynamoDB with client ID"""
        task_data = {
            'type': 'type1',
            'requirements': ['cap1', 'cap2'],
            'priority': 1,
            'client_id': 'client1'
        }
        
        # Store task
        self.distributor.store_task_in_dynamodb('task1', task_data)
        
        # Verify DynamoDB put_item was called with correct data
        self.distributor.dynamodb_client.put_item.assert_called_once()
        call_args = self.distributor.dynamodb_client.put_item.call_args[1]
        
        # Verify table name
        self.assertEqual(call_args['TableName'], 'test_agent_tasks')
        
        # Verify item structure
        item = call_args['Item']
        self.assertEqual(item['task_id']['S'], 'task1')
        self.assertEqual(item['client_id']['S'], 'client1')
        self.assertEqual(item['type']['S'], 'type1')
        self.assertEqual(item['priority']['N'], '1')
        self.assertEqual(item['requirements']['L'][0]['S'], 'cap1')
        self.assertEqual(item['requirements']['L'][1]['S'], 'cap2')
        
    def test_get_client_tasks(self):
        """Test retrieving tasks for a specific client"""
        # Mock DynamoDB query response
        mock_response = {
            'Items': [
                {
                    'task_id': {'S': 'task1'},
                    'client_id': {'S': 'client1'},
                    'type': {'S': 'type1'},
                    'requirements': {'L': [{'S': 'cap1'}]},
                    'priority': {'N': '1'}
                }
            ]
        }
        self.distributor.dynamodb_client.query.return_value = mock_response
        
        # Get client tasks
        tasks = self.distributor.get_client_tasks('client1')
        
        # Verify DynamoDB query was called correctly
        self.distributor.dynamodb_client.query.assert_called_once_with(
            TableName='test_agent_tasks',
            IndexName='ClientIdIndex',
            KeyConditionExpression='client_id = :cid',
            ExpressionAttributeValues={':cid': {'S': 'client1'}}
        )
        
        # Verify returned tasks
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['task_id'], 'task1')
        self.assertEqual(tasks[0]['client_id'], 'client1')
        
    def test_start_workflow_with_client(self):
        """Test starting a workflow with client ID"""
        workflow_def = '{"StartAt": "State1", "States": {"State1": {"Type": "Pass", "End": true}}}'
        input_data = {'key': 'value'}
        
        # Mock Step Functions response
        mock_response = {
            'stateMachineArn': 'arn:aws:states:us-east-1:123456789012:stateMachine:test',
            'executionArn': 'arn:aws:states:us-east-1:123456789012:execution:test:test'
        }
        self.distributor.step_functions_client.create_state_machine.return_value = mock_response
        self.distributor.step_functions_client.start_execution.return_value = {'executionArn': mock_response['executionArn']}
        
        # Start workflow with client ID
        execution_arn = self.distributor.start_workflow(workflow_def, input_data, 'client1')
        
        # Verify Step Functions calls
        self.distributor.step_functions_client.create_state_machine.assert_called_once()
        create_args = self.distributor.step_functions_client.create_state_machine.call_args[1]
        
        # Verify state machine name includes client ID
        self.assertTrue(create_args['name'].startswith('client1-'))
        
        # Verify tags include client ID
        self.assertEqual(create_args['tags'], [{'Key': 'ClientId', 'Value': 'client1'}])
        
        # Verify execution ARN
        self.assertEqual(execution_arn, mock_response['executionArn'])
        
    def test_error_handling(self):
        """Test error handling in client-specific operations"""
        # Test DynamoDB error
        self.distributor.dynamodb_client.query.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}},
            'Query'
        )
        
        # Verify get_client_tasks handles error gracefully
        tasks = self.distributor.get_client_tasks('client1')
        self.assertEqual(tasks, [])
        
        # Test Step Functions error
        self.distributor.step_functions_client.create_state_machine.side_effect = ClientError(
            {'Error': {'Code': 'AccessDeniedException'}},
            'CreateStateMachine'
        )
        
        # Verify start_workflow handles error gracefully
        execution_arn = self.distributor.start_workflow('{}', {}, 'client1')
        self.assertIsNone(execution_arn)

    def test_dict_to_dynamodb_list_of_primitives(self):
        # Test that a list of primitives is converted to DynamoDB format correctly
        data = {'mylist': ['a', 'b', 'c']}
        result = self.distributor._dict_to_dynamodb(data)
        self.assertIn('mylist', result)
        self.assertEqual(result['mylist']['L'][0]['S'], 'a')
        self.assertEqual(result['mylist']['L'][1]['S'], 'b')
        self.assertEqual(result['mylist']['L'][2]['S'], 'c')

if __name__ == '__main__':
    unittest.main()