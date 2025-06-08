import unittest
import json
import os
from unittest.mock import MagicMock, patch
from src.agent_framework.agent_communication import AgentCommunication

class TestAgentCommunication(unittest.TestCase):
    def setUp(self):
        self.comm = AgentCommunication()
        
    def test_register_message_handler(self):
        # Create a mock handler
        mock_handler = MagicMock(return_value="handler_response")
        
        # Register the handler
        self.comm.register_message_handler("test_message", mock_handler)
        
        # Verify handler was registered
        self.assertIn("test_message", self.comm.message_handlers)
        self.assertEqual(self.comm.message_handlers["test_message"], mock_handler)
        
    def test_receive_message(self):
        # Create a mock handler
        mock_handler = MagicMock(return_value="handler_response")
        
        # Register the handler
        self.comm.register_message_handler("test_message", mock_handler)
        
        # Test receiving a message
        result = self.comm.receive_message("sender1", "test_message", "test_content")
        
        # Verify handler was called with correct arguments
        mock_handler.assert_called_once_with("sender1", "test_content")
        self.assertEqual(result, "handler_response")
        
    def test_send_message_direct(self):
        # Create a mock recipient
        mock_recipient = MagicMock()
        mock_recipient.receive_message.return_value = "response_data"
        
        # Send a message
        result = self.comm.send_message(mock_recipient, "test_message", "test_content", "sender1")
        
        # Verify recipient's receive_message was called
        mock_recipient.receive_message.assert_called_once_with("sender1", "test_message", "test_content")
        self.assertEqual(result["status"], "delivered")
        self.assertEqual(result["response"], "response_data")
        
    def test_send_message_invalid_recipient(self):
        # Send a message to an invalid recipient
        result = self.comm.send_message(None, "test_message", "test_content")
        
        # Verify error status
        self.assertEqual(result["status"], "failed")
        self.assertIn("No recipient specified", result["error"])
        
    def test_broadcast_message(self):
        # Create mock recipients
        recipient1 = MagicMock()
        recipient1.receive_message.return_value = "response1"
        recipient2 = MagicMock()
        recipient2.receive_message.return_value = "response2"
        
        # Broadcast a message
        result = self.comm.broadcast_message(
            [recipient1, recipient2], 
            "test_message", 
            "test_content", 
            "sender1"
        )
        
        # Verify recipients' receive_message was called
        recipient1.receive_message.assert_called_once_with("sender1", "test_message", "test_content")
        recipient2.receive_message.assert_called_once_with("sender1", "test_message", "test_content")
        
        # Verify broadcast result
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["successful"], 2)
        self.assertEqual(result["failed"], 0)
        
    def test_message_routing(self):
        # Create a mock destination
        mock_destination = MagicMock()
        mock_destination.receive_message.return_value = "routed_response"
        
        # Add a route
        self.comm.add_route("routed_message", mock_destination)
        
        # Route a message
        result = self.comm.route_message("routed_message", "test_content", "sender1")
        
        # Verify destination's receive_message was called
        mock_destination.receive_message.assert_called_once_with("sender1", "routed_message", "test_content")
        self.assertEqual(result["status"], "delivered")
        
    def test_default_route(self):
        # Create a mock default destination
        mock_default = MagicMock()
        mock_default.receive_message.return_value = "default_response"
        
        # Set default route
        self.comm.set_default_route(mock_default)
        
        # Route a message with no specific route
        result = self.comm.route_message("unknown_message", "test_content", "sender1")
        
        # Verify default destination's receive_message was called
        mock_default.receive_message.assert_called_once_with("sender1", "unknown_message", "test_content")
        self.assertEqual(result["status"], "delivered")
        
    def test_serialization_deserialization(self):
        # Create a test message
        test_message = {
            "sender": "sender1",
            "message_type": "test_message",
            "content": "test_content",
            "metadata": {"key": "value"}
        }
        
        # Test JSON serialization
        self.comm.set_serialization_format("json")
        serialized = self.comm.serialize_message(test_message)
        deserialized = self.comm.deserialize_message(serialized)
        
        # Verify serialization/deserialization worked
        self.assertEqual(deserialized, test_message)
        
        # Test base64_json serialization
        self.comm.set_serialization_format("base64_json")
        serialized = self.comm.serialize_message(test_message)
        deserialized = self.comm.deserialize_message(serialized)
        
        # Verify serialization/deserialization worked
        self.assertEqual(deserialized, test_message)
        
    def test_secure_communication(self):
        # Enable security
        key = self.comm.enable_security()
        
        # Create a mock recipient
        mock_recipient = MagicMock()
        
        # Register auth key and authorize sender
        auth_key = b"test_auth_key"
        sender_id = "secure_sender"
        self.comm.register_auth_key(sender_id, auth_key)
        self.comm.authorize_sender(sender_id)
        
        # Send secure message
        result = self.comm.send_secure_message(
            mock_recipient,
            "secure_message",
            "secure_content",
            sender_id,
            auth_key
        )
        
        # Verify message was sent
        self.assertEqual(result["status"], "delivered")
        
        # Verify recipient received encrypted message
        call_args = mock_recipient.receive_message.call_args
        self.assertEqual(call_args[0][0], sender_id)
        self.assertEqual(call_args[0][1], "secure_message")
        # The content should be encrypted
        self.assertNotEqual(call_args[0][2], "secure_content")
        
    def test_ownership_routing(self):
        # Set up ownership
        self.comm.set_owner("owner1")
        
        # Create mock destinations
        mock_dest1 = MagicMock()
        mock_dest2 = MagicMock()
        
        # Add ownership routes
        self.comm.add_ownership_route("owner1", mock_dest1)
        self.comm.add_ownership_route("owner2", mock_dest2)
        
        # Allow cross-owner communication
        self.comm.set_cross_owner_policy("allow")
        
        # Route message to same owner
        result1 = self.comm.route_message_by_ownership(
            "owner1", "owner1", "test_message", "test_content", "sender1"
        )
        
        # Verify message was routed to correct destination
        mock_dest1.receive_message.assert_called_once()
        self.assertEqual(result1["status"], "delivered")
        
        # Route message to different owner
        result2 = self.comm.route_message_by_ownership(
            "owner1", "owner2", "test_message", "test_content", "sender1"
        )
        
        # Verify message was routed to correct destination
        mock_dest2.receive_message.assert_called_once()
        self.assertEqual(result2["status"], "delivered")
        
        # Test deny policy
        self.comm.set_cross_owner_policy("deny")
        result3 = self.comm.route_message_by_ownership(
            "owner1", "owner2", "test_message", "test_content", "sender1"
        )
        
        # Verify message was denied
        self.assertEqual(result3["status"], "failed")
        self.assertIn("denied by policy", result3["error"])

    @patch('boto3.client')
    def test_sqs_integration(self, mock_boto_client):
        # Mock SQS client
        mock_sqs = MagicMock()
        mock_boto_client.return_value = mock_sqs
        
        # Mock responses
        mock_sqs.create_queue.return_value = {"QueueUrl": "https://sqs.example.com/test-queue"}
        mock_sqs.send_message.return_value = {"MessageId": "test-message-id"}
        
        # Enable SQS
        result = self.comm.enable_sqs("us-west-2")
        self.assertTrue(result)
        
        # Create queue
        queue_url = self.comm.create_sqs_queue("test-queue")
        self.assertEqual(queue_url, "https://sqs.example.com/test-queue")
        
        # Set default queue
        self.comm.set_default_sqs_queue("test-queue")
        
        # Send message
        send_result = self.comm.send_message_to_sqs(
            "test_message",
            "test_content",
            "test-queue",
            "sender1"
        )
        
        # Verify message was sent
        self.assertEqual(send_result["status"], "sent")
        self.assertEqual(send_result["message_id"], "test-message-id")

    @patch('boto3.client')
    def test_eventbridge_integration(self, mock_boto_client):
        # Mock EventBridge client
        mock_events = MagicMock()
        mock_boto_client.return_value = mock_events
        
        # Mock responses
        mock_events.put_events.return_value = {
            "FailedEntryCount": 0,
            "Entries": [{"EventId": "test-event-id"}]
        }
        mock_events.put_rule.return_value = {"RuleArn": "arn:aws:events:us-west-2:123456789012:rule/test-rule"}
        
        # Enable EventBridge
        result = self.comm.enable_eventbridge("us-west-2")
        self.assertTrue(result)
        
        # Publish event
        event_result = self.comm.publish_event(
            "test_event",
            {"key": "value"},
            "TestEvent"
        )
        
        # Verify event was published
        self.assertEqual(event_result["status"], "published")
        self.assertEqual(event_result["event_id"], "test-event-id")
        
        # Create rule
        rule_arn = self.comm.create_event_rule(
            "test-rule",
            event_pattern={"source": ["com.autonomous.agent"]}
        )
        
        # Verify rule was created
        self.assertEqual(rule_arn, "arn:aws:events:us-west-2:123456789012:rule/test-rule")
        
        # Create event pattern
        pattern = self.comm.create_event_pattern_for_message_type("test_message")
        
        # Verify pattern is correct
        self.assertEqual(pattern["source"], [self.comm.event_source])
        self.assertEqual(pattern["detail-type"], ["Agent.test_message"])

if __name__ == '__main__':
    unittest.main()