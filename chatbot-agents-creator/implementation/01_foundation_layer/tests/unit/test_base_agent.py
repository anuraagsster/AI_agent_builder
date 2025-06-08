import unittest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.agent_framework.base_agent import BaseAgent

class TestBaseAgent(unittest.TestCase):
    """Test cases for the BaseAgent class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'name': 'test_agent',
            'capabilities': {
                'test_capability': {
                    'param1': 'value1',
                    'param2': 'value2'
                }
            },
            'exportable': True,
            'owner_id': 'test_owner',
            'ownership_type': 'client'
        }
        self.agent = BaseAgent(self.config, agent_id='test-agent-id')
    
    def test_initialization(self):
        """Test agent initialization"""
        self.assertEqual(self.agent.agent_id, 'test-agent-id')
        self.assertEqual(self.agent.config, self.config)
        self.assertEqual(self.agent.owner_id, 'test_owner')
        self.assertEqual(self.agent.ownership_type, 'client')
        self.assertEqual(self.agent.exportable, True)
        self.assertEqual(self.agent.state['status'], 'created')
        
    def test_initialize_method(self):
        """Test the initialize method"""
        result = self.agent.initialize()
        self.assertTrue(result)
        self.assertEqual(self.agent.state['status'], 'initialized')
        self.assertIn('initialized_at', self.agent.state)
        self.assertIn('test_capability', self.agent.state['capabilities'])
        
    def test_register_capability(self):
        """Test capability registration"""
        result = self.agent.register_capability('new_capability', {'param': 'value'})
        self.assertTrue(result)
        self.assertIn('new_capability', self.agent.state['capabilities'])
        self.assertEqual(
            self.agent.state['capabilities']['new_capability']['parameters'],
            {'param': 'value'}
        )
        
    def test_has_capability(self):
        """Test capability checking"""
        self.agent.register_capability('test_capability')
        self.assertTrue(self.agent.has_capability('test_capability'))
        self.assertFalse(self.agent.has_capability('nonexistent_capability'))
        
    def test_execute_task_success(self):
        """Test successful task execution"""
        self.agent.initialize()
        
        # Mock the _execute_capability method
        self.agent._execute_capability = MagicMock(return_value={'result': 'success'})
        
        task = {
            'id': 'task-123',
            'type': 'test_capability',
            'data': {'input': 'test_input'}
        }
        
        result = self.agent.execute_task(task)
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['task_id'], 'task-123')
        self.assertIn('duration', result)
        self.assertEqual(self.agent.state['metrics']['tasks_completed'], 1)
        self.assertEqual(self.agent.state['metrics']['tasks_failed'], 0)
        self.assertGreater(self.agent.state['metrics']['avg_task_duration'], 0)
        
        # Verify the _execute_capability was called with correct parameters
        self.agent._execute_capability.assert_called_once_with('test_capability', task)
        
    def test_execute_task_missing_capability(self):
        """Test task execution with missing capability"""
        task = {
            'id': 'task-123',
            'type': 'nonexistent_capability',
            'data': {'input': 'test_input'}
        }
        
        result = self.agent.execute_task(task)
        
        self.assertEqual(result['status'], 'failed')
        self.assertIn('error', result)
        self.assertEqual(result['task_id'], 'task-123')
        
    def test_execute_task_failure(self):
        """Test task execution failure"""
        self.agent.initialize()
        
        # Mock the _execute_capability method to raise an exception
        self.agent._execute_capability = MagicMock(side_effect=Exception("Test error"))
        
        task = {
            'id': 'task-123',
            'type': 'test_capability',
            'data': {'input': 'test_input'}
        }
        
        result = self.agent.execute_task(task)
        
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['error'], 'Test error')
        self.assertEqual(result['task_id'], 'task-123')
        self.assertEqual(self.agent.state['metrics']['tasks_completed'], 0)
        self.assertEqual(self.agent.state['metrics']['tasks_failed'], 1)
        
    def test_report_status(self):
        """Test status reporting"""
        self.agent.initialize()
        status = self.agent.report_status()
        
        self.assertEqual(status['agent_id'], 'test-agent-id')
        self.assertEqual(status['status'], 'initialized')
        self.assertIn('test_capability', status['capabilities'])
        self.assertEqual(status['owner_id'], 'test_owner')
        self.assertEqual(status['ownership_type'], 'client')
        self.assertEqual(status['exportable'], True)
        
    def test_terminate(self):
        """Test agent termination"""
        self.agent.initialize()
        result = self.agent.terminate()
        
        self.assertTrue(result)
        self.assertEqual(self.agent.state['status'], 'terminated')
        self.assertIn('terminated_at', self.agent.state)
        
    def test_prepare_for_export(self):
        """Test agent export preparation"""
        self.agent.initialize()
        export_data = self.agent.prepare_for_export()
        
        self.assertEqual(export_data['agent_id'], 'test-agent-id')
        self.assertEqual(export_data['agent_type'], 'BaseAgent')
        self.assertIn('capabilities', export_data)
        self.assertIn('configuration', export_data)
        self.assertEqual(export_data['owner_id'], 'test_owner')
        self.assertEqual(export_data['ownership_type'], 'client')
        self.assertIn('exported_at', export_data)
        
    def test_prepare_for_export_not_exportable(self):
        """Test export preparation for non-exportable agent"""
        config = self.config.copy()
        config['exportable'] = False
        agent = BaseAgent(config)
        
        with self.assertRaises(ValueError):
            agent.prepare_for_export()
            
    def test_update_metrics(self):
        """Test metrics update"""
        self.agent._update_metrics(True, 1.5)
        self.assertEqual(self.agent.state['metrics']['tasks_completed'], 1)
        self.assertEqual(self.agent.state['metrics']['tasks_failed'], 0)
        self.assertEqual(self.agent.state['metrics']['avg_task_duration'], 1.5)
        
        self.agent._update_metrics(True, 2.5)
        self.assertEqual(self.agent.state['metrics']['tasks_completed'], 2)
        self.assertEqual(self.agent.state['metrics']['avg_task_duration'], 2.0)
        
        self.agent._update_metrics(False, 1.0)
        self.assertEqual(self.agent.state['metrics']['tasks_completed'], 2)
        self.assertEqual(self.agent.state['metrics']['tasks_failed'], 1)
        self.assertEqual(self.agent.state['metrics']['avg_task_duration'], 5/3)

if __name__ == '__main__':
    unittest.main()