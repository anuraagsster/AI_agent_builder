class TaskDistributor:
    """
    Responsible for distributing tasks among available agents based on
    capabilities, current workload, and priorities.
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.agents = {}
        self.tasks = {}
        self.task_queue = []
        
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