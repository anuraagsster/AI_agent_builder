"""
Unit tests for the Alert Router component
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

from src.monitoring.alert_router import (
    AlertRouter, Alert, AlertDestination, AlertSeverity, AlertType
)

class TestAlertRouter(unittest.TestCase):
    """Test cases for AlertRouter"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'use_aws': False,  # Disable AWS for unit tests
            'max_history_size': 100
        }
        self.router = AlertRouter(config=self.config)
        
    def test_alert_creation(self):
        """Test creating an alert"""
        alert = self.router.create_alert(
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            title="Test Alert",
            message="This is a test alert",
            source="test_source",
            client_id="test_client"
        )
        
        # Verify alert was created correctly
        self.assertIsInstance(alert, Alert)
        self.assertEqual(alert.type, AlertType.SYSTEM_ERROR)
        self.assertEqual(alert.severity, AlertSeverity.ERROR)
        self.assertEqual(alert.title, "Test Alert")
        self.assertEqual(alert.message, "This is a test alert")
        self.assertEqual(alert.source, "test_source")
        self.assertEqual(alert.client_id, "test_client")
        self.assertIsInstance(alert.timestamp, datetime)
        self.assertIsInstance(alert.id, str)
        
    def test_add_destination(self):
        """Test adding an alert destination"""
        destination = AlertDestination(
            name="test_email",
            type="email",
            config={
                'to_addresses': ['test@example.com'],
                'from_address': 'alerts@example.com'
            }
        )
        
        self.router.add_destination(destination)
        
        # Verify destination was added
        self.assertIn("test_email", self.router.destinations)
        self.assertEqual(self.router.destinations["test_email"], destination)
        
    def test_remove_destination(self):
        """Test removing an alert destination"""
        destination = AlertDestination(
            name="test_email",
            type="email",
            config={}
        )
        
        self.router.add_destination(destination)
        self.assertIn("test_email", self.router.destinations)
        
        self.router.remove_destination("test_email")
        self.assertNotIn("test_email", self.router.destinations)
        
    def test_add_routing_rule(self):
        """Test adding a routing rule"""
        rule = {
            'name': 'test_rule',
            'conditions': {
                'severity': [AlertSeverity.CRITICAL],
                'type': [AlertType.SECURITY_BREACH]
            },
            'destinations': ['admin_email'],
            'priority': 1
        }
        
        self.router.add_routing_rule(rule)
        
        # Verify rule was added
        self.assertIn(rule, self.router.routing_rules)
        
    def test_remove_routing_rule(self):
        """Test removing a routing rule"""
        rule = {
            'name': 'test_rule',
            'conditions': {},
            'destinations': ['admin_email'],
            'priority': 1
        }
        
        self.router.add_routing_rule(rule)
        self.assertIn(rule, self.router.routing_rules)
        
        self.router.remove_routing_rule("test_rule")
        self.assertNotIn(rule, self.router.routing_rules)
        
    def test_rule_matching(self):
        """Test routing rule matching"""
        # Clear default rules for this test
        self.router.routing_rules = []
        
        # Create a rule for critical security alerts
        rule = {
            'name': 'critical_security',
            'conditions': {
                'severity': [AlertSeverity.CRITICAL],
                'type': [AlertType.SECURITY_BREACH]
            },
            'destinations': ['admin_email'],
            'priority': 1
        }
        
        self.router.add_routing_rule(rule)
        
        # Create matching alert
        alert = Alert(
            id="test_alert",
            type=AlertType.SECURITY_BREACH,
            severity=AlertSeverity.CRITICAL,
            title="Security Breach",
            message="Unauthorized access detected",
            source="security_monitor",
            timestamp=datetime.now(),
            metadata={}
        )
        
        # Test rule matching
        matching_rules = self.router._find_matching_rules(alert)
        self.assertEqual(len(matching_rules), 1)
        self.assertEqual(matching_rules[0]['name'], 'critical_security')
        
        # Test non-matching alert
        non_matching_alert = Alert(
            id="test_alert2",
            type=AlertType.RESOURCE_UTILIZATION,
            severity=AlertSeverity.WARNING,
            title="High CPU Usage",
            message="CPU usage is high",
            source="resource_monitor",
            timestamp=datetime.now(),
            metadata={}
        )
        
        matching_rules = self.router._find_matching_rules(non_matching_alert)
        self.assertEqual(len(matching_rules), 0)
        
    def test_client_specific_routing(self):
        """Test client-specific alert routing"""
        # Clear default rules for this test
        self.router.routing_rules = []
        
        # Create a rule for client-specific alerts
        rule = {
            'name': 'client_alerts',
            'conditions': {
                'client_id': 'not_null'
            },
            'destinations': ['client_notifications'],
            'priority': 1
        }
        
        self.router.add_routing_rule(rule)
        
        # Create client-specific alert
        alert = Alert(
            id="client_alert",
            type=AlertType.CLIENT_SPECIFIC,
            severity=AlertSeverity.WARNING,
            title="Client Issue",
            message="Client-specific problem detected",
            source="client_monitor",
            timestamp=datetime.now(),
            metadata={},
            client_id="client_123"
        )
        
        # Test rule matching
        matching_rules = self.router._find_matching_rules(alert)
        self.assertEqual(len(matching_rules), 1)
        self.assertEqual(matching_rules[0]['name'], 'client_alerts')
        
        # Test non-client alert
        non_client_alert = Alert(
            id="system_alert",
            type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            title="System Error",
            message="System error occurred",
            source="system_monitor",
            timestamp=datetime.now(),
            metadata={}
        )
        
        matching_rules = self.router._find_matching_rules(non_client_alert)
        self.assertEqual(len(matching_rules), 0)
        
    def test_destination_filtering(self):
        """Test destination filtering"""
        # Create destination with filters
        destination = AlertDestination(
            name="filtered_email",
            type="email",
            config={},
            filters={
                'min_severity': AlertSeverity.ERROR,
                'types': [AlertType.SYSTEM_ERROR, AlertType.SECURITY_BREACH]
            }
        )
        
        # Test alert that passes filters
        passing_alert = Alert(
            id="passing_alert",
            type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.CRITICAL,
            title="Critical System Error",
            message="Critical error occurred",
            source="system_monitor",
            timestamp=datetime.now(),
            metadata={}
        )
        
        self.assertTrue(self.router._check_destination_filters(passing_alert, destination))
        
        # Test alert that fails severity filter
        low_severity_alert = Alert(
            id="low_severity_alert",
            type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.WARNING,
            title="Warning",
            message="Warning message",
            source="system_monitor",
            timestamp=datetime.now(),
            metadata={}
        )
        
        self.assertFalse(self.router._check_destination_filters(low_severity_alert, destination))
        
        # Test alert that fails type filter
        wrong_type_alert = Alert(
            id="wrong_type_alert",
            type=AlertType.RESOURCE_UTILIZATION,
            severity=AlertSeverity.ERROR,
            title="Resource Issue",
            message="Resource issue",
            source="resource_monitor",
            timestamp=datetime.now(),
            metadata={}
        )
        
        self.assertFalse(self.router._check_destination_filters(wrong_type_alert, destination))
        
    @patch('requests.post')
    def test_slack_notification(self, mock_post):
        """Test Slack notification sending"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Create Slack destination
        destination = AlertDestination(
            name="test_slack",
            type="slack",
            config={
                'webhook_url': 'https://hooks.slack.com/test'
            }
        )
        
        # Create test alert
        alert = Alert(
            id="test_alert",
            type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            title="Test Error",
            message="Test error message",
            source="test_source",
            timestamp=datetime.now(),
            metadata={}
        )
        
        # Send to Slack
        result = self.router._send_slack(alert, destination)
        
        # Verify result
        self.assertEqual(result['status'], 'sent')
        mock_post.assert_called_once()
        
        # Verify Slack message format
        call_args = mock_post.call_args
        slack_message = call_args[1]['json']
        self.assertIn('attachments', slack_message)
        self.assertEqual(len(slack_message['attachments']), 1)
        
        attachment = slack_message['attachments'][0]
        self.assertEqual(attachment['title'], '[ERROR] Test Error')
        self.assertEqual(attachment['text'], 'Test error message')
        
    @patch('boto3.client')
    def test_sns_notification(self, mock_boto3_client):
        """Test SNS notification sending"""
        # Mock SNS client
        mock_sns = MagicMock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-id'}
        mock_boto3_client.return_value = mock_sns
        
        # Initialize router with AWS enabled
        aws_config = {'use_aws': True, 'aws_region': 'us-east-1'}
        aws_router = AlertRouter(config=aws_config)
        
        # Create SNS destination
        destination = AlertDestination(
            name="test_sns",
            type="sns",
            config={
                'topic_arn': 'arn:aws:sns:us-east-1:123456789012:test-topic'
            }
        )
        
        # Create test alert
        alert = Alert(
            id="test_alert",
            type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            title="Test Error",
            message="Test error message",
            source="test_source",
            timestamp=datetime.now(),
            metadata={}
        )
        
        # Send to SNS
        result = aws_router._send_sns(alert, destination)
        
        # Verify result
        self.assertEqual(result['status'], 'sent')
        self.assertEqual(result['message_id'], 'test-message-id')
        mock_sns.publish.assert_called_once()
        
    def test_alert_history(self):
        """Test alert history functionality"""
        # Create several alerts
        alert1 = self.router.create_alert(
            AlertType.SYSTEM_ERROR,
            AlertSeverity.ERROR,
            "Error 1",
            "First error",
            "source1"
        )
        
        alert2 = self.router.create_alert(
            AlertType.RESOURCE_UTILIZATION,
            AlertSeverity.WARNING,
            "Warning 1",
            "First warning",
            "source2",
            client_id="client1"
        )
        
        alert3 = self.router.create_alert(
            AlertType.SECURITY_BREACH,
            AlertSeverity.CRITICAL,
            "Critical 1",
            "First critical",
            "source3"
        )
        
        # Test getting all history
        history = self.router.get_alert_history()
        self.assertEqual(len(history), 3)
        
        # Test filtering by severity
        error_alerts = self.router.get_alert_history(severity=AlertSeverity.ERROR)
        self.assertEqual(len(error_alerts), 1)
        self.assertEqual(error_alerts[0].id, alert1.id)
        
        # Test filtering by type
        resource_alerts = self.router.get_alert_history(alert_type=AlertType.RESOURCE_UTILIZATION)
        self.assertEqual(len(resource_alerts), 1)
        self.assertEqual(resource_alerts[0].id, alert2.id)
        
        # Test filtering by client
        client_alerts = self.router.get_alert_history(client_id="client1")
        self.assertEqual(len(client_alerts), 1)
        self.assertEqual(client_alerts[0].id, alert2.id)
        
    def test_alert_statistics(self):
        """Test alert statistics functionality"""
        # Create alerts with different severities and types
        self.router.create_alert(
            AlertType.SYSTEM_ERROR,
            AlertSeverity.ERROR,
            "Error 1",
            "Error message",
            "source1"
        )
        
        self.router.create_alert(
            AlertType.SYSTEM_ERROR,
            AlertSeverity.ERROR,
            "Error 2",
            "Error message 2",
            "source1"
        )
        
        self.router.create_alert(
            AlertType.RESOURCE_UTILIZATION,
            AlertSeverity.WARNING,
            "Warning 1",
            "Warning message",
            "source2",
            client_id="client1"
        )
        
        self.router.create_alert(
            AlertType.SECURITY_BREACH,
            AlertSeverity.CRITICAL,
            "Critical 1",
            "Critical message",
            "source3"
        )
        
        # Get statistics
        stats = self.router.get_alert_statistics(hours=24)
        
        # Verify statistics
        self.assertEqual(stats['total_alerts'], 4)
        self.assertEqual(stats['by_severity']['error'], 2)
        self.assertEqual(stats['by_severity']['warning'], 1)
        self.assertEqual(stats['by_severity']['critical'], 1)
        self.assertEqual(stats['by_type']['system_error'], 2)
        self.assertEqual(stats['by_type']['resource_utilization'], 1)
        self.assertEqual(stats['by_type']['security_breach'], 1)
        self.assertEqual(stats['by_client']['client1'], 1)
        self.assertEqual(stats['by_client']['unknown'], 3)
        
    def test_history_size_limit(self):
        """Test that alert history respects size limits"""
        # Create more alerts than the max history size
        max_size = 5
        self.router.max_history_size = max_size
        
        for i in range(max_size + 3):
            self.router.create_alert(
                AlertType.SYSTEM_ERROR,
                AlertSeverity.ERROR,
                f"Error {i}",
                f"Error message {i}",
                "source1"
            )
        
        # Verify history size is limited
        self.assertEqual(len(self.router.alert_history), max_size)
        
        # Verify only the most recent alerts are kept
        history = self.router.get_alert_history()
        self.assertEqual(len(history), max_size)
        
    def test_route_alert_no_destinations(self):
        """Test routing when no destinations are configured"""
        # Clear default rules for this test
        self.router.routing_rules = []
        
        alert = Alert(
            id="test_alert",
            type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            title="Test Error",
            message="Test error message",
            source="test_source",
            timestamp=datetime.now(),
            metadata={}
        )
        
        # Route alert (should use default rules but no destinations exist)
        result = self.router.route_alert(alert)
        
        # Should fail because no destinations are configured
        self.assertEqual(result['status'], 'failed')
        self.assertIn('No matching routing rules found', result['error'])
        
    def test_route_alert_with_destinations(self):
        """Test routing with configured destinations"""
        # Clear default rules for this test
        self.router.routing_rules = []
        
        # Add a destination
        destination = AlertDestination(
            name="test_email",
            type="email",
            config={
                'to_addresses': ['test@example.com'],
                'from_address': 'alerts@example.com'
            }
        )
        self.router.add_destination(destination)
        
        # Add a routing rule
        rule = {
            'name': 'test_rule',
            'conditions': {
                'severity': [AlertSeverity.ERROR]
            },
            'destinations': ['test_email'],
            'priority': 1
        }
        self.router.add_routing_rule(rule)
        
        # Create and route alert
        alert = self.router.create_alert(
            AlertType.SYSTEM_ERROR,
            AlertSeverity.ERROR,
            "Test Error",
            "Test error message",
            "test_source"
        )
        
        # Alert should be in history
        history = self.router.get_alert_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].id, alert.id)
        
    def test_unsupported_destination_type(self):
        """Test handling of unsupported destination types"""
        destination = AlertDestination(
            name="unsupported",
            type="unsupported_type",
            config={}
        )
        
        alert = Alert(
            id="test_alert",
            type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            title="Test Error",
            message="Test error message",
            source="test_source",
            timestamp=datetime.now(),
            metadata={}
        )
        
        result = self.router._send_to_destination(alert, destination)
        
        self.assertEqual(result['status'], 'failed')
        self.assertIn('Unsupported destination type', result['error'])
        
    def test_email_formatting(self):
        """Test email body formatting"""
        alert = Alert(
            id="test_alert",
            type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            title="Test Error",
            message="Test error message",
            source="test_source",
            timestamp=datetime.now(),
            metadata={'key': 'value'},
            client_id="client1",
            owner_id="owner1",
            resource_id="resource1",
            agent_id="agent1"
        )
        
        body = self.router._format_email_body(alert)
        
        # Verify email body contains all expected information
        self.assertIn("Test Error", body)
        self.assertIn("ERROR", body)
        self.assertIn("system_error", body)
        self.assertIn("test_source", body)
        self.assertIn("Test error message", body)
        self.assertIn("client1", body)
        self.assertIn("owner1", body)
        self.assertIn("resource1", body)
        self.assertIn("agent1", body)
        self.assertIn('"key": "value"', body)
        
    def test_sns_message_formatting(self):
        """Test SNS message formatting"""
        alert = Alert(
            id="test_alert",
            type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.ERROR,
            title="Test Error",
            message="Test error message",
            source="test_source",
            timestamp=datetime.now(),
            metadata={'key': 'value'},
            client_id="client1",
            owner_id="owner1"
        )
        
        message = self.router._format_sns_message(alert)
        
        # Parse JSON message
        parsed = json.loads(message)
        
        # Verify message contains all expected fields
        self.assertEqual(parsed['alert_id'], "test_alert")
        self.assertEqual(parsed['type'], "system_error")
        self.assertEqual(parsed['severity'], "error")
        self.assertEqual(parsed['title'], "Test Error")
        self.assertEqual(parsed['message'], "Test error message")
        self.assertEqual(parsed['source'], "test_source")
        self.assertEqual(parsed['client_id'], "client1")
        self.assertEqual(parsed['owner_id'], "owner1")
        self.assertEqual(parsed['metadata'], {'key': 'value'})

if __name__ == '__main__':
    unittest.main() 