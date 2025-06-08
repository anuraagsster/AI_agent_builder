"""
Configuration schema for the Foundation Layer.
This file defines the schema for validating configuration files.
"""

from typing import Dict, List, Union, Optional, Literal

# Type definitions for configuration validation
ArchitecturePattern = Literal["centralized", "distributed", "hybrid"]
IsolationMethod = Literal["virtual_env", "container", "none"]
VersionCheckFrequency = Literal["startup", "daily", "weekly", "never"]
DeploymentEnvironment = Literal["local", "cloud", "hybrid"]
CloudProvider = Literal["aws", "azure", "gcp"]
TaskDistributionAlgorithm = Literal["balanced", "priority", "capability"]

# Schema definitions
ARCHITECTURE_SCHEMA = {
    "pattern": {
        "type": ArchitecturePattern,
        "required": True,
        "default": "hybrid",
    },
    "component_registry": {
        "type": Dict,
        "required": True,
        "schema": {
            "auto_discovery": {
                "type": bool,
                "required": False,
                "default": True,
            },
            "discovery_paths": {
                "type": List[str],
                "required": False,
                "default": ["src"],
            },
        },
    },
    "extension_system": {
        "type": Dict,
        "required": True,
        "schema": {
            "enabled": {
                "type": bool,
                "required": False,
                "default": True,
            },
            "plugin_directory": {
                "type": str,
                "required": False,
                "default": "plugins",
            },
            "auto_load": {
                "type": bool,
                "required": False,
                "default": True,
            },
        },
    },
}

DEPENDENCIES_SCHEMA = {
    "version_check_frequency": {
        "type": VersionCheckFrequency,
        "required": False,
        "default": "daily",
    },
    "auto_update": {
        "type": bool,
        "required": False,
        "default": False,
    },
    "isolation_method": {
        "type": IsolationMethod,
        "required": False,
        "default": "virtual_env",
    },
}

CONFIG_SCHEMA = {
    "config_file": {
        "type": str,
        "required": False,
        "default": "config.yaml",
    },
    "environment_variable_prefix": {
        "type": str,
        "required": False,
        "default": "AGENT_CREATOR",
    },
    "dynamic_reload": {
        "type": bool,
        "required": False,
        "default": True,
    },
    "validation_on_load": {
        "type": bool,
        "required": False,
        "default": True,
    },
}

DEPLOYMENT_SCHEMA = {
    "default_environment": {
        "type": DeploymentEnvironment,
        "required": False,
        "default": "local",
    },
    "environments": {
        "type": Dict,
        "required": True,
        "schema": {
            "local": {
                "type": Dict,
                "required": False,
                "schema": {
                    "max_resources": {
                        "type": Dict,
                        "required": False,
                    },
                },
            },
            "cloud": {
                "type": Dict,
                "required": False,
                "schema": {
                    "provider": {
                        "type": CloudProvider,
                        "required": False,
                        "default": "aws",
                    },
                    "region": {
                        "type": str,
                        "required": False,
                    },
                    "auto_scaling": {
                        "type": bool,
                        "required": False,
                        "default": True,
                    },
                },
            },
        },
    },
}

AGENT_FRAMEWORK_SCHEMA = {
    "base_agent": {
        "type": Dict,
        "required": True,
        "schema": {
            "default_timeout": {
                "type": int,
                "required": False,
                "default": 60,
            },
            "max_retries": {
                "type": int,
                "required": False,
                "default": 3,
            },
            "metrics_collection": {
                "type": bool,
                "required": False,
                "default": True,
            },
        },
    },
    "communication": {
        "type": Dict,
        "required": True,
        "schema": {
            "message_format": {
                "type": str,
                "required": False,
                "default": "json",
            },
            "async_enabled": {
                "type": bool,
                "required": False,
                "default": True,
            },
            "retry_failed_messages": {
                "type": bool,
                "required": False,
                "default": True,
            },
        },
    },
    "frameworks": {
        "type": Dict,
        "required": True,
    },
}

WORKLOAD_MANAGEMENT_SCHEMA = {
    "task_distribution": {
        "type": Dict,
        "required": True,
        "schema": {
            "algorithm": {
                "type": TaskDistributionAlgorithm,
                "required": False,
                "default": "balanced",
            },
            "max_queue_size": {
                "type": int,
                "required": False,
                "default": 1000,
            },
            "default_priority": {
                "type": int,
                "required": False,
                "default": 5,
            },
        },
    },
    "resource_monitoring": {
        "type": Dict,
        "required": True,
        "schema": {
            "enabled": {
                "type": bool,
                "required": False,
                "default": True,
            },
            "interval": {
                "type": int,
                "required": False,
                "default": 5,
            },
            "warning_threshold": {
                "type": float,
                "required": False,
                "default": 0.8,
            },
            "critical_threshold": {
                "type": float,
                "required": False,
                "default": 0.95,
            },
        },
    },
    "quality_control": {
        "type": Dict,
        "required": True,
        "schema": {
            "verification_enabled": {
                "type": bool,
                "required": False,
                "default": True,
            },
            "feedback_collection": {
                "type": bool,
                "required": False,
                "default": True,
            },
            "minimum_quality_score": {
                "type": float,
                "required": False,
                "default": 0.7,
            },
        },
    },
}

# Complete schema
CONFIG_SCHEMA_COMPLETE = {
    "ARCHITECTURE": ARCHITECTURE_SCHEMA,
    "DEPENDENCIES": DEPENDENCIES_SCHEMA,
    "CONFIG": CONFIG_SCHEMA,
    "DEPLOYMENT": DEPLOYMENT_SCHEMA,
    "AGENT_FRAMEWORK": AGENT_FRAMEWORK_SCHEMA,
    "WORKLOAD_MANAGEMENT": WORKLOAD_MANAGEMENT_SCHEMA,
}