import json
import boto3
from botocore.exceptions import ClientError

class TaskDistributor:
    """
    Responsible for distributing tasks among available agents based on
    capabilities, current workload, and priorities.
    
    Supports both local task distribution and AWS Step Functions for complex workflows.
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.agents = {}
        self.tasks = {}
        self.task_queue = []
        self.use_step_functions = self.config.get('use_step_functions', False)
        self.step_functions_client = None
        self.dynamodb_client = None
        
        if self.use_step_functions:
            self._initialize_aws_clients()
        
    def register_agent(self, agent_id, capabilities, capacity):
        """
        Register an agent with the task distributor
        
        Args:
            agent_id: Unique identifier for the agent
            capabilities: List of capabilities the agent has
            capacity: Maximum number of concurrent tasks the agent can handle
        """
        self.agents[agent_id] = {
            'capabilities': capabilities,
            'capacity': capacity,
            'current_tasks': [],
            'utilization': 0.0
        }
        
    def submit_task(self, task_id, task_type, requirements, priority=0):
        """
        Submit a task to be distributed
        
        Args:
            task_id: Unique identifier for the task
            task_type: Type of task
            requirements: Required capabilities to perform the task
            priority: Task priority (higher number = higher priority)
        """
        self.tasks[task_id] = {
            'type': task_type,
            'requirements': requirements,
            'priority': priority,
            'status': 'pending',
            'assigned_to': None
        }
        self._add_to_queue(task_id)
        
    def _add_to_queue(self, task_id):
        """Add a task to the priority queue"""
        # In a real implementation, this would use a proper priority queue
        self.task_queue.append(task_id)
        self.task_queue.sort(key=lambda tid: self.tasks[tid]['priority'], reverse=True)
        
    def distribute_tasks(self):
        """
        Distribute pending tasks to available agents
        
        Returns:
            Dictionary mapping task_ids to agent_ids
        """
        assignments = {}
        
        for task_id in self.task_queue[:]:
            task = self.tasks[task_id]
            
            # Find the best agent for this task
            best_agent = self._find_best_agent(task)
            
            if best_agent:
                # Assign the task
                task['assigned_to'] = best_agent
                task['status'] = 'assigned'
                self.agents[best_agent]['current_tasks'].append(task_id)
                self.agents[best_agent]['utilization'] += 1.0 / self.agents[best_agent]['capacity']
                
                # Remove from queue
                self.task_queue.remove(task_id)
                
                # Record the assignment
                assignments[task_id] = best_agent
                
        return assignments
        
    def _find_best_agent(self, task):
        """Find the best agent for a given task"""
        eligible_agents = []
        
        for agent_id, agent in self.agents.items():
            # Check if agent has all required capabilities
            if all(cap in agent['capabilities'] for cap in task['requirements']):
                # Check if agent has capacity
                if len(agent['current_tasks']) < agent['capacity']:
                    eligible_agents.append(agent_id)
        
        if not eligible_agents:
            return None
            
        # Find the agent with the lowest utilization
        return min(eligible_agents, key=lambda aid: self.agents[aid]['utilization'])
        
    def complete_task(self, task_id):
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
                # Create table
                self.dynamodb_client.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'task_id', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'task_id', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                # Wait for table to be created
                waiter = self.dynamodb_client.get_waiter('table_exists')
                waiter.wait(TableName=table_name)
    
    def start_workflow(self, workflow_definition, input_data=None):
        """
        Start a Step Functions workflow for complex task orchestration
        
        Args:
            workflow_definition: ARN of the Step Functions state machine or the state machine definition
            input_data: Optional input data for the workflow
            
        Returns:
            Execution ARN if successful, None otherwise
        """
        if not self.use_step_functions or not self.step_functions_client:
            print("AWS Step Functions not configured")
            return None
            
        try:
            # Check if workflow_definition is an ARN or a state machine definition
            if workflow_definition.startswith('arn:'):
                # Use existing state machine
                state_machine_arn = workflow_definition
            else:
                # Create new state machine
                response = self.step_functions_client.create_state_machine(
                    name=f"AgentWorkflow-{int(time.time())}",
                    definition=workflow_definition,
                    roleArn=self.config.get('step_functions_role_arn'),
                    type='STANDARD'
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
    
    def check_workflow_status(self, execution_arn):
        """
        Check the status of a Step Functions workflow
        
        Args:
            execution_arn: The execution ARN returned by start_workflow
            
        Returns:
            Status of the workflow execution
        """
        if not self.use_step_functions or not self.step_functions_client:
            return None
            
        try:
            response = self.step_functions_client.describe_execution(
                executionArn=execution_arn
            )
            
            return {
                'status': response['status'],
                'start_date': response['startDate'],
                'stop_date': response.get('stopDate'),
                'output': json.loads(response.get('output', '{}')) if 'output' in response else None
            }
            
        except Exception as e:
            print(f"Error checking workflow status: {str(e)}")
            return None
    
    def store_task_in_dynamodb(self, task_id, task_data):
        """
        Store task data in DynamoDB
        
        Args:
            task_id: Unique identifier for the task
            task_data: Task data to store
            
        Returns:
            True if successful, False otherwise
        """
        if not self.use_step_functions or not self.dynamodb_client:
            return False
            
        try:
            table_name = self.config.get('dynamodb_table', 'agent_tasks')
            
            # Convert task data to DynamoDB format
            item = {
                'task_id': {'S': task_id},
                'data': {'S': json.dumps(task_data)}
            }
            
            self.dynamodb_client.put_item(
                TableName=table_name,
                Item=item
            )
            
            return True
            
        except Exception as e:
            print(f"Error storing task in DynamoDB: {str(e)}")
            return False
    
    def get_task_from_dynamodb(self, task_id):
        """
        Retrieve task data from DynamoDB
        
        Args:
            task_id: Unique identifier for the task
            
        Returns:
            Task data if found, None otherwise
        """
        if not self.use_step_functions or not self.dynamodb_client:
            return None
            
        try:
            table_name = self.config.get('dynamodb_table', 'agent_tasks')
            
            response = self.dynamodb_client.get_item(
                TableName=table_name,
                Key={'task_id': {'S': task_id}}
            )
            
            if 'Item' in response:
                return json.loads(response['Item']['data']['S'])
            else:
                return None
                
        except Exception as e:
            print(f"Error retrieving task from DynamoDB: {str(e)}")
            return None