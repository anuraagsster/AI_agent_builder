import unittest
from src.architecture.component_registry import ComponentRegistry, ExtensionSystem, ComponentMetadata

class TestComponentRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ComponentRegistry()
        
    def test_register_and_get(self):
        # Create a mock component
        mock_component = {"type": "test"}
        component_id = "test_component"
        
        # Register the component
        self.registry.register(component_id, mock_component)
        
        # Verify the component was registered
        self.assertIn(component_id, self.registry.list_components())
        
        # Get the component
        retrieved_component = self.registry.get(component_id)
        self.assertEqual(retrieved_component, mock_component)
        
    def test_register_with_metadata(self):
        # Create a mock component and metadata
        mock_component = {"type": "test"}
        component_id = "test_component"
        metadata = ComponentMetadata(
            name="Test Component",
            version="1.2.3",
            description="A test component",
            tags=["test", "mock"]
        )
        
        # Register the component with metadata
        self.registry.register(component_id, mock_component, metadata)
        
        # Verify the metadata was stored
        retrieved_metadata = self.registry.get_metadata(component_id)
        self.assertEqual(retrieved_metadata.name, "Test Component")
        self.assertEqual(retrieved_metadata.version, "1.2.3")
        self.assertEqual(retrieved_metadata.description, "A test component")
        self.assertEqual(retrieved_metadata.tags, ["test", "mock"])
        
    def test_list_components(self):
        # Register multiple components
        self.registry.register("comp1", {"type": "test1"})
        self.registry.register("comp2", {"type": "test2"})
        self.registry.register("comp3", {"type": "test3"})
        
        # List components
        components = self.registry.list_components()
        
        # Verify all components are listed
        self.assertEqual(len(components), 3)
        self.assertIn("comp1", components)
        self.assertIn("comp2", components)
        self.assertIn("comp3", components)
        
    def test_remove_component(self):
        # Register a component
        component_id = "test_component"
        self.registry.register(component_id, {"type": "test"})
        
        # Verify it exists
        self.assertIn(component_id, self.registry.list_components())
        
        # Remove the component
        result = self.registry.remove(component_id)
        
        # Verify removal was successful
        self.assertTrue(result)
        self.assertNotIn(component_id, self.registry.list_components())
        
    def test_get_components_by_tag(self):
        # Register components with different tags
        self.registry.register("comp1", {"type": "test1"},
                              ComponentMetadata(name="Comp1", version="1.0", description="Test", tags=["tag1", "tag2"]))
        self.registry.register("comp2", {"type": "test2"},
                              ComponentMetadata(name="Comp2", version="1.0", description="Test", tags=["tag2", "tag3"]))
        self.registry.register("comp3", {"type": "test3"},
                              ComponentMetadata(name="Comp3", version="1.0", description="Test", tags=["tag1", "tag3"]))
        
        # Get components by tag
        tag1_components = self.registry.get_components_by_tag("tag1")
        tag2_components = self.registry.get_components_by_tag("tag2")
        tag3_components = self.registry.get_components_by_tag("tag3")
        
        # Verify correct components are returned
        self.assertEqual(len(tag1_components), 2)
        self.assertEqual(len(tag2_components), 2)
        self.assertEqual(len(tag3_components), 2)
        
    def test_dependency_resolution(self):
        # Register components with dependencies
        self.registry.register("comp3", {"type": "test3"},
                              ComponentMetadata(name="Comp3", version="1.0", description="Test", dependencies=["comp1", "comp2"]))
        self.registry.register("comp2", {"type": "test2"},
                              ComponentMetadata(name="Comp2", version="1.0", description="Test", dependencies=["comp1"]))
        self.registry.register("comp1", {"type": "test1"},
                              ComponentMetadata(name="Comp1", version="1.0", description="Test"))
        
        # Resolve dependencies
        order = self.registry._resolve_dependencies()
        
        # Verify correct order
        self.assertEqual(order.index("comp1"), 0)  # comp1 should be first
        self.assertTrue(order.index("comp2") > order.index("comp1"))  # comp2 should be after comp1
        self.assertTrue(order.index("comp3") > order.index("comp2"))  # comp3 should be after comp2
        
class TestExtensionSystem(unittest.TestCase):
    def setUp(self):
        self.registry = ComponentRegistry()
        self.extension_system = ExtensionSystem(self.registry)
        
    def test_register_extension_point(self):
        # Define an interface class
        class TestInterface:
            def test_method(self):
                pass
                
        # Register extension point
        self.extension_system.register_extension_point("test_point", TestInterface)
        
        # Verify no extensions yet
        extensions = self.extension_system.get_extensions("test_point")
        self.assertEqual(len(extensions), 0)
        
    def test_register_extension(self):
        # Define an interface and implementation
        class TestInterface:
            def test_method(self):
                pass
                
        class TestExtension(TestInterface):
            def test_method(self):
                return "test"
                
        # Register extension point and extension
        self.extension_system.register_extension_point("test_point", TestInterface)
        extension = TestExtension()
        self.extension_system.register_extension("test_point", extension)
        
        # Get extensions
        extensions = self.extension_system.get_extensions("test_point")
        
        # Verify extension was registered
        self.assertEqual(len(extensions), 1)
        self.assertIs(extensions[0], extension)
        
    def test_remove_extension(self):
        # Define an interface and implementation
        class TestInterface:
            def test_method(self):
                pass
                
        class TestExtension(TestInterface):
            def test_method(self):
                return "test"
                
        # Register extension point and extension
        self.extension_system.register_extension_point("test_point", TestInterface)
        extension = TestExtension()
        self.extension_system.register_extension("test_point", extension, "test_ext")
        
        # Verify extension exists
        extensions = self.extension_system.get_extensions("test_point")
        self.assertEqual(len(extensions), 1)
        
        # Remove extension
        result = self.extension_system.remove_extension("test_point", "test_ext")
        
        # Verify extension was removed
        self.assertTrue(result)
        extensions = self.extension_system.get_extensions("test_point")
        self.assertEqual(len(extensions), 0)
        
    def test_extension_type_checking(self):
        # Define an interface and wrong implementation
        class TestInterface:
            def test_method(self):
                pass
                
        class WrongExtension:
            def different_method(self):
                return "test"
                
        # Register extension point
        self.extension_system.register_extension_point("test_point", TestInterface)
        
        # Try to register extension of wrong type
        extension = WrongExtension()
        with self.assertRaises(TypeError):
            self.extension_system.register_extension("test_point", extension)

if __name__ == "__main__":
    unittest.main()