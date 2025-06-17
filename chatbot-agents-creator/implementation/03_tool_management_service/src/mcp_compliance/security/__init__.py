"""
Security package for the MCP compliance layer.

This package provides security functionality for the Tool Management Service, including:
- Data encryption and decryption using AWS KMS
- JWT token generation and verification
- Secure key management
"""

from .security_manager import SecurityManager

__all__ = ['SecurityManager'] 