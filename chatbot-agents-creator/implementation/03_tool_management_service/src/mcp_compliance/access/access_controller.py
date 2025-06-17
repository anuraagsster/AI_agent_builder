"""
Access Controller for MCP Compliance Layer.

This module handles access control and permission management for the Tool Management Service.
"""

import logging
from typing import Dict, Any, List, Set
import boto3
from botocore.exceptions import ClientError

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