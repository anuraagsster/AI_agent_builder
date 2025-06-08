import os
import json
import unittest
from unittest.mock import patch, MagicMock

# Import the module we want to test
from src.deployment.resource_abstraction import ResourceAbstraction, EnvironmentDetector, DeploymentTemplate, EnvironmentType


class TestEnvironmentDetector(unittest.TestCase):
    """Test cases for the EnvironmentDetector class"""

    def setUp(self):
        """Set up test fixtures"""
        self.detector = EnvironmentDetector()

    def test_init(self):
        """Test initialization of EnvironmentDetector"""
        self.assertIsInstance(self.detector, EnvironmentDetector)
        self.assertEqual(self.detector.env_info, {})

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_local_environment(self):
        """Test detecting local environment when no cloud indicators are present"""
        env_type = self.detector.detect_environment()
        self.assertEqual(env_type, EnvironmentType.LOCAL)

    @patch.dict(os.environ, {"AWS_REGION": "us-west-2"})
    def test_detect_aws_environment(self):
        """Test detecting AWS environment"""
        env_type = self.detector.detect_environment()
        self.assertEqual(env_type, EnvironmentType.CLOUD_AWS)

    @patch.dict(os.environ, {"AZURE_FUNCTIONS_ENVIRONMENT": "Production"})
    def test_detect_azure_environment(self):
        """Test detecting Azure environment"""
        env_type = self.detector.detect_environment()
        self.assertEqual(env_type, EnvironmentType.CLOUD_AZURE)

    @patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "my-project"})
    def test_detect_gcp_environment(self):
        """Test detecting GCP environment"""
        env_type = self.detector.detect_environment()
        self.assertEqual(env_type, EnvironmentType.CLOUD_GCP)

    def test_get_environment_info(self):
        """Test getting environment information"""
        env_info = self.detector.get_environment_info()
        
        # Basic checks for environment info
        self.assertIn("platform", env_info)
        self.assertIn("python_version", env_info)
        self.assertIn("hostname", env_info)
        self.assertIn("processor", env_info)
        self.assertIn("cpu_count", env_info)
        self.assertIn("environment_type", env_info)


class TestResourceAbstraction(unittest.TestCase):
    """Test cases for the ResourceAbstraction class"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "environments": {
                "local": {
                    "max_resources": {
                        "cpu": "80%",
                        "memory": "70%",
                        "disk": "90%",
                    },
                },
                "cloud": {
                    "provider": "aws",
                    "region": "us-west-2",
                    "auto_scaling": True,
                },
            },
        }
        
        # Mock the environment detector to always return LOCAL
        self.env_detector_patcher = patch('src.deployment.resource_abstraction.EnvironmentDetector')
        self.mock_env_detector = self.env_detector_patcher.start()
        self.mock_env_detector_instance = self.mock_env_detector.return_value
        self.mock_env_detector_instance.detect_environment.return_value = EnvironmentType.LOCAL
        
        self.resource_abstraction = ResourceAbstraction(config=self.config)

    def tearDown(self):
        """Tear down test fixtures"""
        self.env_detector_patcher.stop()

    def test_init(self):
        """Test initialization of ResourceAbstraction"""
        self.assertEqual(self.resource_abstraction.config, self.config)
        self.assertEqual(self.resource_abstraction.current_environment, EnvironmentType.LOCAL)
        self.assertEqual(self.resource_abstraction.allocated_resources, {})

    def test_allocate_local_resources(self):
        """Test allocating resources in local environment"""
        resources = {
            "cpu": "50%",
            "memory": "2G",
            "disk": "10G"
        }
        
        result = self.resource_abstraction.allocate_resources(resources)
        
        # Check result structure
        self.assertEqual(result["status"], "allocated")
        self.assertEqual(result["location"], "local")
        self.assertIn("details", result)
        self.assertIn("resource_id", result)
        
        # Check that resources were tracked
        resource_id = result["resource_id"]
        self.assertIn(resource_id, self.resource_abstraction.allocated_resources)
        self.assertEqual(
            self.resource_abstraction.allocated_resources[resource_id]["resources"], 
            resources
        )

    @patch('src.deployment.resource_abstraction.EnvironmentDetector')
    def test_allocate_cloud_resources(self, mock_env_detector):
        """Test allocating resources in cloud environment"""
        # Setup mock to return cloud environment
        mock_detector_instance = mock_env_detector.return_value
        mock_detector_instance.detect_environment.return_value = EnvironmentType.CLOUD_AWS
        
        # Create resource abstraction with cloud environment
        cloud_resource_abstraction = ResourceAbstraction(config=self.config)
        
        resources = {
            "cpu": "2",
            "memory": "4G",
            "disk": "100G"
        }
        
        result = cloud_resource_abstraction.allocate_resources(resources)
        
        # Check result structure
        self.assertEqual(result["status"], "allocated")
        self.assertEqual(result["location"], "cloud:aws")
        self.assertEqual(result["region"], "us-west-2")
        self.assertIn("details", result)
        self.assertIn("resource_id", result)

    def test_release_resources(self):
        """Test releasing allocated resources"""
        # First allocate resources
        resources = {"cpu": "50%", "memory": "2G"}
        allocation_result = self.resource_abstraction.allocate_resources(resources)
        resource_id = allocation_result["resource_id"]
        
        # Verify resource is allocated
        self.assertIn(resource_id, self.resource_abstraction.allocated_resources)
        
        # Release the resource
        result = self.resource_abstraction.release_resources(resource_id)
        
        # Verify release was successful
        self.assertTrue(result)
        self.assertNotIn(resource_id, self.resource_abstraction.allocated_resources)
        
        # Try to release non-existent resource
        result = self.resource_abstraction.release_resources("non-existent-id")
        self.assertFalse(result)

    def test_scale_resources(self):
        """Test scaling allocated resources"""
        # First allocate resources
        resources = {"cpu": "40%", "memory": "2G"}
        allocation_result = self.resource_abstraction.allocate_resources(resources)
        resource_id = allocation_result["resource_id"]
        
        # Scale up the resources
        scale_result = self.resource_abstraction.scale_resources(resource_id, 2.0)
        
        # Verify scaling result
        self.assertEqual(scale_result["status"], "allocated")
        
        # Check that the new allocation has scaled values
        new_resource_id = scale_result["resource_id"]
        scaled_resources = self.resource_abstraction.allocated_resources[new_resource_id]["resources"]
        self.assertEqual(scaled_resources["cpu"], "80%")  # 40% * 2.0 = 80%
        
        # Try to scale non-existent resource
        scale_result = self.resource_abstraction.scale_resources("non-existent-id", 2.0)
        self.assertEqual(scale_result["status"], "error")

    def test_get_resource_usage(self):
        """Test getting resource usage information"""
        # First allocate some resources
        resources1 = {"cpu": "30%", "memory": "1G"}
        resources2 = {"cpu": "20%", "memory": "2G"}
        
        allocation1 = self.resource_abstraction.allocate_resources(resources1)
        allocation2 = self.resource_abstraction.allocate_resources(resources2)
        
        resource_id1 = allocation1["resource_id"]
        resource_id2 = allocation2["resource_id"]
        
        # Get usage for specific resource
        usage1 = self.resource_abstraction.get_resource_usage(resource_id1)
        self.assertEqual(usage1["resources"], resources1)
        
        # Get overall usage
        overall_usage = self.resource_abstraction.get_resource_usage()
        self.assertEqual(overall_usage["total_allocations"], 2)
        self.assertIn("environments", overall_usage)
        self.assertIn("resources", overall_usage)

    def test_package_for_export(self):
        """Test packaging resources for export"""
        # First allocate resources
        resources = {"cpu": "50%", "memory": "2G"}
        allocation_result = self.resource_abstraction.allocate_resources(resources)
        resource_id = allocation_result["resource_id"]
        
        # Export as JSON
        json_export = self.resource_abstraction.package_for_export(resource_id, "json")
        self.assertIsInstance(json_export, str)
        
        # Verify JSON structure
        export_data = json.loads(json_export)
        self.assertIn("resource_configuration", export_data)
        self.assertIn("metadata", export_data)
        self.assertEqual(export_data["resource_configuration"]["resources"], resources)
        
        # Export as YAML
        yaml_export = self.resource_abstraction.package_for_export(resource_id, "yaml")
        self.assertIsInstance(yaml_export, str)
        
        # Try to export non-existent resource
        empty_export = self.resource_abstraction.package_for_export("non-existent-id")
        self.assertEqual(empty_export, "")


class TestDeploymentTemplate(unittest.TestCase):
    """Test cases for the DeploymentTemplate class"""

    def setUp(self):
        """Set up test fixtures"""
        self.template_manager = DeploymentTemplate()

    def test_init(self):
        """Test initialization of DeploymentTemplate"""
        self.assertIsInstance(self.template_manager, DeploymentTemplate)
        self.assertIsInstance(self.template_manager.templates, dict)
        self.assertGreater(len(self.template_manager.templates), 0)

    def test_get_template(self):
        """Test getting a deployment template"""
        # Get existing template
        aws_lambda_template = self.template_manager.get_template("aws_lambda")
        self.assertIsInstance(aws_lambda_template, dict)
        self.assertEqual(aws_lambda_template["type"], "serverless")
        self.assertEqual(aws_lambda_template["provider"], "aws")
        
        # Get non-existent template
        empty_template = self.template_manager.get_template("non-existent")
        self.assertEqual(empty_template, {})

    def test_customize_template(self):
        """Test customizing a deployment template"""
        # Customize existing template
        customizations = {
            "resources": {
                "memory": "256MB",
                "timeout": 60
            },
            "environment": {
                "variables": {
                    "DEBUG": "true"
                }
            }
        }
        
        customized = self.template_manager.customize_template("aws_lambda", customizations)
        
        # Verify customizations were applied
        self.assertEqual(customized["resources"]["memory"], "256MB")
        self.assertEqual(customized["resources"]["timeout"], 60)
        self.assertEqual(customized["environment"]["variables"]["DEBUG"], "true")
        
        # Original template values should be preserved
        self.assertEqual(customized["type"], "serverless")
        self.assertEqual(customized["provider"], "aws")
        
        # Customize non-existent template
        empty_customized = self.template_manager.customize_template("non-existent", customizations)
        self.assertEqual(empty_customized, {})

    def test_generate_deployment_files(self):
        """Test generating deployment files from a template"""
        template = self.template_manager.get_template("aws_lambda")
        output_dir = "/tmp/deployment"
        
        files = self.template_manager.generate_deployment_files(template, output_dir)
        
        # Verify expected files
        self.assertIsInstance(files, list)
        self.assertGreater(len(files), 0)
        self.assertIn(f"{output_dir}/serverless.yml", files)
        self.assertIn(f"{output_dir}/handler.py", files)


if __name__ == '__main__':
    unittest.main()