import unittest
from unittest.mock import MagicMock
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from src.architecture.component_registry import ComponentRegistry, ComponentMetadata, ExtensionSystem


class TestOwnershipMetadata(unittest.TestCase):
    """Test cases for ownership metadata functionality"""

    def setUp(self):
        """Set up test environment"""
        self.registry = ComponentRegistry()
        
        # Create mock components with different ownership
        self.system_component = MagicMock()
        self.client1_component = MagicMock()
        self.client2_component = MagicMock()
        
        # Set up prepare_for_export method on client component
        self.client1_component.prepare_for_export = MagicMock(return_value={
            "component_id": "client1_component",
            "exported_data": "test_data"
        })
        
        # Register components with metadata
        self.registry.register(
            "system_component",
            self.system_component,
            ComponentMetadata(
                name="system_component",
                version="1.0.0",
                description="System component"
                # No owner_id means system component
            )
        )
        
        self.registry.register(
            "client1_component",
            self.client1_component,
            ComponentMetadata(
                name="client1_component",
                version="1.0.0",
                description="Client 1 component",
                owner_id="client1",
                exportable=True
            )
        )
        
        self.registry.register(
            "client2_component",
            self.client2_component,
            ComponentMetadata(
                name="client2_component",
                version="1.0.0",
                description="Client 2 component",
                owner_id="client2",
                exportable=True
            )
        )
        
        # Set up extension system
        self.extension_system = ExtensionSystem(self.registry)
        
        # Register extension point
        class TestInterface:
            def test_method(self):
                pass
                
        self.extension_system.register_extension_point("test_point", TestInterface)
        
        # Create mock extensions
        self.client1_extension = MagicMock(spec=TestInterface)
        self.client2_extension = MagicMock(spec=TestInterface)
        
        # Register extensions with ownership
        self.extension_system.register_extension(
            "test_point",
            self.client1_extension,
            "client1_extension",
            owner_id="client1"
        )
        
        self.extension_system.register_extension(
            "test_point",
            self.client2_extension,
            "client2_extension",
            owner_id="client2"
        )

    def test_get_components_by_owner(self):
        """Test retrieving components by owner"""
        # Get client1 components
        client1_components = self.registry.get_components_by_owner("client1")
        self.assertEqual(len(client1_components), 1)
        self.assertEqual(client1_components[0], self.client1_component)
        
        # Get client2 components
        client2_components = self.registry.get_components_by_owner("client2")
        self.assertEqual(len(client2_components), 1)
        self.assertEqual(client2_components[0], self.client2_component)
        
        # Get non-existent client components
        client3_components = self.registry.get_components_by_owner("client3")
        self.assertEqual(len(client3_components), 0)

    def test_access_component(self):
        """Test access control based on ownership"""
        # System component can be accessed by anyone
        self.assertEqual(
            self.registry.access_component("system_component", "client1"),
            self.system_component
        )
        
        # Client component can be accessed by its owner
        self.assertEqual(
            self.registry.access_component("client1_component", "client1"),
            self.client1_component
        )
        
        # Client component cannot be accessed by other clients
        self.assertIsNone(
            self.registry.access_component("client1_component", "client2")
        )
        
        # Non-existent component returns None
        self.assertIsNone(
            self.registry.access_component("non_existent", "client1")
        )

    def test_export_component(self):
        """Test exporting a component"""
        # Export client component
        export_data = self.registry.export_component("client1_component")
        self.assertEqual(export_data["component_id"], "client1_component")
        self.assertEqual(export_data["exported_data"], "test_data")
        
        # Try to export system component (not exportable)
        export_data = self.registry.export_component("system_component")
        self.assertEqual(export_data, {})
        
        # Try to export non-existent component
        export_data = self.registry.export_component("non_existent")
        self.assertEqual(export_data, {})

    def test_get_extensions_by_owner(self):
        """Test retrieving extensions by owner"""
        # Get client1 extensions
        client1_extensions = self.extension_system.get_extensions_by_owner("test_point", "client1")
        self.assertEqual(len(client1_extensions), 1)
        self.assertEqual(client1_extensions[0], self.client1_extension)
        
        # Get client2 extensions
        client2_extensions = self.extension_system.get_extensions_by_owner("test_point", "client2")
        self.assertEqual(len(client2_extensions), 1)
        self.assertEqual(client2_extensions[0], self.client2_extension)
        
        # Get non-existent client extensions
        client3_extensions = self.extension_system.get_extensions_by_owner("test_point", "client3")
        self.assertEqual(len(client3_extensions), 0)

    def test_export_extensions(self):
        """Test exporting extensions by owner"""
        # Mock export_component to return test data
        self.registry.export_component = MagicMock(return_value={"test": "data"})
        
        # Export client1 extensions
        export_data = self.extension_system.export_extensions("client1")
        self.assertIn("test_point", export_data)
        self.assertIn("client1_extension", export_data["test_point"])
        
        # Export non-existent client extensions
        export_data = self.extension_system.export_extensions("client3")
        self.assertEqual(export_data, {})


if __name__ == '__main__':
    unittest.main()