import unittest
from unittest.mock import MagicMock, patch
from src.tool_registry import ToolRegistry, ToolCategory
from src.tool_interface import ToolInterface


class MockTool(ToolInterface):
    def __init__(self, name, description, category=None):
        self.name = name
        self.description = description
        self.category = category
        
    def execute(self, parameters):
        return {"result": "mock_result"}
        
    def get_parameter_schema(self):
        return {"type": "object", "properties": {}}
        
    def get_result_schema(self):
        return {"type": "object", "properties": {}}


class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        # Create a fresh registry for each test
        self.registry = ToolRegistry()
        
        # Create some mock tools
        self.tool1 = MockTool("tool1", "Test tool 1", ToolCategory.DATA_PROCESSING)
        self.tool2 = MockTool("tool2", "Test tool 2", ToolCategory.COMMUNICATION)
        self.tool3 = MockTool("tool3", "Test tool 3", ToolCategory.UTILITY)
        
    def test_register_tool(self):
        # Register a tool
        self.registry.register_tool(self.tool1)
        
        # Check if the tool is registered
        self.assertIn("tool1", self.registry.get_tool_names())
        self.assertEqual(self.registry.get_tool("tool1"), self.tool1)
        
    def test_register_duplicate_tool(self):
        # Register a tool
        self.registry.register_tool(self.tool1)
        
        # Try to register a tool with the same name
        duplicate_tool = MockTool("tool1", "Duplicate tool")
        
        # This should raise a ValueError
        with self.assertRaises(ValueError):
            self.registry.register_tool(duplicate_tool)
            
    def test_unregister_tool(self):
        # Register a tool
        self.registry.register_tool(self.tool1)
        
        # Unregister the tool
        self.registry.unregister_tool("tool1")
        
        # Check if the tool is unregistered
        self.assertNotIn("tool1", self.registry.get_tool_names())
        with self.assertRaises(KeyError):
            self.registry.get_tool("tool1")
            
    def test_unregister_nonexistent_tool(self):
        # Try to unregister a tool that doesn't exist
        with self.assertRaises(KeyError):
            self.registry.unregister_tool("nonexistent_tool")
            
    def test_get_tools_by_category(self):
        # Register tools with different categories
        self.registry.register_tool(self.tool1)  # DATA_PROCESSING
        self.registry.register_tool(self.tool2)  # COMMUNICATION
        self.registry.register_tool(self.tool3)  # UTILITY
        
        # Get tools by category
        data_tools = self.registry.get_tools_by_category(ToolCategory.DATA_PROCESSING)
        comm_tools = self.registry.get_tools_by_category(ToolCategory.COMMUNICATION)
        util_tools = self.registry.get_tools_by_category(ToolCategory.UTILITY)
        
        # Check if the tools are correctly categorized
        self.assertEqual(len(data_tools), 1)
        self.assertEqual(data_tools[0], self.tool1)
        
        self.assertEqual(len(comm_tools), 1)
        self.assertEqual(comm_tools[0], self.tool2)
        
        self.assertEqual(len(util_tools), 1)
        self.assertEqual(util_tools[0], self.tool3)
        
    def test_search_tools(self):
        # Register tools
        self.registry.register_tool(self.tool1)
        self.registry.register_tool(self.tool2)
        self.registry.register_tool(self.tool3)
        
        # Search for tools by name
        results = self.registry.search_tools("tool1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.tool1)
        
        # Search for tools by description
        results = self.registry.search_tools("Test tool")
        self.assertEqual(len(results), 3)
        self.assertIn(self.tool1, results)
        self.assertIn(self.tool2, results)
        self.assertIn(self.tool3, results)
        
    def test_get_tool_metadata(self):
        # Register a tool
        self.registry.register_tool(self.tool1)
        
        # Get tool metadata
        metadata = self.registry.get_tool_metadata("tool1")
        
        # Check metadata
        self.assertEqual(metadata["name"], "tool1")
        self.assertEqual(metadata["description"], "Test tool 1")
        self.assertEqual(metadata["category"], ToolCategory.DATA_PROCESSING)
        self.assertIn("parameter_schema", metadata)
        self.assertIn("result_schema", metadata)
        
    def test_get_all_tools(self):
        # Register tools
        self.registry.register_tool(self.tool1)
        self.registry.register_tool(self.tool2)
        self.registry.register_tool(self.tool3)
        
        # Get all tools
        all_tools = self.registry.get_all_tools()
        
        # Check if all tools are returned
        self.assertEqual(len(all_tools), 3)
        self.assertIn(self.tool1, all_tools)
        self.assertIn(self.tool2, all_tools)
        self.assertIn(self.tool3, all_tools)


if __name__ == "__main__":
    unittest.main()