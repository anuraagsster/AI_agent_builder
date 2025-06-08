import json
import base64
import queue
import threading
import time
import hmac
import hashlib
import os
import uuid
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, List, Union, Optional, Callable

class AgentCommunication:
    def __init__(self):
        self.message_handlers = {}
        self.routes = {}
        self.default_route = None
        self.serialization_format = "json"  # Default serialization format
        
        # Message queue for asynchronous processing
        self.message_queue = queue.Queue()
        self.async_processing = False
        self.async_thread = None
        self.async_handlers = {}
        
        # Security settings
        self.security_enabled = False
        self.encryption_key = None
        self.auth_keys = {}  # Map of agent_id to auth keys
        self.authorized_senders = set()  # Set of authorized sender agent_ids
        
        # Ownership settings
        self.owner_id = None  # Owner of this communication handler
        self.ownership_routes = {}  # Map of owner_id to destination
        self.cross_owner_policy = "deny"  # Policy for cross-owner communication: deny, allow, or secure
        
        # AWS SQS settings
        self.sqs_enabled = False
        self.sqs_client = None
        self.sqs_queues = {}  # Map of queue_name to queue_url
        self.default_queue = None
        
        # AWS EventBridge settings
        self.eventbridge_enabled = False
        self.eventbridge_client = None
        self.event_bus_name = "default"
        self.event_source = "com.autonomous.agent"
        
    def register_message_handler(self, message_type, handler):
        """Register a handler for a specific message type"""
        self.message_handlers[message_type] = handler
        
    def send_message(self, recipient, message_type, content, sender=None, metadata=None):
        """
        Send a message to another agent
        
        Args:
            recipient: The recipient agent's communication handler or agent_id
            message_type: Type of message being sent
            content: The message content/payload
            sender: The sender's agent_id (optional)
            metadata: Additional metadata for the message (optional)
            
        Returns:
            Dictionary with status of the message delivery and any response
        """
        if not recipient:
            return {"status": "failed", "error": "No recipient specified"}
            
        # Create message structure
        message = {
            "sender": sender,
            "message_type": message_type,
            "content": content,
            "timestamp": self._get_timestamp(),
            "metadata": metadata or {}
        }
        
        # Handle different recipient types
        if hasattr(recipient, "receive_message"):
            # Direct object reference to another AgentCommunication instance
            try:
                response = recipient.receive_message(sender, message_type, content)
                return {
                    "status": "delivered",
                    "response": response
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": str(e)
                }
        elif isinstance(recipient, str):
            # Agent ID - would need a registry to look up the agent
            # This is a placeholder for future implementation with a registry
            return {
                "status": "pending",
                "message": "Message queued for delivery to agent ID: " + recipient
            }
        else:
            return {
                "status": "failed",
                "error": "Invalid recipient type"
            }
    
    def _get_timestamp(self):
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
        
    def receive_message(self, sender, message_type, content):
        """Process a received message"""
        if message_type in self.message_handlers:
            return self.message_handlers[message_type](sender, content)
        return None
        
    def broadcast_message(self, recipients, message_type, content, sender=None, metadata=None):
        """
        Send a message to multiple agents
        
        Args:
            recipients: List of recipient agent communication handlers or agent_ids
            message_type: Type of message being sent
            content: The message content/payload
            sender: The sender's agent_id (optional)
            metadata: Additional metadata for the message (optional)
            
        Returns:
            Dictionary with status of the broadcast and delivery results
        """
        if not recipients:
            return {"status": "failed", "error": "No recipients specified"}
            
        results = {
            "status": "completed",
            "total": len(recipients),
            "successful": 0,
            "failed": 0,
            "pending": 0,
            "details": []
        }
        
        # Send message to each recipient
        for recipient in recipients:
            result = self.send_message(recipient, message_type, content, sender, metadata)
            results["details"].append(result)
            
            # Update counters
            if result["status"] == "delivered":
                results["successful"] += 1
            elif result["status"] == "pending":
                results["pending"] += 1
            else:
                results["failed"] += 1
                
        # Update overall status
        if results["failed"] == len(recipients):
            results["status"] = "failed"
        elif results["failed"] > 0 or results["pending"] > 0:
            results["status"] = "partial"
            
        return results
        
    def add_route(self, message_type, destination):
        """
        Add a routing rule for a specific message type
        
        Args:
            message_type: The type of message to route
            destination: The destination to route messages to (agent or handler)
        """
        self.routes[message_type] = destination
        
    def set_default_route(self, destination):
        """
        Set the default route for messages without a specific route
        
        Args:
            destination: The default destination for messages
        """
        self.default_route = destination
        
    def route_message(self, message_type, content, sender=None, metadata=None):
        """
        Route a message based on its type using the routing table
        
        Args:
            message_type: Type of message to route
            content: The message content
            sender: The sender's agent_id (optional)
            metadata: Additional metadata for the message (optional)
            
        Returns:
            Dictionary with status of the routing operation
        """
        # Check if we have a specific route for this message type
        if message_type in self.routes:
            destination = self.routes[message_type]
            return self.send_message(destination, message_type, content, sender, metadata)
        
        # Use default route if available
        elif self.default_route:
            return self.send_message(self.default_route, message_type, content, sender, metadata)
        
        # No route available
        else:
            return {
                "status": "failed",
                "error": f"No route found for message type: {message_type}"
            }
            
    def serialize_message(self, message: Dict[str, Any]) -> str:
        """
        Serialize a message to a string format for transmission or storage
        
        Args:
            message: The message dictionary to serialize
            
        Returns:
            Serialized message string
        """
        if self.serialization_format == "json":
            return json.dumps(message)
        elif self.serialization_format == "base64_json":
            # JSON encode then Base64 for binary transmission
            json_str = json.dumps(message)
            return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        else:
            raise ValueError(f"Unsupported serialization format: {self.serialization_format}")
    
    def deserialize_message(self, serialized_message: str) -> Dict[str, Any]:
        """
        Deserialize a message from string format back to a dictionary
        
        Args:
            serialized_message: The serialized message string
            
        Returns:
            Deserialized message dictionary
        """
        if self.serialization_format == "json":
            return json.loads(serialized_message)
        elif self.serialization_format == "base64_json":
            # Base64 decode then JSON decode
            json_str = base64.b64decode(serialized_message.encode('utf-8')).decode('utf-8')
            return json.loads(json_str)
        else:
            raise ValueError(f"Unsupported serialization format: {self.serialization_format}")
    
    def set_serialization_format(self, format_name: str) -> None:
        """
        Set the serialization format to use for messages
        
        Args:
            format_name: The name of the serialization format ("json" or "base64_json")
        """
        supported_formats = ["json", "base64_json"]
        if format_name not in supported_formats:
            raise ValueError(f"Unsupported serialization format: {format_name}. Supported formats: {supported_formats}")
        
        self.serialization_format = format_name
        
    def send_message_async(self, recipient, message_type, content, sender=None, metadata=None):
        """
        Send a message asynchronously (non-blocking)
        
        Args:
            recipient: The recipient agent's communication handler or agent_id
            message_type: Type of message being sent
            content: The message content/payload
            sender: The sender's agent_id (optional)
            metadata: Additional metadata for the message (optional)
            
        Returns:
            Dictionary with status of the queuing operation
        """
        # Create message structure
        message = {
            "recipient": recipient,
            "sender": sender,
            "message_type": message_type,
            "content": content,
            "timestamp": self._get_timestamp(),
            "metadata": metadata or {}
        }
        
        # Add to queue for async processing
        try:
            self.message_queue.put(message)
            return {
                "status": "queued",
                "queue_size": self.message_queue.qsize()
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Failed to queue message: {str(e)}"
            }
    
    def register_async_handler(self, message_type, handler):
        """
        Register a handler for asynchronous processing of specific message types
        
        Args:
            message_type: Type of message to handle
            handler: Function to handle the message
        """
        self.async_handlers[message_type] = handler
    
    def start_async_processing(self):
        """
        Start asynchronous message processing in a background thread
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.async_processing:
            return False  # Already running
            
        self.async_processing = True
        self.async_thread = threading.Thread(target=self._process_async_messages)
        self.async_thread.daemon = True  # Thread will exit when main program exits
        self.async_thread.start()
        return True
    
    def stop_async_processing(self):
        """
        Stop asynchronous message processing
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.async_processing:
            return False  # Not running
            
        self.async_processing = False
        if self.async_thread:
            self.async_thread.join(timeout=2.0)  # Wait for thread to finish
            self.async_thread = None
        return True
    
    def _process_async_messages(self):
        """Background thread function to process queued messages"""
        while self.async_processing:
            try:
                # Get message from queue with timeout to allow checking async_processing flag
                try:
                    message = self.message_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                    
                # Process the message
                recipient = message.get("recipient")
                message_type = message.get("message_type")
                content = message.get("content")
                sender = message.get("sender")
                metadata = message.get("metadata", {})
                
                # Use async handler if available
                if message_type in self.async_handlers:
                    try:
                        self.async_handlers[message_type](sender, content, metadata)
                    except Exception as e:
                        # Log error but continue processing other messages
                        print(f"Error in async handler for {message_type}: {str(e)}")
                else:
                    # Fall back to synchronous send
                    self.send_message(recipient, message_type, content, sender, metadata)
                    
                # Mark as done
                self.message_queue.task_done()
                
            except Exception as e:
                # Log error but continue processing
                print(f"Error in async message processing: {str(e)}")
                time.sleep(0.1)  # Prevent tight loop in case of persistent errors
                
    def enable_security(self, encryption_key=None):
        """
        Enable secure communication features
        
        Args:
            encryption_key: Optional encryption key (generated if not provided)
            
        Returns:
            The encryption key being used
        """
        self.security_enabled = True
        
        # Generate encryption key if not provided
        if not encryption_key:
            encryption_key = os.urandom(32)  # 256-bit key
            
        self.encryption_key = encryption_key
        return encryption_key
    
    def disable_security(self):
        """Disable secure communication features"""
        self.security_enabled = False
        self.encryption_key = None
        
    def register_auth_key(self, agent_id, auth_key):
        """
        Register an authentication key for an agent
        
        Args:
            agent_id: The agent's ID
            auth_key: Authentication key for the agent
        """
        self.auth_keys[agent_id] = auth_key
        
    def authorize_sender(self, sender_id):
        """
        Add a sender to the authorized senders list
        
        Args:
            sender_id: The sender's agent_id to authorize
        """
        self.authorized_senders.add(sender_id)
        
    def revoke_sender(self, sender_id):
        """
        Remove a sender from the authorized senders list
        
        Args:
            sender_id: The sender's agent_id to revoke
        """
        if sender_id in self.authorized_senders:
            self.authorized_senders.remove(sender_id)
            
    def send_secure_message(self, recipient, message_type, content, sender, auth_key):
        """
        Send an authenticated and encrypted message
        
        Args:
            recipient: The recipient agent's communication handler or agent_id
            message_type: Type of message being sent
            content: The message content/payload
            sender: The sender's agent_id (required for secure messages)
            auth_key: Authentication key for the sender
            
        Returns:
            Dictionary with status of the message delivery
        """
        if not self.security_enabled:
            return {"status": "failed", "error": "Security not enabled"}
            
        if not sender:
            return {"status": "failed", "error": "Sender ID required for secure messages"}
            
        # Verify sender is authorized
        if sender not in self.authorized_senders:
            return {"status": "failed", "error": "Sender not authorized"}
            
        # Create message with authentication
        message = {
            "sender": sender,
            "message_type": message_type,
            "content": content,
            "timestamp": self._get_timestamp()
        }
        
        # Add authentication signature
        signature = self._create_signature(message, auth_key)
        message["signature"] = signature
        
        # Encrypt the message
        encrypted_content = self._encrypt_content(message)
        
        # Send the encrypted message
        metadata = {"encrypted": True, "requires_auth": True}
        return self.send_message(recipient, "secure_message", encrypted_content, sender, metadata)
        
    def receive_secure_message(self, sender, content):
        """
        Process a received secure message
        
        Args:
            sender: The sender's agent_id
            content: The encrypted message content
            
        Returns:
            Decrypted and verified message content, or None if verification fails
        """
        if not self.security_enabled:
            return None
            
        try:
            # Decrypt the message
            decrypted_message = self._decrypt_content(content)
            
            # Verify the sender
            if decrypted_message.get("sender") != sender:
                return None
                
            # Verify the signature
            if sender in self.auth_keys:
                auth_key = self.auth_keys[sender]
                signature = decrypted_message.pop("signature", None)
                
                if not signature or not self._verify_signature(decrypted_message, signature, auth_key):
                    return None
                    
            # Process the message
            return decrypted_message.get("content")
            
        except Exception as e:
            print(f"Error processing secure message: {str(e)}")
            return None
            
    def _create_signature(self, message, auth_key):
        """Create an HMAC signature for a message"""
        message_str = json.dumps(message, sort_keys=True)
        return hmac.new(auth_key, message_str.encode(), hashlib.sha256).hexdigest()
        
    def _verify_signature(self, message, signature, auth_key):
        """Verify an HMAC signature for a message"""
        message_str = json.dumps(message, sort_keys=True)
        expected = hmac.new(auth_key, message_str.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)
        
    def _encrypt_content(self, content):
        """
        Encrypt message content (placeholder implementation)
        
        In a real implementation, this would use proper encryption like AES
        """
        # For demonstration purposes, using base64 encoding as a placeholder
        # In a real implementation, use proper encryption
        content_json = json.dumps(content)
        return base64.b64encode(content_json.encode()).decode()
        
    def _decrypt_content(self, encrypted_content):
        """
        Decrypt message content (placeholder implementation)
        
        In a real implementation, this would use proper decryption like AES
        """
        # For demonstration purposes, using base64 decoding as a placeholder
        # In a real implementation, use proper decryption
        content_json = base64.b64decode(encrypted_content.encode()).decode()
        return json.loads(content_json)
        
    def set_owner(self, owner_id):
        """
        Set the owner of this communication handler
        
        Args:
            owner_id: The ID of the owner
        """
        self.owner_id = owner_id
        
    def add_ownership_route(self, owner_id, destination):
        """
        Add a routing rule for messages from a specific owner
        
        Args:
            owner_id: The owner ID to route messages from
            destination: The destination to route messages to
        """
        self.ownership_routes[owner_id] = destination
        
    def set_cross_owner_policy(self, policy):
        """
        Set the policy for cross-owner communication
        
        Args:
            policy: The policy to use ("deny", "allow", or "secure")
        """
        valid_policies = ["deny", "allow", "secure"]
        if policy not in valid_policies:
            raise ValueError(f"Invalid cross-owner policy: {policy}. Valid policies: {valid_policies}")
            
        self.cross_owner_policy = policy
        
    def route_message_by_ownership(self, sender_owner_id, recipient_owner_id, message_type, content, sender=None, metadata=None):
        """
        Route a message based on ownership information
        
        Args:
            sender_owner_id: The owner ID of the sender
            recipient_owner_id: The owner ID of the recipient
            message_type: Type of message being sent
            content: The message content/payload
            sender: The sender's agent_id (optional)
            metadata: Additional metadata for the message (optional)
            
        Returns:
            Dictionary with status of the routing operation
        """
        # Check if this is cross-owner communication
        is_cross_owner = sender_owner_id != recipient_owner_id
        
        # Apply cross-owner policy if needed
        if is_cross_owner:
            if self.cross_owner_policy == "deny":
                return {
                    "status": "failed",
                    "error": "Cross-owner communication denied by policy"
                }
            elif self.cross_owner_policy == "secure" and not self.security_enabled:
                return {
                    "status": "failed",
                    "error": "Secure communication required but not enabled"
                }
        
        # Check if we have a specific route for this owner
        if recipient_owner_id in self.ownership_routes:
            destination = self.ownership_routes[recipient_owner_id]
            
            # Add ownership metadata
            if not metadata:
                metadata = {}
            metadata["sender_owner_id"] = sender_owner_id
            metadata["recipient_owner_id"] = recipient_owner_id
            metadata["cross_owner"] = is_cross_owner
            
            # Use secure communication for cross-owner if policy requires it
            if is_cross_owner and self.cross_owner_policy == "secure" and sender and sender in self.auth_keys:
                return self.send_secure_message(
                    destination,
                    message_type,
                    content,
                    sender,
                    self.auth_keys[sender]
                )
            else:
                return self.send_message(
                    destination,
                    message_type,
                    content,
                    sender,
                    metadata
                )
        else:
            return {
                "status": "failed",
                "error": f"No route found for owner: {recipient_owner_id}"
            }
            
    # AWS SQS Integration
    
    def enable_sqs(self, aws_region=None, aws_access_key=None, aws_secret_key=None):
        """
        Enable AWS SQS integration for message queuing
        
        Args:
            aws_region: AWS region for SQS (uses default if None)
            aws_access_key: AWS access key (uses default credentials if None)
            aws_secret_key: AWS secret key (uses default credentials if None)
            
        Returns:
            True if enabled successfully, False otherwise
        """
        try:
            # Create SQS client
            kwargs = {}
            if aws_region:
                kwargs['region_name'] = aws_region
            if aws_access_key and aws_secret_key:
                kwargs['aws_access_key_id'] = aws_access_key
                kwargs['aws_secret_access_key'] = aws_secret_key
                
            self.sqs_client = boto3.client('sqs', **kwargs)
            self.sqs_enabled = True
            return True
            
        except Exception as e:
            print(f"Failed to enable SQS: {str(e)}")
            self.sqs_enabled = False
            self.sqs_client = None
            return False
            
    def disable_sqs(self):
        """Disable AWS SQS integration"""
        self.sqs_enabled = False
        self.sqs_client = None
        
    def create_sqs_queue(self, queue_name, fifo=False, attributes=None):
        """
        Create an SQS queue
        
        Args:
            queue_name: Name of the queue to create
            fifo: Whether to create a FIFO queue
            attributes: Additional queue attributes
            
        Returns:
            Queue URL if created successfully, None otherwise
        """
        if not self.sqs_enabled or not self.sqs_client:
            return None
            
        try:
            # Add .fifo suffix for FIFO queues if not already present
            if fifo and not queue_name.endswith('.fifo'):
                queue_name = f"{queue_name}.fifo"
                
            # Set up queue attributes
            queue_attributes = attributes or {}
            if fifo:
                queue_attributes['FifoQueue'] = 'true'
                
            # Create the queue
            response = self.sqs_client.create_queue(
                QueueName=queue_name,
                Attributes=queue_attributes
            )
            
            queue_url = response.get('QueueUrl')
            if queue_url:
                self.sqs_queues[queue_name] = queue_url
                
            return queue_url
            
        except ClientError as e:
            print(f"Error creating SQS queue: {str(e)}")
            return None
            
    def set_default_sqs_queue(self, queue_name):
        """
        Set the default SQS queue for sending messages
        
        Args:
            queue_name: Name of the queue to use as default
            
        Returns:
            True if successful, False otherwise
        """
        if queue_name in self.sqs_queues:
            self.default_queue = queue_name
            return True
        return False
        
    def send_message_to_sqs(self, message_type, content, queue_name=None, sender=None, metadata=None, message_group_id=None):
        """
        Send a message to an SQS queue
        
        Args:
            message_type: Type of message being sent
            content: The message content/payload
            queue_name: Name of the queue to send to (uses default if None)
            sender: The sender's agent_id (optional)
            metadata: Additional metadata for the message (optional)
            message_group_id: Message group ID for FIFO queues (optional)
            
        Returns:
            Dictionary with status of the send operation
        """
        if not self.sqs_enabled or not self.sqs_client:
            return {"status": "failed", "error": "SQS not enabled"}
            
        # Use default queue if none specified
        if not queue_name:
            if not self.default_queue:
                return {"status": "failed", "error": "No queue specified and no default queue set"}
            queue_name = self.default_queue
            
        # Get queue URL
        queue_url = self.sqs_queues.get(queue_name)
        if not queue_url:
            return {"status": "failed", "error": f"Queue not found: {queue_name}"}
            
        try:
            # Create message structure
            message = {
                "sender": sender,
                "message_type": message_type,
                "content": content,
                "timestamp": self._get_timestamp(),
                "metadata": metadata or {}
            }
            
            # Serialize the message
            message_body = self.serialize_message(message)
            
            # Set up send parameters
            send_params = {
                'QueueUrl': queue_url,
                'MessageBody': message_body
            }
            
            # Add FIFO-specific parameters if needed
            is_fifo = queue_name.endswith('.fifo')
            if is_fifo:
                # Generate message deduplication ID if not provided
                dedup_id = str(uuid.uuid4())
                send_params['MessageDeduplicationId'] = dedup_id
                
                # Use provided message group ID or default
                send_params['MessageGroupId'] = message_group_id or 'default'
                
            # Send the message
            response = self.sqs_client.send_message(**send_params)
            
            return {
                "status": "sent",
                "message_id": response.get('MessageId'),
                "queue": queue_name
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Failed to send message to SQS: {str(e)}"
            }
            
    def receive_messages_from_sqs(self, queue_name, max_messages=10, wait_time=0, visibility_timeout=30):
        """
        Receive messages from an SQS queue
        
        Args:
            queue_name: Name of the queue to receive from
            max_messages: Maximum number of messages to receive (1-10)
            wait_time: Long polling wait time in seconds (0-20)
            visibility_timeout: Visibility timeout in seconds
            
        Returns:
            List of received messages or empty list if none available
        """
        if not self.sqs_enabled or not self.sqs_client:
            return []
            
        # Get queue URL
        queue_url = self.sqs_queues.get(queue_name)
        if not queue_url:
            return []
            
        try:
            # Receive messages
            response = self.sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max(1, min(10, max_messages)),
                WaitTimeSeconds=max(0, min(20, wait_time)),
                VisibilityTimeout=visibility_timeout,
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            result = []
            
            for msg in messages:
                try:
                    # Parse the message body
                    body = msg.get('Body', '{}')
                    message_data = self.deserialize_message(body)
                    
                    # Add receipt handle for deletion
                    message_data['receipt_handle'] = msg.get('ReceiptHandle')
                    message_data['message_id'] = msg.get('MessageId')
                    
                    result.append(message_data)
                except Exception as e:
                    print(f"Error parsing SQS message: {str(e)}")
                    
            return result
            
        except Exception as e:
            print(f"Error receiving messages from SQS: {str(e)}")
            return []
            
    def delete_message_from_sqs(self, queue_name, receipt_handle):
        """
        Delete a message from an SQS queue after processing
        
        Args:
            queue_name: Name of the queue
            receipt_handle: Receipt handle of the message to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.sqs_enabled or not self.sqs_client:
            return False
            
        # Get queue URL
        queue_url = self.sqs_queues.get(queue_name)
        if not queue_url:
            return False
            
        try:
            self.sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            return True
        except Exception as e:
            print(f"Error deleting message from SQS: {str(e)}")
            return False
            
    # AWS EventBridge Integration
    
    def enable_eventbridge(self, aws_region=None, aws_access_key=None, aws_secret_key=None, event_bus_name="default", event_source=None):
        """
        Enable AWS EventBridge integration for event-based communication
        
        Args:
            aws_region: AWS region for EventBridge (uses default if None)
            aws_access_key: AWS access key (uses default credentials if None)
            aws_secret_key: AWS secret key (uses default credentials if None)
            event_bus_name: Name of the event bus to use
            event_source: Source name for events (defaults to com.autonomous.agent)
            
        Returns:
            True if enabled successfully, False otherwise
        """
        try:
            # Create EventBridge client
            kwargs = {}
            if aws_region:
                kwargs['region_name'] = aws_region
            if aws_access_key and aws_secret_key:
                kwargs['aws_access_key_id'] = aws_access_key
                kwargs['aws_secret_access_key'] = aws_secret_key
                
            self.eventbridge_client = boto3.client('events', **kwargs)
            self.eventbridge_enabled = True
            self.event_bus_name = event_bus_name
            self.event_source = event_source or "com.autonomous.agent"
            return True
            
        except Exception as e:
            print(f"Failed to enable EventBridge: {str(e)}")
            self.eventbridge_enabled = False
            self.eventbridge_client = None
            return False
            
    def disable_eventbridge(self):
        """Disable AWS EventBridge integration"""
        self.eventbridge_enabled = False
        self.eventbridge_client = None
        
    def publish_event(self, event_type, detail, detail_type=None, resources=None):
        """
        Publish an event to EventBridge
        
        Args:
            event_type: Type of event (used in detail-type if detail_type not provided)
            detail: Event detail payload (must be JSON serializable)
            detail_type: Detail type for the event (defaults to event_type)
            resources: List of resources associated with the event
            
        Returns:
            Dictionary with status of the publish operation
        """
        if not self.eventbridge_enabled or not self.eventbridge_client:
            return {"status": "failed", "error": "EventBridge not enabled"}
            
        try:
            # Create event entry
            event_entry = {
                'Source': self.event_source,
                'DetailType': detail_type or f"Agent.{event_type}",
                'Detail': json.dumps(detail),
                'EventBusName': self.event_bus_name
            }
            
            # Add resources if provided
            if resources:
                event_entry['Resources'] = resources
                
            # Put the event
            response = self.eventbridge_client.put_events(
                Entries=[event_entry]
            )
            
            # Check for failures
            failed_count = response.get('FailedEntryCount', 0)
            if failed_count > 0:
                return {
                    "status": "failed",
                    "error": f"Failed to publish event: {failed_count} entries failed"
                }
                
            # Return success with event ID
            entries = response.get('Entries', [])
            event_id = entries[0].get('EventId') if entries else None
            
            return {
                "status": "published",
                "event_id": event_id,
                "event_bus": self.event_bus_name
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Failed to publish event to EventBridge: {str(e)}"
            }
            
    def create_event_rule(self, rule_name, event_pattern=None, schedule_expression=None, description=None):
        """
        Create an EventBridge rule for event filtering
        
        Args:
            rule_name: Name of the rule to create
            event_pattern: JSON pattern for matching events
            schedule_expression: Schedule expression for time-based rules
            description: Description of the rule
            
        Returns:
            ARN of the created rule if successful, None otherwise
        """
        if not self.eventbridge_enabled or not self.eventbridge_client:
            return None
            
        if not event_pattern and not schedule_expression:
            print("Either event_pattern or schedule_expression must be provided")
            return None
            
        try:
            # Set up rule parameters
            rule_params = {
                'Name': rule_name,
                'EventBusName': self.event_bus_name,
                'State': 'ENABLED'
            }
            
            if description:
                rule_params['Description'] = description
                
            if event_pattern:
                if isinstance(event_pattern, dict):
                    event_pattern = json.dumps(event_pattern)
                rule_params['EventPattern'] = event_pattern
                
            if schedule_expression:
                rule_params['ScheduleExpression'] = schedule_expression
                
            # Create the rule
            response = self.eventbridge_client.put_rule(**rule_params)
            
            return response.get('RuleArn')
            
        except Exception as e:
            print(f"Error creating EventBridge rule: {str(e)}")
            return None
            
    def add_event_target(self, rule_name, target_arn, target_id=None, input_path=None, input_transformer=None):
        """
        Add a target to an EventBridge rule
        
        Args:
            rule_name: Name of the rule to add target to
            target_arn: ARN of the target resource
            target_id: ID for the target (generated if not provided)
            input_path: JSONPath to extract part of the event
            input_transformer: Transform the event before sending to target
            
        Returns:
            True if target added successfully, False otherwise
        """
        if not self.eventbridge_enabled or not self.eventbridge_client:
            return False
            
        try:
            # Create target configuration
            target = {
                'Id': target_id or f"target-{uuid.uuid4()}",
                'Arn': target_arn
            }
            
            if input_path:
                target['InputPath'] = input_path
                
            if input_transformer:
                target['InputTransformer'] = input_transformer
                
            # Add the target to the rule
            self.eventbridge_client.put_targets(
                Rule=rule_name,
                EventBusName=self.event_bus_name,
                Targets=[target]
            )
            
            return True
            
        except Exception as e:
            print(f"Error adding target to EventBridge rule: {str(e)}")
            return False
            
    def create_event_pattern_for_message_type(self, message_type):
        """
        Create an event pattern that matches a specific message type
        
        Args:
            message_type: The message type to match
            
        Returns:
            Event pattern dictionary
        """
        return {
            "source": [self.event_source],
            "detail-type": [f"Agent.{message_type}"]
        }