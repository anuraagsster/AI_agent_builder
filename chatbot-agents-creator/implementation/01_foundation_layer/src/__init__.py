# __init__.py for Foundation Layer module

# Import submodules
from .architecture import ComponentRegistry, ExtensionSystem, ComponentMetadata
from .config_management import ConfigManager
from .deployment import ResourceAbstraction, EnvironmentDetector
from .agent_framework import BaseAgent, AgentCommunication, CrewAIAdapter, MCPAdapter
from .workload_management import TaskDistributor, ResourceMonitor, QualityController