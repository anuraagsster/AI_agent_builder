import logging
from typing import Any, Dict, List, Optional, Union
import importlib
from datetime import datetime

class CrewAIAdapter:
    """
    Adapter for integrating with CrewAI framework.
    This adapter translates between our system's agent interface and CrewAI's agent interface.
    
    CrewAI is a framework for orchestrating role-playing autonomous AI agents. This adapter
    allows our system to leverage CrewAI's capabilities while maintaining our own abstractions.
    """
    
    def __init__(self, config=None):
        """
        Initialize the CrewAI adapter
        
        Args:
            config: Configuration dictionary for the adapter
        """
        self.config = config or {}
        self.logger = logging.getLogger("crewai_adapter")
        self._crewai_available = self._check_crewai_available()
        
        # Store references to CrewAI classes if available
        self.crewai_agent_class = None
        self.crewai_task_class = None
        self.crewai_crew_class = None
        
        if self._crewai_available:
            self._initialize_crewai_classes()
        
    def _check_crewai_available(self) -> bool:
        """
        Check if CrewAI is available in the environment
        
        Returns:
            True if CrewAI is available, False otherwise
        """
        try:
            importlib.import_module('crewai')
            self.logger.info("CrewAI framework is available")
            return True
        except ImportError:
            self.logger.warning("CrewAI framework is not available. Some functionality will be limited.")
            return False
    
    def _initialize_crewai_classes(self) -> None:
        """
        Initialize references to CrewAI classes
        """
        try:
            crewai = importlib.import_module('crewai')
            self.crewai_agent_class = getattr(crewai, 'Agent')
            self.crewai_task_class = getattr(crewai, 'Task')
            self.crewai_crew_class = getattr(crewai, 'Crew')
            self.logger.info("Successfully initialized CrewAI classes")
        except (ImportError, AttributeError) as e:
            self.logger.error(f"Failed to initialize CrewAI classes: {str(e)}")
            self._crewai_available = False
        
    def create_crewai_agent(self, agent_config: Dict[str, Any]) -> Any:
        """
        Convert our agent configuration to a CrewAI agent
        
        Args:
            agent_config: Our system's agent configuration
            
        Returns:
            A CrewAI compatible agent or None if CrewAI is not available
        """
        if not self._crewai_available:
            self.logger.warning("Cannot create CrewAI agent: CrewAI is not available")
            return None
            
        try:
            # Extract relevant fields from our agent config
            name = agent_config.get('name', f"Agent-{agent_config.get('agent_id', 'unknown')}")
            role = agent_config.get('role', 'Assistant')
            goal = agent_config.get('goal', 'Help the user with their tasks')
            backstory = agent_config.get('description', 'An AI assistant')
            verbose = self.config.get('verbose', True)
            
            # Extract LLM configuration if available
            llm_config = agent_config.get('llm_config', {})
            llm = None
            
            # If there's a specific LLM provider configuration, use it
            if 'provider' in llm_config:
                llm = self._create_llm_from_config(llm_config)
            
            # Preserve ownership metadata
            allow_delegation = agent_config.get('ownership_type', 'system') != 'client'
            
            # Create the CrewAI agent
            crewai_agent = self.crewai_agent_class(
                name=name,
                role=role,
                goal=goal,
                backstory=backstory,
                verbose=verbose,
                allow_delegation=allow_delegation,
                llm=llm
            )
            
            # Store original agent_id for reference
            crewai_agent.original_agent_id = agent_config.get('agent_id')
            
            # Store ownership metadata
            crewai_agent.owner_id = agent_config.get('owner_id')
            crewai_agent.ownership_type = agent_config.get('ownership_type', 'system')
            crewai_agent.exportable = agent_config.get('exportable', False)
            
            self.logger.info(f"Created CrewAI agent: {name}")
            return crewai_agent
            
        except Exception as e:
            self.logger.error(f"Failed to create CrewAI agent: {str(e)}")
            return None
    
    def _create_llm_from_config(self, llm_config: Dict[str, Any]) -> Any:
        """
        Create an LLM instance from configuration
        
        Args:
            llm_config: LLM configuration dictionary
            
        Returns:
            An LLM instance compatible with CrewAI
        """
        provider = llm_config.get('provider', '').lower()
        
        try:
            if provider == 'openai':
                from langchain.chat_models import ChatOpenAI
                return ChatOpenAI(
                    model_name=llm_config.get('model', 'gpt-4'),
                    temperature=llm_config.get('temperature', 0.7),
                    api_key=llm_config.get('api_key')
                )
            elif provider == 'anthropic':
                from langchain.chat_models import ChatAnthropic
                return ChatAnthropic(
                    model=llm_config.get('model', 'claude-2'),
                    temperature=llm_config.get('temperature', 0.7),
                    api_key=llm_config.get('api_key')
                )
            else:
                self.logger.warning(f"Unsupported LLM provider: {provider}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to create LLM: {str(e)}")
            return None
        
    def convert_task(self, task: Dict[str, Any]) -> Any:
        """
        Convert our task format to CrewAI's task format
        
        Args:
            task: Our system's task object
            
        Returns:
            A CrewAI compatible task or None if CrewAI is not available
        """
        if not self._crewai_available:
            self.logger.warning("Cannot convert task: CrewAI is not available")
            return None
            
        try:
            # Extract relevant fields from our task
            description = task.get('description', '')
            if 'type' in task:
                description = f"{task['type']}: {description}"
                
            task_id = task.get('id', str(datetime.now().timestamp()))
            expected_output = task.get('expected_output', 'Completed task')
            
            # Create the CrewAI task
            crewai_task = self.crewai_task_class(
                description=description,
                expected_output=expected_output
            )
            
            # Store original task_id for reference
            crewai_task.original_task_id = task_id
            
            # Store ownership metadata if available
            if 'owner_id' in task:
                crewai_task.owner_id = task['owner_id']
                
            self.logger.info(f"Converted task: {task_id}")
            return crewai_task
            
        except Exception as e:
            self.logger.error(f"Failed to convert task: {str(e)}")
            return None
        
    def process_result(self, crewai_result: Any) -> Dict[str, Any]:
        """
        Convert CrewAI's result format to our system's result format
        
        Args:
            crewai_result: Result from CrewAI
            
        Returns:
            Our system's result format
        """
        try:
            # CrewAI typically returns a string result
            if isinstance(crewai_result, str):
                return {
                    'status': 'completed',
                    'result': crewai_result,
                    'timestamp': datetime.now().isoformat()
                }
            
            # If it's already a dictionary, ensure it has our required fields
            elif isinstance(crewai_result, dict):
                result = crewai_result.copy()
                if 'status' not in result:
                    result['status'] = 'completed'
                if 'timestamp' not in result:
                    result['timestamp'] = datetime.now().isoformat()
                return result
                
            # For other types, wrap in our format
            else:
                return {
                    'status': 'completed',
                    'result': str(crewai_result),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to process CrewAI result: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def create_crew(self, agents: List[Any], tasks: List[Any]) -> Any:
        """
        Create a CrewAI crew with the given agents and tasks
        
        Args:
            agents: List of CrewAI agents
            tasks: List of CrewAI tasks
            
        Returns:
            A CrewAI crew or None if CrewAI is not available
        """
        if not self._crewai_available:
            self.logger.warning("Cannot create CrewAI crew: CrewAI is not available")
            return None
            
        try:
            # Check for ownership compatibility
            self._validate_ownership_compatibility(agents)
            
            # Create the CrewAI crew
            crew = self.crewai_crew_class(
                agents=agents,
                tasks=tasks,
                verbose=self.config.get('verbose', True)
            )
            
            self.logger.info(f"Created CrewAI crew with {len(agents)} agents and {len(tasks)} tasks")
            return crew
            
        except Exception as e:
            self.logger.error(f"Failed to create CrewAI crew: {str(e)}")
            return None
    
    def _validate_ownership_compatibility(self, agents: List[Any]) -> None:
        """
        Validate that all agents in a crew have compatible ownership
        
        Args:
            agents: List of CrewAI agents
            
        Raises:
            ValueError: If agents have incompatible ownership
        """
        # Group agents by owner_id
        owners = {}
        for agent in agents:
            owner_id = getattr(agent, 'owner_id', None)
            if owner_id:
                if owner_id not in owners:
                    owners[owner_id] = []
                owners[owner_id].append(agent)
        
        # If we have multiple owners, check if any agents are not exportable
        if len(owners) > 1:
            for owner_id, owner_agents in owners.items():
                for agent in owner_agents:
                    if not getattr(agent, 'exportable', False):
                        raise ValueError(f"Agent {agent.name} is not exportable and cannot be used in a multi-owner crew")
    
    def prepare_for_export(self, crewai_agent: Any) -> Dict[str, Any]:
        """
        Prepare a CrewAI agent for export to a client environment
        
        Args:
            crewai_agent: A CrewAI agent
            
        Returns:
            Dictionary containing exportable agent configuration
        """
        if not hasattr(crewai_agent, 'exportable') or not crewai_agent.exportable:
            raise ValueError("This agent is not exportable")
            
        # Create a clean export configuration
        export_config = {
            'agent_id': getattr(crewai_agent, 'original_agent_id', None),
            'name': crewai_agent.name,
            'role': crewai_agent.role,
            'goal': crewai_agent.goal,
            'backstory': crewai_agent.backstory,
            'owner_id': getattr(crewai_agent, 'owner_id', None),
            'ownership_type': getattr(crewai_agent, 'ownership_type', 'client'),
            'exportable': True,
            'exported_at': datetime.now().isoformat(),
            'framework': 'crewai'
        }
        
        return export_config