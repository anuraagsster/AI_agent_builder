"""
Base Agent Component

This module provides the base agent class that all agents in the system inherit from.
It defines the core functionality and interfaces that all agents must implement.
"""

import logging
import time
import uuid
import json
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime

class BaseAgent:
    """
    Base class for all agents in the system.
    
    Provides core functionality for agent state management, task execution,
    capability registration, and metrics collection.
    """
    
    def __init__(self, config: Dict[str, Any], agent_id: Optional[str] = None):
        """
        Initialize a new agent
        
        Args:
            config: Configuration dictionary for the agent
            agent_id: Optional unique identifier for the agent (generated if not provided)
        """
        self.config = config
        self.agent_id = agent_id or str(uuid.uuid4())
        self.state = {
            'status': 'created',
            'capabilities': {},
            'metrics': {
                'tasks_completed': 0,
                'tasks_failed': 0,
                'avg_task_duration': 0,
                'last_active': None
            },
            'current_task': None,
            'task_history': []
        }
        
        # Client ownership metadata
        self.owner_id = config.get('owner_id')
        self.ownership_type = config.get('ownership_type', 'system')  # system, client, shared
        self.exportable = config.get('exportable', False)
        
        # Communication handler
        self.communication_handler = None
        
        # Setup logging
        self.logger = logging.getLogger(f"agent.{self.agent_id}")
        
    def initialize(self) -> bool:
        """
        Initialize the agent and prepare it for operation
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing agent {self.agent_id}")
            
            # Register capabilities from config
            if 'capabilities' in self.config:
                for capability, params in self.config['capabilities'].items():
                    self.register_capability(capability, params)
            
            # Set up secure storage if needed
            if self.config.get('use_secure_storage', False):
                self._setup_secure_storage()
            
            # Initialize communication handler if provided
            if 'communication_handler' in self.config:
                self.communication_handler = self.config['communication_handler']
            
            # Update state
            self.state['status'] = 'initialized'
            self.state['initialized_at'] = datetime.now().isoformat()
            
            return True
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            self.state['status'] = 'initialization_failed'
            return False
    
    def register_capability(self, capability_name: str, parameters: Dict[str, Any] = None) -> bool:
        """
        Register a capability that this agent can perform
        
        Args:
            capability_name: Name of the capability
            parameters: Optional parameters for the capability
            
        Returns:
            True if registration was successful, False otherwise
        """
        try:
            self.state['capabilities'][capability_name] = {
                'parameters': parameters or {},
                'registered_at': datetime.now().isoformat()
            }
            self.logger.info(f"Registered capability: {capability_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register capability {capability_name}: {str(e)}")
            return False
    
    def has_capability(self, capability_name: str) -> bool:
        """
        Check if the agent has a specific capability
        
        Args:
            capability_name: Name of the capability to check
            
        Returns:
            True if the agent has the capability, False otherwise
        """
        return capability_name in self.state['capabilities']
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task and return the result
        
        Args:
            task: Task definition dictionary
            
        Returns:
            Dictionary containing the task result
        """
        if not task or 'type' not in task:
            return {'status': 'failed', 'error': 'Invalid task format'}
        
        task_type = task['type']
        task_id = task.get('id', str(uuid.uuid4()))
        
        # Check if agent has the required capability
        if not self.has_capability(task_type):
            return {
                'status': 'failed',
                'error': f"Agent does not have capability: {task_type}",
                'task_id': task_id
            }
        
        # Update state
        start_time = time.time()
        self.state['status'] = 'busy'
        self.state['current_task'] = task
        self.state['last_active'] = datetime.now().isoformat()
        
        try:
            # Execute the task using the appropriate capability handler
            # In a real implementation, this would dispatch to specific handlers
            self.logger.info(f"Executing task {task_id} of type {task_type}")
            
            # Placeholder for actual task execution
            # In a real implementation, this would be replaced with actual logic
            result = self._execute_capability(task_type, task)
            
            # Update metrics
            duration = time.time() - start_time
            self._update_metrics(True, duration)
            
            # Add to task history
            self.state['task_history'].append({
                'task_id': task_id,
                'type': task_type,
                'status': 'completed',
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                'status': 'completed',
                'result': result,
                'task_id': task_id,
                'duration': duration
            }
            
        except Exception as e:
            # Update metrics for failure
            duration = time.time() - start_time
            self._update_metrics(False, duration)
            
            # Add to task history
            self.state['task_history'].append({
                'task_id': task_id,
                'type': task_type,
                'status': 'failed',
                'error': str(e),
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.error(f"Task execution failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'task_id': task_id
            }
        finally:
            # Reset state
            self.state['status'] = 'idle'
            self.state['current_task'] = None
    
    def _execute_capability(self, capability_name: str, task: Dict[str, Any]) -> Any:
        """
        Execute a specific capability
        
        Args:
            capability_name: Name of the capability to execute
            task: Task definition dictionary
            
        Returns:
            Result of the capability execution
        """
        # This is a placeholder method that would be overridden by specific agent implementations
        # or would dispatch to registered capability handlers
        
        # For demonstration purposes, just return a simple result
        return {
            'message': f"Executed capability {capability_name}",
            'timestamp': datetime.now().isoformat()
        }
    
    def _update_metrics(self, success: bool, duration: float) -> None:
        """
        Update agent metrics after task execution
        
        Args:
            success: Whether the task was successful
            duration: Task execution duration in seconds
        """
        metrics = self.state['metrics']
        
        if success:
            metrics['tasks_completed'] += 1
        else:
            metrics['tasks_failed'] += 1
        
        # Update average task duration
        total_tasks = metrics['tasks_completed'] + metrics['tasks_failed']
        if total_tasks == 1:
            metrics['avg_task_duration'] = duration
        else:
            metrics['avg_task_duration'] = (
                (metrics['avg_task_duration'] * (total_tasks - 1) + duration) / total_tasks
            )
        
        metrics['last_active'] = datetime.now().isoformat()
    
    def report_status(self) -> Dict[str, Any]:
        """
        Report the current status of the agent
        
        Returns:
            Dictionary containing agent status information
        """
        return {
            'agent_id': self.agent_id,
            'status': self.state['status'],
            'capabilities': list(self.state['capabilities'].keys()),
            'metrics': self.state['metrics'],
            'current_task': self.state['current_task'],
            'owner_id': self.owner_id,
            'ownership_type': self.ownership_type,
            'exportable': self.exportable
        }
    
    def terminate(self) -> bool:
        """
        Terminate the agent and clean up resources
        
        Returns:
            True if termination was successful, False otherwise
        """
        try:
            self.logger.info(f"Terminating agent {self.agent_id}")
            
            # Clean up any resources
            # This would be implemented by specific agent types
            
            # Update state
            self.state['status'] = 'terminated'
            self.state['terminated_at'] = datetime.now().isoformat()
            
            return True
        except Exception as e:
            self.logger.error(f"Termination failed: {str(e)}")
            return False
    
    def prepare_for_export(self) -> Dict[str, Any]:
        """
        Prepare the agent for export to a client environment
        
        Returns:
            Dictionary containing exportable agent configuration
        """
        if not self.exportable:
            raise ValueError("This agent is not exportable")
        
        # Create a clean export configuration
        export_config = {
            'agent_id': self.agent_id,
            'agent_type': self.__class__.__name__,
            'capabilities': self.state['capabilities'],
            'configuration': {
                # Include only necessary configuration items
                k: v for k, v in self.config.items()
                if k not in ['secure_credentials', 'internal_endpoints']
            },
            'owner_id': self.owner_id,
            'ownership_type': self.ownership_type,
            'exported_at': datetime.now().isoformat(),
            'metrics': {
                'tasks_completed': self.state['metrics']['tasks_completed'],
                'avg_task_duration': self.state['metrics']['avg_task_duration']
            }
        }
        
        return export_config
    
    def _setup_secure_storage(self) -> None:
        """
        Set up secure storage for sensitive agent state
        """
        # This is a placeholder for actual secure storage implementation
        # In a real implementation, this would use encryption or secure storage services
        self.logger.info("Setting up secure storage for agent state")
        
        # Example implementation might use AWS KMS or similar service
        if 'secure_storage' not in self.state:
            self.state['secure_storage'] = {
                'enabled': True,
                'initialized_at': datetime.now().isoformat()
            }