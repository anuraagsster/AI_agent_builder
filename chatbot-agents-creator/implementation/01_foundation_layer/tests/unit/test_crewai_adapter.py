import unittest
from unittest.mock import patch, MagicMock
import sys
import importlib
from datetime import datetime

# Add path to src directory
sys.path.append('chatbot-agents-creator/implementation/01_foundation_layer/src')

from agent_framework.framework_adapters.crewai_adapter import CrewAIAdapter

class TestCrewAIAdapter(unittest.TestCase):
    
    def setUp(self):
        # Create a mock config
        self.config = {
            'verbose': True
        }
        
    @patch('importlib.import_module')
    def test_init_crewai_available(self, mock_import):
        # Setup mock
        mock_import.return_value = MagicMock()
        
        # Create adapter
        adapter = CrewAIAdapter(self.config)
        
        # Verify
        self.assertTrue(adapter._crewai_available)
        mock_import.assert_called_once_with('crewai')
        
    @patch('importlib.import_module')
    def test_init_crewai_not_available(self, mock_import):
        # Setup mock to raise ImportError
        mock_import.side_effect = ImportError("No module named 'crewai'")
        
        # Create adapter
        adapter = CrewAIAdapter(self.config)
        
        # Verify
        self.assertFalse(adapter._crewai_available)
        
    @patch('importlib.import_module')
    def test_create_crewai_agent(self, mock_import):
        # Setup mocks
        mock_crewai = MagicMock()
        mock_agent_class = MagicMock()
        mock_crewai.Agent = mock_agent_class
        mock_import.return_value = mock_crewai
        
        # Create adapter
        adapter = CrewAIAdapter(self.config)
        adapter.crewai_agent_class = mock_agent_class
        
        # Test data
        agent_config = {
            'agent_id': 'test-agent-123',
            'name': 'Test Agent',
            'role': 'Assistant',
            'goal': 'Help with testing',
            'description': 'A test agent',
            'owner_id': 'test-owner',
            'ownership_type': 'system',
            'exportable': True
        }
        
        # Call method
        result = adapter.create_crewai_agent(agent_config)
        
        # Verify
        mock_agent_class.assert_called_once()
        self.assertEqual(result.original_agent_id, 'test-agent-123')
        self.assertEqual(result.owner_id, 'test-owner')
        self.assertEqual(result.ownership_type, 'system')
        self.assertEqual(result.exportable, True)
        
    @patch('importlib.import_module')
    def test_convert_task(self, mock_import):
        # Setup mocks
        mock_crewai = MagicMock()
        mock_task_class = MagicMock()
        mock_crewai.Task = mock_task_class
        mock_import.return_value = mock_crewai
        
        # Create adapter
        adapter = CrewAIAdapter(self.config)
        adapter.crewai_task_class = mock_task_class
        
        # Test data
        task = {
            'id': 'test-task-123',
            'type': 'research',
            'description': 'Research CrewAI',
            'expected_output': 'A summary of CrewAI',
            'owner_id': 'test-owner'
        }
        
        # Call method
        result = adapter.convert_task(task)
        
        # Verify
        mock_task_class.assert_called_once()
        self.assertEqual(result.original_task_id, 'test-task-123')
        self.assertEqual(result.owner_id, 'test-owner')
        
    def test_process_result_string(self):
        # Create adapter
        adapter = CrewAIAdapter(self.config)
        
        # Test data
        result = "Task completed successfully"
        
        # Call method
        processed = adapter.process_result(result)
        
        # Verify
        self.assertEqual(processed['status'], 'completed')
        self.assertEqual(processed['result'], "Task completed successfully")
        self.assertTrue('timestamp' in processed)
        
    def test_process_result_dict(self):
        # Create adapter
        adapter = CrewAIAdapter(self.config)
        
        # Test data
        result = {
            'output': 'Task output',
            'metadata': {'key': 'value'}
        }
        
        # Call method
        processed = adapter.process_result(result)
        
        # Verify
        self.assertEqual(processed['status'], 'completed')
        self.assertEqual(processed['output'], 'Task output')
        self.assertEqual(processed['metadata'], {'key': 'value'})
        self.assertTrue('timestamp' in processed)
        
    @patch('importlib.import_module')
    def test_create_crew(self, mock_import):
        # Setup mocks
        mock_crewai = MagicMock()
        mock_crew_class = MagicMock()
        mock_crewai.Crew = mock_crew_class
        mock_import.return_value = mock_crewai
        
        # Create adapter
        adapter = CrewAIAdapter(self.config)
        adapter.crewai_crew_class = mock_crew_class
        
        # Test data
        mock_agent1 = MagicMock()
        mock_agent1.owner_id = 'owner1'
        mock_agent1.exportable = True
        
        mock_agent2 = MagicMock()
        mock_agent2.owner_id = 'owner1'
        mock_agent2.exportable = True
        
        mock_task = MagicMock()
        
        # Call method
        result = adapter.create_crew([mock_agent1, mock_agent2], [mock_task])
        
        # Verify
        mock_crew_class.assert_called_once()
        
    @patch('importlib.import_module')
    def test_validate_ownership_compatibility_success(self, mock_import):
        # Create adapter
        adapter = CrewAIAdapter(self.config)
        
        # Test data - same owner
        mock_agent1 = MagicMock()
        mock_agent1.owner_id = 'owner1'
        mock_agent1.exportable = True
        
        mock_agent2 = MagicMock()
        mock_agent2.owner_id = 'owner1'
        mock_agent2.exportable = True
        
        # Should not raise exception
        adapter._validate_ownership_compatibility([mock_agent1, mock_agent2])
        
        # Test data - different owners but exportable
        mock_agent3 = MagicMock()
        mock_agent3.owner_id = 'owner2'
        mock_agent3.exportable = True
        
        # Should not raise exception
        adapter._validate_ownership_compatibility([mock_agent1, mock_agent3])
        
    @patch('importlib.import_module')
    def test_validate_ownership_compatibility_failure(self, mock_import):
        # Create adapter
        adapter = CrewAIAdapter(self.config)
        
        # Test data - different owners, one not exportable
        mock_agent1 = MagicMock()
        mock_agent1.owner_id = 'owner1'
        mock_agent1.exportable = False
        mock_agent1.name = 'Agent1'
        
        mock_agent2 = MagicMock()
        mock_agent2.owner_id = 'owner2'
        mock_agent2.exportable = True
        mock_agent2.name = 'Agent2'
        
        # Should raise exception
        with self.assertRaises(ValueError):
            adapter._validate_ownership_compatibility([mock_agent1, mock_agent2])
            
    def test_prepare_for_export(self):
        # Create adapter
        adapter = CrewAIAdapter(self.config)
        
        # Test data
        mock_agent = MagicMock()
        mock_agent.exportable = True
        mock_agent.original_agent_id = 'test-agent-123'
        mock_agent.name = 'Test Agent'
        mock_agent.role = 'Assistant'
        mock_agent.goal = 'Help with testing'
        mock_agent.backstory = 'A test agent'
        mock_agent.owner_id = 'test-owner'
        mock_agent.ownership_type = 'client'
        
        # Call method
        result = adapter.prepare_for_export(mock_agent)
        
        # Verify
        self.assertEqual(result['agent_id'], 'test-agent-123')
        self.assertEqual(result['name'], 'Test Agent')
        self.assertEqual(result['role'], 'Assistant')
        self.assertEqual(result['goal'], 'Help with testing')
        self.assertEqual(result['backstory'], 'A test agent')
        self.assertEqual(result['owner_id'], 'test-owner')
        self.assertEqual(result['ownership_type'], 'client')
        self.assertEqual(result['exportable'], True)
        self.assertEqual(result['framework'], 'crewai')
        self.assertTrue('exported_at' in result)
        
    def test_prepare_for_export_not_exportable(self):
        # Create adapter
        adapter = CrewAIAdapter(self.config)
        
        # Test data
        mock_agent = MagicMock()
        mock_agent.exportable = False
        
        # Should raise exception
        with self.assertRaises(ValueError):
            adapter.prepare_for_export(mock_agent)

if __name__ == '__main__':
    unittest.main()