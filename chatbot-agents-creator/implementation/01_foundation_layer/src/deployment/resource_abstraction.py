"""
Resource Abstraction Layer for the Foundation Layer.

This module provides an abstraction layer for managing resources across different
deployment environments (local, cloud, hybrid). It handles resource allocation,
scaling, and environment detection.
"""

import os
import platform
import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnvironmentType(Enum):
    """Enum for supported environment types."""
    LOCAL = "local"
    CLOUD_AWS = "aws"
    CLOUD_AZURE = "azure"
    CLOUD_GCP = "gcp"
    HYBRID = "hybrid"

class ResourceType(Enum):
    """Enum for resource types."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"

class ResourceAbstraction:
    """
    Provides an abstraction layer for managing resources across different environments.
    
    This class handles resource allocation, scaling, and release in a way that's
    consistent across different deployment environments.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the ResourceAbstraction with configuration.
        
        Args:
            config: Configuration dictionary for resource management
        """
        self.config = config or {}
        self.environment_detector = EnvironmentDetector()
        self.current_environment = self.environment_detector.detect_environment()
        self.allocated_resources = {}
        logger.info(f"Resource abstraction initialized for {self.current_environment.value} environment")
    
    def allocate_resources(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        """
        Allocate resources based on the current environment.
        
        Args:
            resources: Dictionary of resources to allocate
                      {
                          "cpu": "2",
                          "memory": "4G",
                          "disk": "10G"
                      }
        
        Returns:
            Dictionary with allocation details and resource identifiers
        """
        env_type = self.current_environment
        allocation_result = {}
        
        logger.info(f"Allocating resources in {env_type.value} environment: {resources}")
        
        if env_type == EnvironmentType.LOCAL:
            # Local resource allocation logic
            allocation_result = self._allocate_local_resources(resources)
        elif env_type in [EnvironmentType.CLOUD_AWS, EnvironmentType.CLOUD_AZURE, EnvironmentType.CLOUD_GCP]:
            # Cloud resource allocation logic
            allocation_result = self._allocate_cloud_resources(resources, env_type)
        elif env_type == EnvironmentType.HYBRID:
            # Hybrid resource allocation logic
            allocation_result = self._allocate_hybrid_resources(resources)
        
        # Store allocated resources for tracking
        resource_id = f"resource_{len(self.allocated_resources) + 1}"
        self.allocated_resources[resource_id] = {
            "resources": resources,
            "allocation_result": allocation_result,
            "environment": env_type.value
        }
        
        allocation_result["resource_id"] = resource_id
        return allocation_result
    
    def _allocate_local_resources(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Allocate resources in the local environment."""
        # In a local environment, we're just checking if resources are available
        # and marking them as allocated in our tracking system
        
        # Get max resources from config
        max_resources = self.config.get("environments", {}).get("local", {}).get("max_resources", {})
        
        # Check if requested resources are available
        for resource_type, amount in resources.items():
            if resource_type in max_resources:
                # Simple string percentage parsing for demonstration
                if isinstance(amount, str) and amount.endswith("%"):
                    requested_percent = float(amount.rstrip("%")) / 100
                    max_percent = float(max_resources[resource_type].rstrip("%")) / 100
                    if requested_percent > max_percent:
                        logger.warning(f"Requested {resource_type} ({amount}) exceeds maximum ({max_resources[resource_type]})")
        
        # In a real implementation, we would actually reserve these resources
        return {
            "status": "allocated",
            "location": "local",
            "details": {
                "host": platform.node(),
                "allocated_resources": resources
            }
        }
    
    def _allocate_cloud_resources(self, resources: Dict[str, Any], cloud_provider: EnvironmentType) -> Dict[str, Any]:
        """Allocate resources in a cloud environment."""
        # In a real implementation, this would make API calls to the cloud provider
        
        provider_name = cloud_provider.value
        region = self.config.get("environments", {}).get("cloud", {}).get("region", "us-west-2")
        
        # Simulate cloud resource allocation
        logger.info(f"Allocating resources on {provider_name} in region {region}")
        
        # This would be replaced with actual API calls in a real implementation
        return {
            "status": "allocated",
            "location": f"cloud:{provider_name}",
            "region": region,
            "details": {
                "instance_type": "t3.medium",  # Example
                "allocated_resources": resources
            }
        }
    
    def _allocate_hybrid_resources(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Allocate resources in a hybrid environment."""
        # In a hybrid environment, we decide whether to allocate locally or in the cloud
        # based on resource requirements and availability
        
        # Simple strategy: CPU/Memory intensive tasks go to cloud, others stay local
        if "cpu" in resources and isinstance(resources["cpu"], str) and resources["cpu"].endswith("%"):
            cpu_percent = float(resources["cpu"].rstrip("%"))
            if cpu_percent > 50:  # If CPU requirement is high, use cloud
                return self._allocate_cloud_resources(resources, EnvironmentType.CLOUD_AWS)
        
        # Default to local for most resources
        return self._allocate_local_resources(resources)
    
    def release_resources(self, resource_id: str) -> bool:
        """
        Release previously allocated resources.
        
        Args:
            resource_id: The identifier of the resources to release
            
        Returns:
            True if resources were successfully released, False otherwise
        """
        if resource_id not in self.allocated_resources:
            logger.warning(f"Resource ID {resource_id} not found")
            return False
        
        resource_info = self.allocated_resources[resource_id]
        env_type = EnvironmentType(resource_info["environment"])
        
        logger.info(f"Releasing resources for {resource_id} in {env_type.value} environment")
        
        # Implement environment-specific resource release logic
        if env_type == EnvironmentType.LOCAL:
            # Local resource release logic
            pass
        elif env_type in [EnvironmentType.CLOUD_AWS, EnvironmentType.CLOUD_AZURE, EnvironmentType.CLOUD_GCP]:
            # Cloud resource release logic - would make API calls to release resources
            pass
        
        # Remove from tracking
        del self.allocated_resources[resource_id]
        return True
    
    def scale_resources(self, resource_id: str, scale_factor: float) -> Dict[str, Any]:
        """
        Scale allocated resources by the given factor.
        
        Args:
            resource_id: The identifier of the resources to scale
            scale_factor: Factor to scale resources by (e.g., 2.0 doubles resources)
            
        Returns:
            Updated resource allocation information
        """
        if resource_id not in self.allocated_resources:
            logger.warning(f"Resource ID {resource_id} not found")
            return {"status": "error", "message": "Resource not found"}
        
        resource_info = self.allocated_resources[resource_id]
        env_type = EnvironmentType(resource_info["environment"])
        original_resources = resource_info["resources"]
        
        # Create scaled resource request
        scaled_resources = {}
        for resource_type, amount in original_resources.items():
            if isinstance(amount, (int, float)):
                scaled_resources[resource_type] = amount * scale_factor
            elif isinstance(amount, str) and amount.endswith("%"):
                percent = float(amount.rstrip("%"))
                scaled_percent = min(percent * scale_factor, 100)  # Cap at 100%
                scaled_resources[resource_type] = f"{scaled_percent}%"
            else:
                scaled_resources[resource_type] = amount  # Keep as is if we can't scale
        
        logger.info(f"Scaling resources for {resource_id} by factor {scale_factor}")
        logger.info(f"Original: {original_resources}, Scaled: {scaled_resources}")
        
        # Release old resources and allocate new ones
        self.release_resources(resource_id)
        return self.allocate_resources(scaled_resources)
    
    def get_resource_usage(self, resource_id: str = None) -> Dict[str, Any]:
        """
        Get current resource usage information.
        
        Args:
            resource_id: Optional resource ID to get specific resource usage
            
        Returns:
            Dictionary with resource usage information
        """
        if resource_id and resource_id in self.allocated_resources:
            return self.allocated_resources[resource_id]
        
        # If no specific resource_id or not found, return overall usage
        return {
            "total_allocations": len(self.allocated_resources),
            "environments": {env.value: 0 for env in EnvironmentType},
            "resources": self.allocated_resources
        }
    
    def package_for_export(self, resource_id: str, export_format: str = "json") -> str:
        """
        Package resource configuration for client deployment.
        
        Args:
            resource_id: The identifier of the resources to export
            export_format: Format for the export (json or yaml)
            
        Returns:
            Serialized resource configuration for deployment
        """
        if resource_id not in self.allocated_resources:
            logger.warning(f"Resource ID {resource_id} not found")
            return ""
        
        resource_info = self.allocated_resources[resource_id]
        
        # Create exportable configuration
        export_config = {
            "resource_configuration": {
                "type": resource_info["environment"],
                "resources": resource_info["resources"],
                "deployment_details": resource_info["allocation_result"]
            },
            "metadata": {
                "exported_at": "2025-08-06T15:30:00Z",  # In a real implementation, use actual timestamp
                "version": "1.0",
                "exportable": True
            }
        }
        
        # Serialize to requested format
        if export_format.lower() == "json":
            return json.dumps(export_config, indent=2)
        elif export_format.lower() == "yaml":
            return yaml.dump(export_config, default_flow_style=False)
        else:
            logger.error(f"Unsupported export format: {export_format}")
            return ""


class EnvironmentDetector:
    """
    Detects and provides information about the current execution environment.
    
    This class is responsible for determining whether the code is running in a
    local environment, cloud environment, or hybrid environment.
    """
    
    def __init__(self):
        """Initialize the environment detector."""
        self.env_info = {}
    
    def detect_environment(self) -> EnvironmentType:
        """
        Detect the current execution environment.
        
        Returns:
            EnvironmentType enum indicating the detected environment
        """
        # Check for cloud environment indicators
        if self._is_aws_environment():
            return EnvironmentType.CLOUD_AWS
        elif self._is_azure_environment():
            return EnvironmentType.CLOUD_AZURE
        elif self._is_gcp_environment():
            return EnvironmentType.CLOUD_GCP
        
        # Check for hybrid environment indicators
        if self._is_hybrid_environment():
            return EnvironmentType.HYBRID
        
        # Default to local environment
        return EnvironmentType.LOCAL
    
    def _is_aws_environment(self) -> bool:
        """Check if running in AWS environment."""
        # Check for AWS-specific environment variables
        aws_indicators = [
            "AWS_REGION", "AWS_DEFAULT_REGION", "AWS_LAMBDA_FUNCTION_NAME",
            "AWS_EXECUTION_ENV", "AWS_LAMBDA_FUNCTION_VERSION"
        ]
        return any(indicator in os.environ for indicator in aws_indicators)
    
    def _is_azure_environment(self) -> bool:
        """Check if running in Azure environment."""
        # Check for Azure-specific environment variables
        azure_indicators = [
            "AZURE_FUNCTIONS_ENVIRONMENT", "WEBSITE_SITE_NAME",
            "WEBSITE_INSTANCE_ID", "WEBSITE_RESOURCE_GROUP"
        ]
        return any(indicator in os.environ for indicator in azure_indicators)
    
    def _is_gcp_environment(self) -> bool:
        """Check if running in GCP environment."""
        # Check for GCP-specific environment variables
        gcp_indicators = [
            "FUNCTION_NAME", "FUNCTION_REGION", "FUNCTION_IDENTITY",
            "GCP_PROJECT", "GOOGLE_CLOUD_PROJECT"
        ]
        return any(indicator in os.environ for indicator in gcp_indicators)
    
    def _is_hybrid_environment(self) -> bool:
        """Check if running in a hybrid environment."""
        # This is a simplified check - in reality, hybrid detection would be more complex
        # For example, check if we have connections to both local and cloud resources
        return False  # Default to not hybrid for now
    
    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get detailed information about the current environment.
        
        Returns:
            Dictionary with environment details
        """
        env_type = self.detect_environment()
        
        # Collect basic system information
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count()
        }
        
        # Add environment-specific information
        if env_type == EnvironmentType.LOCAL:
            system_info.update(self._get_local_environment_info())
        elif env_type == EnvironmentType.CLOUD_AWS:
            system_info.update(self._get_aws_environment_info())
        elif env_type == EnvironmentType.CLOUD_AZURE:
            system_info.update(self._get_azure_environment_info())
        elif env_type == EnvironmentType.CLOUD_GCP:
            system_info.update(self._get_gcp_environment_info())
        
        system_info["environment_type"] = env_type.value
        return system_info
    
    def _get_local_environment_info(self) -> Dict[str, Any]:
        """Get information specific to local environments."""
        # In a real implementation, this would include more detailed system metrics
        return {
            "memory_total": "N/A",  # Would use psutil to get actual memory
            "disk_space": "N/A",    # Would use os.statvfs or similar
            "is_virtual_machine": "N/A"  # Would detect if running in VM
        }
    
    def _get_aws_environment_info(self) -> Dict[str, Any]:
        """Get information specific to AWS environments."""
        return {
            "region": os.environ.get("AWS_REGION", "unknown"),
            "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "N/A"),
            "execution_env": os.environ.get("AWS_EXECUTION_ENV", "N/A")
        }
    
    def _get_azure_environment_info(self) -> Dict[str, Any]:
        """Get information specific to Azure environments."""
        return {
            "site_name": os.environ.get("WEBSITE_SITE_NAME", "N/A"),
            "resource_group": os.environ.get("WEBSITE_RESOURCE_GROUP", "N/A"),
            "instance_id": os.environ.get("WEBSITE_INSTANCE_ID", "N/A")
        }
    
    def _get_gcp_environment_info(self) -> Dict[str, Any]:
        """Get information specific to GCP environments."""
        return {
            "project": os.environ.get("GOOGLE_CLOUD_PROJECT", "N/A"),
            "function_name": os.environ.get("FUNCTION_NAME", "N/A"),
            "function_region": os.environ.get("FUNCTION_REGION", "N/A")
        }


class DeploymentTemplate:
    """
    Manages deployment templates for different environments.
    
    This class provides functionality to create, customize, and apply deployment
    templates for different environments.
    """
    
    def __init__(self, template_dir: str = None):
        """
        Initialize the deployment template manager.
        
        Args:
            template_dir: Directory containing template files
        """
        self.template_dir = template_dir or "templates/deployment"
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load available templates from the template directory."""
        # In a real implementation, this would load template files from disk
        # For now, we'll define some basic templates inline
        
        self.templates = {
            "aws_lambda": {
                "type": "serverless",
                "provider": "aws",
                "resources": {
                    "memory": "128MB",
                    "timeout": 30
                },
                "environment": {
                    "variables": {}
                }
            },
            "aws_ec2": {
                "type": "server",
                "provider": "aws",
                "resources": {
                    "instance_type": "t3.micro",
                    "volume_size": "20GB"
                }
            },
            "docker": {
                "type": "container",
                "base_image": "python:3.9-slim",
                "ports": ["8080:8080"],
                "environment": {
                    "variables": {}
                }
            },
            "kubernetes": {
                "type": "container_orchestration",
                "replicas": 1,
                "resources": {
                    "requests": {
                        "cpu": "100m",
                        "memory": "128Mi"
                    },
                    "limits": {
                        "cpu": "500m",
                        "memory": "512Mi"
                    }
                }
            }
        }
    
    def get_template(self, template_name: str) -> Dict[str, Any]:
        """
        Get a deployment template by name.
        
        Args:
            template_name: Name of the template to retrieve
            
        Returns:
            Template configuration dictionary
        """
        if template_name not in self.templates:
            logger.warning(f"Template {template_name} not found")
            return {}
        
        return self.templates[template_name].copy()
    
    def customize_template(self, template_name: str, customizations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Customize a deployment template.
        
        Args:
            template_name: Name of the template to customize
            customizations: Dictionary of customizations to apply
            
        Returns:
            Customized template configuration
        """
        template = self.get_template(template_name)
        if not template:
            return {}
        
        # Apply customizations (deep merge)
        self._deep_update(template, customizations)
        return template
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Recursively update a dictionary with another dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def generate_deployment_files(self, template: Dict[str, Any], output_dir: str) -> List[str]:
        """
        Generate deployment files from a template.
        
        Args:
            template: Template configuration
            output_dir: Directory to write deployment files
            
        Returns:
            List of generated file paths
        """
        # In a real implementation, this would generate actual deployment files
        # For now, we'll just log what would be generated
        
        template_type = template.get("type", "unknown")
        provider = template.get("provider", "generic")
        
        logger.info(f"Generating {template_type} deployment files for {provider} in {output_dir}")
        
        # This would actually write files in a real implementation
        generated_files = []
        
        if template_type == "serverless" and provider == "aws":
            # Would generate serverless.yml, handler.py, etc.
            generated_files = [
                f"{output_dir}/serverless.yml",
                f"{output_dir}/handler.py"
            ]
        elif template_type == "server" and provider == "aws":
            # Would generate CloudFormation template, user-data script, etc.
            generated_files = [
                f"{output_dir}/cloudformation.yaml",
                f"{output_dir}/user-data.sh"
            ]
        elif template_type == "container":
            # Would generate Dockerfile, docker-compose.yml, etc.
            generated_files = [
                f"{output_dir}/Dockerfile",
                f"{output_dir}/docker-compose.yml"
            ]
        elif template_type == "container_orchestration":
            # Would generate Kubernetes manifests
            generated_files = [
                f"{output_dir}/deployment.yaml",
                f"{output_dir}/service.yaml"
            ]
        
        return generated_files