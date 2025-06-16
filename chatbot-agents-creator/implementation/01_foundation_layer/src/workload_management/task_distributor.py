import json
import boto3
import time
from botocore.exceptions import ClientError
from typing import Dict, List, Any, Optional

class TaskDistributor:
    """
    Responsible for distributing tasks among available agents based on
    capabilities, current workload, and priorities.
    
    Supports both local task distribution and AWS Step Functions for complex workflows.
    Implements client-specific task isolation to ensure tasks from different clients
    are properly segregated.
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.agents = {}  # agent_id -> agent_info
        self.tasks = {}  # task_id -> task_info
        self.client_queues = {}  # client_id -> list of task_ids
        self.client_agents = {}  # client_id -> set of agent_ids
        self.use_step_functions = self.config.get('use_step_functions', False)
        self.step_functions_client = None
        self.dynamodb_client = None
        
        if self.use_step_functions:
            self._initialize_aws_clients()
        
    def register_agent(self, agent_id: str, capabilities: List[str], capacity: int, client_id: Optional[str] = None):
        """
        Register an agent with the task distributor
        
        Args:
            agent_id: Unique identifier for the agent
            capabilities: List of capabilities the agent has
            capacity: Maximum number of concurrent tasks the agent can handle
            client_id: Optional client ID for client-specific agents
        """
        self.agents[agent_id] = {
            'capabilities': capabilities,
            'capacity': capacity,
            'current_tasks': [],
            'utilization': 0.0,
            'client_id': client_id
        }
        
        # Track client-specific agents
        if client_id:
            if client_id not in self.client_agents:
                self.client_agents[client_id] = set()
            self.client_agents[client_id].add(agent_id)
        
    def submit_task(self, task_id: str, task_type: str, requirements: List[str], priority: int = 0, client_id: Optional[str] = None):
        """
        Submit a task to be distributed
        
        Args:
            task_id: Unique identifier for the task
            task_type: Type of task
            requirements: Required capabilities to perform the task
            priority: Task priority (higher number = higher priority)
            client_id: Optional client ID for client-specific tasks
        """
        self.tasks[task_id] = {
            'type': task_type,
            'requirements': requirements,
            'priority': priority,
            'status': 'pending',
            'assigned_to': None,
            'client_id': client_id
        }
        self._add_to_queue(task_id, client_id)
        
    def _add_to_queue(self, task_id: str, client_id: Optional[str] = None):
        """Add a task to the appropriate priority queue"""
        if client_id:
            # Add to client-specific queue
            if client_id not in self.client_queues:
                self.client_queues[client_id] = []
            self.client_queues[client_id].append(task_id)
            self.client_queues[client_id].sort(key=lambda tid: self.tasks[tid]['priority'], reverse=True)
        else:
            # Add to global queue
            if 'global' not in self.client_queues:
                self.client_queues['global'] = []
            self.client_queues['global'].append(task_id)
            self.client_queues['global'].sort(key=lambda tid: self.tasks[tid]['priority'], reverse=True)
        
    def distribute_tasks(self, client_id: Optional[str] = None):
        """
        Distribute pending tasks to available agents
        
        Args:
            client_id: Optional client ID to distribute tasks for a specific client
            
        Returns:
            Dictionary mapping task_ids to agent_ids
        """
        assignments = {}
        # Determine which queues to process
        queues_to_process = []
        if client_id:
            if client_id in self.client_queues:
                queues_to_process.append((client_id, self.client_queues[client_id]))
        else:
            # Process all queues, including 'global'
            for cid, queue in self.client_queues.items():
                queues_to_process.append((cid, queue))
        for queue_client_id, task_queue in queues_to_process:
            for task_id in task_queue[:]:  # Copy list to allow modification during iteration
                task = self.tasks[task_id]
                # For global queue, pass None as client_id to _find_best_agent
                best_agent = self._find_best_agent(task, None if queue_client_id == 'global' else queue_client_id)
                if best_agent:
                    task['assigned_to'] = best_agent
                    task['status'] = 'assigned'
                    self.agents[best_agent]['current_tasks'].append(task_id)
                    self.agents[best_agent]['utilization'] += 1.0 / self.agents[best_agent]['capacity']
                    task_queue.remove(task_id)
                    assignments[task_id] = best_agent
        return assignments
        
    def _find_best_agent(self, task: Dict[str, Any], client_id: Optional[str] = None) -> Optional[str]:
        """Find the best agent for a given task"""
        eligible_agents = []
        task_client_id = task.get('client_id')
        # Determine which agents to consider
        agents_to_check = []
        if task_client_id:
            # Task is client-specific, only consider client's agents
            if task_client_id in self.client_agents:
                agents_to_check = list(self.client_agents[task_client_id])
        elif client_id:
            # Looking for client-specific tasks, only consider client's agents
            if client_id in self.client_agents:
                agents_to_check = list(self.client_agents[client_id])
        else:
            # Global task, consider all agents
            agents_to_check = list(self.agents.keys())
        for agent_id in agents_to_check:
            agent = self.agents[agent_id]
            if all(cap in agent['capabilities'] for cap in task['requirements']):
                if len(agent['current_tasks']) < agent['capacity']:
                    eligible_agents.append(agent_id)
        if not eligible_agents:
            return None
        return min(eligible_agents, key=lambda aid: self.agents[aid]['utilization'])
        
    def complete_task(self, task_id: str):
        """
        Mark a task as completed and update agent utilization
        
        Args:
            task_id: ID of the completed task
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task['assigned_to']:
                agent_id = task['assigned_to']
                self.agents[agent_id]['current_tasks'].remove(task_id)
                self.agents[agent_id]['utilization'] -= 1.0 / self.agents[agent_id]['capacity']
                task['status'] = 'completed'
                
    def _initialize_aws_clients(self):
        """Initialize AWS clients for Step Functions and DynamoDB"""
        try:
            # Initialize AWS clients with optional custom endpoint for local testing
            endpoint_url = self.config.get('aws_endpoint_url')
            region = self.config.get('aws_region', 'us-east-1')
            
            kwargs = {'region_name': region}
            if endpoint_url:
                kwargs['endpoint_url'] = endpoint_url
                
            self.step_functions_client = boto3.client('stepfunctions', **kwargs)
            self.dynamodb_client = boto3.client('dynamodb', **kwargs)
            
            # Create DynamoDB table if it doesn't exist
            self._ensure_task_table_exists()
            
        except Exception as e:
            print(f"Error initializing AWS clients: {str(e)}")
            # Fall back to local task distribution
            self.use_step_functions = False
    
    def _ensure_task_table_exists(self):
        """Ensure the DynamoDB tasks table exists"""
        table_name = self.config.get('dynamodb_table', 'agent_tasks')
        
        try:
            # Check if table exists
            self.dynamodb_client.describe_table(TableName=table_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create table with client_id as a GSI
                self.dynamodb_client.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'task_id', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'task_id', 'AttributeType': 'S'},
                        {'AttributeName': 'client_id', 'AttributeType': 'S'}
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'ClientIdIndex',
                            'KeySchema': [
                                {'AttributeName': 'client_id', 'KeyType': 'HASH'}
                            ],
                            'Projection': {
                                'ProjectionType': 'ALL'
                            },
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            }
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                # Wait for table to be created
                waiter = self.dynamodb_client.get_waiter('table_exists')
                waiter.wait(TableName=table_name)
    
    def start_workflow(self, workflow_definition: str, input_data: Optional[Dict[str, Any]] = None, client_id: Optional[str] = None):
        """
        Start a Step Functions workflow for complex task orchestration
        
        Args:
            workflow_definition: ARN of the Step Functions state machine or the state machine definition
            input_data: Optional input data for the workflow
            client_id: Optional client ID for client-specific workflow
            
        Returns:
            Execution ARN if successful, None otherwise
        """
        if not self.use_step_functions or not self.step_functions_client:
            print("AWS Step Functions not configured")
            return None
            
        try:
            # Add client_id to input data if provided
            if client_id and input_data:
                input_data['client_id'] = client_id
            
            # Check if workflow_definition is an ARN or a state machine definition
            if workflow_definition.startswith('arn:'):
                # Use existing state machine
                state_machine_arn = workflow_definition
            else:
                # Create new state machine with client-specific name if provided
                name = f"AgentWorkflow-{int(time.time())}"
                if client_id:
                    name = f"{client_id}-{name}"
                
                response = self.step_functions_client.create_state_machine(
                    name=name,
                    definition=workflow_definition,
                    roleArn=self.config.get('step_functions_role_arn'),
                    type='STANDARD',
                    tags=[{'Key': 'ClientId', 'Value': client_id}] if client_id else []
                )
                state_machine_arn = response['stateMachineArn']
            
            # Start execution
            response = self.step_functions_client.start_execution(
                stateMachineArn=state_machine_arn,
                input=json.dumps(input_data or {})
            )
            
            return response['executionArn']
            
        except Exception as e:
            print(f"Error starting Step Functions workflow: {str(e)}")
            return None
    
    def store_task_in_dynamodb(self, task_id: str, task_data: Dict[str, Any]):
        """
        Store task data in DynamoDB
        
        Args:
            task_id: Unique identifier for the task
            task_data: Task data to store
        """
        if not self.dynamodb_client:
            return
        table_name = self.config.get('dynamodb_table', 'agent_tasks')
        # Use _dict_to_dynamodb for all fields except task_id
        item = {'task_id': {'S': task_id}}
        item.update(self._dict_to_dynamodb(task_data))
        try:
            self.dynamodb_client.put_item(
                TableName=table_name,
                Item=item
            )
        except Exception as e:
            print(f"Error storing task in DynamoDB: {str(e)}")
    
    def get_task_from_dynamodb(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve task data from DynamoDB
        
        Args:
            task_id: Unique identifier for the task
            
        Returns:
            Task data if found, None otherwise
        """
        if not self.dynamodb_client:
            return None
            
        table_name = self.config.get('dynamodb_table', 'agent_tasks')
        
        try:
            response = self.dynamodb_client.get_item(
                TableName=table_name,
                Key={'task_id': {'S': task_id}}
            )
            
            if 'Item' in response:
                return self._dynamodb_to_dict(response['Item'])
            return None
            
        except Exception as e:
            print(f"Error retrieving task from DynamoDB: {str(e)}")
            return None
    
    def get_client_tasks(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Get all tasks for a specific client
        
        Args:
            client_id: Client ID to get tasks for
            
        Returns:
            List of task data
        """
        if not self.dynamodb_client:
            return []
            
        table_name = self.config.get('dynamodb_table', 'agent_tasks')
        
        try:
            response = self.dynamodb_client.query(
                TableName=table_name,
                IndexName='ClientIdIndex',
                KeyConditionExpression='client_id = :cid',
                ExpressionAttributeValues={
                    ':cid': {'S': client_id}
                }
            )
            
            return [self._dynamodb_to_dict(item) for item in response.get('Items', [])]
            
        except Exception as e:
            print(f"Error querying client tasks from DynamoDB: {str(e)}")
            return []
    
    def _dict_to_dynamodb(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Python dictionary to DynamoDB format"""
        result = {}
        for k, v in data.items():
            if isinstance(v, str):
                result[k] = {'S': v}
            elif isinstance(v, (int, float)):
                result[k] = {'N': str(v)}
            elif isinstance(v, bool):
                result[k] = {'BOOL': v}
            elif isinstance(v, dict):
                result[k] = {'M': self._dict_to_dynamodb(v)}
            elif isinstance(v, list):
                # Handle lists of primitives and dicts
                dynamo_list = []
                for item in v:
                    if isinstance(item, str):
                        dynamo_list.append({'S': item})
                    elif isinstance(item, (int, float)):
                        dynamo_list.append({'N': str(item)})
                    elif isinstance(item, bool):
                        dynamo_list.append({'BOOL': item})
                    elif isinstance(item, dict):
                        dynamo_list.append({'M': self._dict_to_dynamodb(item)})
                    else:
                        dynamo_list.append({'S': str(item)})
                result[k] = {'L': dynamo_list}
            else:
                result[k] = {'S': str(v)}
        return result
    
    def _dynamodb_to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DynamoDB format to Python dictionary"""
        result = {}
        for k, v in data.items():
            if 'S' in v:
                result[k] = v['S']
            elif 'N' in v:
                result[k] = float(v['N'])
            elif 'BOOL' in v:
                result[k] = v['BOOL']
            elif 'M' in v:
                result[k] = self._dynamodb_to_dict(v['M'])
            elif 'L' in v:
                result[k] = [self._dynamodb_to_dict({'item': item})['item'] for item in v['L']]
        return result