"""
Security Manager for MCP Compliance Layer.

This module handles encryption, authentication, and authorization for the Tool Management Service.
"""

import logging
import json
import time
from typing import Dict, Any, Set
import boto3
from botocore.exceptions import ClientError
import jwt
from cryptography.fernet import Fernet
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