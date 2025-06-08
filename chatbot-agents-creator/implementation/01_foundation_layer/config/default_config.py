"""
Default configuration for the Foundation Layer.
This file contains default settings that can be overridden by environment-specific configurations.
"""

# System Architecture Configuration
ARCHITECTURE = {
    "pattern": "hybrid",  # Options: centralized, distributed, hybrid
    "component_registry": {
        "auto_discovery": True,
        "discovery_paths": ["src"],
    },
    "extension_system": {
        "enabled": True,
        "plugin_directory": "plugins",
        "auto_load": True,
    },
}

# Dependency Management Configuration
DEPENDENCIES = {
    "version_check_frequency": "daily",  # Options: startup, daily, weekly, never
    "auto_update": False,
    "isolation_method": "virtual_env",  # Options: virtual_env, container, none
}

# Configuration Management
CONFIG = {
    "config_file": "config.yaml",
    "environment_variable_prefix": "AGENT_CREATOR",
    "dynamic_reload": True,
    "validation_on_load": True,
}

# Deployment Configuration
DEPLOYMENT = {
    "default_environment": "local",  # Options: local, cloud, hybrid
    "environments": {
        "local": {
            "max_resources": {
                "cpu": "80%",
                "memory": "70%",
                "disk": "90%",
            },
        },
        "cloud": {
            "provider": "aws",  # Options: aws, azure, gcp
            "region": "us-west-2",
            "auto_scaling": True,
        },
    },
}

# Agent Framework Configuration
AGENT_FRAMEWORK = {
    "base_agent": {
        "default_timeout": 60,  # seconds
        "max_retries": 3,
        "metrics_collection": True,
    },
    "communication": {
        "message_format": "json",
        "async_enabled": True,
        "retry_failed_messages": True,
    },
    "frameworks": {
        "crewai": {
            "enabled": True,
            "config_path": "config/crewai_config.yaml",
        },
        "mcp": {
            "enabled": True,
            "config_path": "config/mcp_config.yaml",
        },
    },
}

# Workload Management Configuration
WORKLOAD_MANAGEMENT = {
    "task_distribution": {
        "algorithm": "balanced",  # Options: balanced, priority, capability
        "max_queue_size": 1000,
        "default_priority": 5,
    },
    "resource_monitoring": {
        "enabled": True,
        "interval": 5,  # seconds
        "warning_threshold": 0.8,  # 80%
        "critical_threshold": 0.95,  # 95%
    },
    "quality_control": {
        "verification_enabled": True,
        "feedback_collection": True,
        "minimum_quality_score": 0.7,  # 70%
    },
}