"""
MCP (Model Control Protocol) Compliance Layer.

This module implements security measures, audit logging, and access control
for the Tool Management Service to ensure compliance with MCP requirements.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import jwt
from cryptography.fernet import Fernet
import hashlib
import os

class SecurityManager:
    """
    Manages security measures for the Tool Management Service.
    
    This class handles encryption, authentication, and authorization.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the security manager.
        
        Args:
            config: Security configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize encryption
        self._init_encryption()
        
        # Initialize AWS clients
        self._init_aws_clients()
        
    def _init_encryption(self):
        """Initialize encryption keys and ciphers."""
        # Generate or load encryption key
        key_file = self.config.get('encryption_key_file')
        if key_file and os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.encryption_key = f.read()
        else:
            self.encryption_key = Fernet.generate_key()
            if key_file:
                with open(key_file, 'wb') as f:
                    f.write(self.encryption_key)
                    
        self.cipher = Fernet(self.encryption_key)
        
    def _init_aws_clients(self):
        """Initialize AWS clients for security services."""
        self.kms = boto3.client('kms')
        self.secrets = boto3.client('secretsmanager')
        
    def encrypt_data(self, data: Dict[str, Any]) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data as string
        """
        try:
            # Convert data to JSON string
            json_data = json.dumps(data)
            
            # Encrypt the data
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            return encrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
            
    def decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data as string
            
        Returns:
            Decrypted data
        """
        try:
            # Decrypt the data
            decrypted_data = self.cipher.decrypt(encrypted_data.encode())
            
            # Parse JSON
            return json.loads(decrypted_data.decode())
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
            
    def generate_token(self, user_id: str, permissions: Set[str]) -> str:
        """
        Generate JWT token for authentication.
        
        Args:
            user_id: User ID
            permissions: Set of permissions
            
        Returns:
            JWT token
        """
        try:
            # Create token payload
            payload = {
                'user_id': user_id,
                'permissions': list(permissions),
                'exp': int(time.time()) + self.config.get('token_expiry', 3600)
            }
            
            # Sign token with KMS
            response = self.kms.sign(
                KeyId=self.config['kms_key_id'],
                Message=json.dumps(payload).encode(),
                SigningAlgorithm='RSASSA_PSS_SHA_256'
            )
            
            return response['Signature'].decode()
        except Exception as e:
            self.logger.error(f"Token generation failed: {e}")
            raise
            
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            Token payload if valid
            
        Raises:
            ValueError: If token is invalid
        """
        try:
            # Verify token with KMS
            response = self.kms.verify(
                KeyId=self.config['kms_key_id'],
                Message=token.encode(),
                Signature=token.encode(),
                SigningAlgorithm='RSASSA_PSS_SHA_256'
            )
            
            if not response['SignatureValid']:
                raise ValueError("Invalid token signature")
                
            # Parse payload
            return json.loads(response['Message'].decode())
        except Exception as e:
            self.logger.error(f"Token verification failed: {e}")
            raise ValueError("Invalid token")


class AuditLogger:
    """
    Handles audit logging for the Tool Management Service.
    
    This class manages logging of security-relevant events and actions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the audit logger.
        
        Args:
            config: Audit logging configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize AWS clients
        self._init_aws_clients()
        
    def _init_aws_clients(self):
        """Initialize AWS clients for audit logging."""
        self.cloudwatch = boto3.client('cloudwatch')
        self.firehose = boto3.client('firehose')
        
    def log_event(self, event_type: str, user_id: str, action: str,
                  resource: str, details: Dict[str, Any] = None) -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of event (e.g., 'auth', 'access', 'modification')
            user_id: ID of the user performing the action
            action: Action performed
            resource: Resource affected
            details: Additional event details
        """
        try:
            # Create event record
            event = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'details': details or {}
            }
            
            # Send to CloudWatch
            self.cloudwatch.put_metric_data(
                Namespace='ToolManagementService/Audit',
                MetricData=[{
                    'MetricName': event_type,
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'UserID', 'Value': user_id},
                        {'Name': 'Action', 'Value': action},
                        {'Name': 'Resource', 'Value': resource}
                    ]
                }]
            )
            
            # Send to Firehose for long-term storage
            self.firehose.put_record(
                DeliveryStreamName=self.config['audit_stream_name'],
                Record={'Data': json.dumps(event) + '\n'}
            )
            
            # Log locally
            self.logger.info(f"Audit event: {json.dumps(event)}")
        except Exception as e:
            self.logger.error(f"Audit logging failed: {e}")
            raise


class AccessController:
    """
    Manages access control for the Tool Management Service.
    
    This class handles permission management and access control checks.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the access controller.
        
        Args:
            config: Access control configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize AWS clients
        self._init_aws_clients()
        
        # Load permissions
        self._load_permissions()
        
    def _init_aws_clients(self):
        """Initialize AWS clients for access control."""
        self.iam = boto3.client('iam')
        self.dynamodb = boto3.resource('dynamodb')
        
    def _load_permissions(self):
        """Load permissions from DynamoDB."""
        try:
            table = self.dynamodb.Table(self.config['permissions_table'])
            response = table.scan()
            self.permissions = response['Items']
        except Exception as e:
            self.logger.error(f"Failed to load permissions: {e}")
            self.permissions = []
            
    def check_permission(self, user_id: str, action: str, resource: str) -> bool:
        """
        Check if a user has permission to perform an action on a resource.
        
        Args:
            user_id: ID of the user
            action: Action to perform
            resource: Resource to act on
            
        Returns:
            True if permission is granted, False otherwise
        """
        try:
            # Get user's permissions
            user_permissions = self._get_user_permissions(user_id)
            
            # Check if user has required permission
            required_permission = f"{action}:{resource}"
            return required_permission in user_permissions
        except Exception as e:
            self.logger.error(f"Permission check failed: {e}")
            return False
            
    def _get_user_permissions(self, user_id: str) -> Set[str]:
        """
        Get all permissions for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Set of permissions
        """
        try:
            # Get user's groups
            groups = self._get_user_groups(user_id)
            
            # Get permissions for each group
            permissions = set()
            for group in groups:
                group_permissions = self._get_group_permissions(group)
                permissions.update(group_permissions)
                
            return permissions
        except Exception as e:
            self.logger.error(f"Failed to get user permissions: {e}")
            return set()
            
    def _get_user_groups(self, user_id: str) -> List[str]:
        """
        Get groups a user belongs to.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of group names
        """
        try:
            table = self.dynamodb.Table(self.config['user_groups_table'])
            response = table.get_item(Key={'user_id': user_id})
            return response.get('Item', {}).get('groups', [])
        except Exception as e:
            self.logger.error(f"Failed to get user groups: {e}")
            return []
            
    def _get_group_permissions(self, group: str) -> Set[str]:
        """
        Get permissions for a group.
        
        Args:
            group: Group name
            
        Returns:
            Set of permissions
        """
        try:
            table = self.dynamodb.Table(self.config['group_permissions_table'])
            response = table.get_item(Key={'group': group})
            return set(response.get('Item', {}).get('permissions', []))
        except Exception as e:
            self.logger.error(f"Failed to get group permissions: {e}")
            return set()


class MCPComplianceLayer:
    """
    Main MCP compliance layer for the Tool Management Service.
    
    This class coordinates security, audit logging, and access control.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the MCP compliance layer.
        
        Args:
            config: Configuration for the compliance layer
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.security = SecurityManager(config.get('security', {}))
        self.audit = AuditLogger(config.get('audit', {}))
        self.access = AccessController(config.get('access', {}))
        
    def validate_request(self, token: str, action: str, resource: str) -> bool:
        """
        Validate a request against MCP compliance requirements.
        
        Args:
            token: Authentication token
            action: Action to perform
            resource: Resource to act on
            
        Returns:
            True if request is valid, False otherwise
        """
        try:
            # Verify token
            payload = self.security.verify_token(token)
            user_id = payload['user_id']
            
            # Check permissions
            if not self.access.check_permission(user_id, action, resource):
                self.audit.log_event(
                    'access_denied',
                    user_id,
                    action,
                    resource,
                    {'reason': 'insufficient_permissions'}
                )
                return False
                
            # Log successful access
            self.audit.log_event(
                'access_granted',
                user_id,
                action,
                resource
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Request validation failed: {e}")
            return False
            
    def encrypt_sensitive_data(self, data: Dict[str, Any]) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
        """
        return self.security.encrypt_data(data)
        
    def decrypt_sensitive_data(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data
            
        Returns:
            Decrypted data
        """
        return self.security.decrypt_data(encrypted_data)
        
    def log_security_event(self, event_type: str, user_id: str, action: str,
                          resource: str, details: Dict[str, Any] = None) -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of event
            user_id: ID of the user
            action: Action performed
            resource: Resource affected
            details: Additional event details
        """
        self.audit.log_event(event_type, user_id, action, resource, details) 