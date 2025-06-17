"""
MCP Compliance Layer Core.

This module coordinates security, audit logging, and access control for the Tool Management Service.
"""

import logging
from typing import Dict, Any
from ..security.security_manager import SecurityManager
from ..audit.audit_logger import AuditLogger
from ..access.access_controller import AccessController

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