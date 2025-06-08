# __init__.py for Foundation Layer module

# Import submodules
from .architecture import ComponentRegistry, ExtensionSystem
from .config_management import ConfigManager, DependencyManager
from .deployment import ResourceAbstraction, EnvironmentDetector
from .agent_framework import BaseAgent, AgentCommunication, FrameworkAdapters
from .workload_management import TaskDistributor, ResourceMonitor, QualityController