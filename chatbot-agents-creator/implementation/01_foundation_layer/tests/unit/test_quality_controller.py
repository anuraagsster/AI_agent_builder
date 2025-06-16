import unittest
from unittest.mock import MagicMock
from src.workload_management.quality_controller import QualityController

class TestQualityController(unittest.TestCase):
    def setUp(self):
        self.controller = QualityController()

    def test_route_task_to_best_agent(self):
        # Mock feedback history for two agents
        self.controller.get_agent_feedback_history = MagicMock(side_effect=lambda agent_id: [
            {'feedback': {'task_type': 'task1', 'score': 0.8}},
            {'feedback': {'task_type': 'task1', 'score': 0.9}}
        ] if agent_id == 'agent1' else [
            {'feedback': {'task_type': 'task1', 'score': 0.7}}
        ])
        best_agent = self.controller.route_task_to_best_agent('task1', ['agent1', 'agent2'])
        self.assertEqual(best_agent, 'agent1')

    def test_apply_continuous_improvement(self):
        # This is a stub, so we just ensure it doesn't raise an error
        self.controller.apply_continuous_improvement('agent1')

    def test_client_quality_standards(self):
        standards = {'threshold': 0.8}
        self.controller.set_client_quality_standards('client1', standards)
        retrieved = self.controller.get_client_quality_standards('client1')
        self.assertEqual(retrieved, standards)

    def test_record_anonymized_feedback(self):
        self.controller.record_anonymized_feedback('task1', 'Great job!', 5)
        self.assertIn('task1', self.controller.anonymized_feedback)
        self.assertEqual(len(self.controller.anonymized_feedback['task1']), 1)
        self.assertEqual(self.controller.anonymized_feedback['task1'][0]['content'], 'Great job!')
        self.assertEqual(self.controller.anonymized_feedback['task1'][0]['rating'], 5)

    def test_generate_quality_metrics_dashboard(self):
        # Mock feedback history and anonymized feedback
        self.controller.feedback_history = {
            'task1': [
                {'agent_id': 'agent1', 'score': 0.8, 'client_id': 'client1'},
                {'agent_id': 'agent2', 'score': 0.7, 'client_id': 'client1'}
            ]
        }
        self.controller.anonymized_feedback = {
            'task1': [{'content': 'Great job!', 'rating': 5}]
        }
        self.controller.quality_metrics = {'metric1': {'evaluation_function': lambda x, y: 0.8, 'threshold': 0.7}}
        
        # Test dashboard generation for agent1
        dashboard = self.controller.generate_quality_metrics_dashboard(agent_id='agent1')
        self.assertEqual(dashboard['overall_score'], 0.8)
        self.assertEqual(dashboard['feedback_count'], 1)
        self.assertEqual(dashboard['anonymized_feedback_count'], 1)
        
        # Test dashboard generation for client1
        dashboard = self.controller.generate_quality_metrics_dashboard(client_id='client1')
        self.assertEqual(dashboard['overall_score'], 0.75)
        self.assertEqual(dashboard['feedback_count'], 2)
        self.assertEqual(dashboard['anonymized_feedback_count'], 1)

if __name__ == '__main__':
    unittest.main() 