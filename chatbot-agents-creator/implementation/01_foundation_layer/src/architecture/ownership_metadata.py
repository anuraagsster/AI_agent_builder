"""
Ownership Metadata Component

This module provides functionality for tracking and managing ownership of components
in the system. It defines the ownership metadata schema and provides utility functions
for ownership validation and management.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OwnershipType(Enum):
    """Enum for ownership types"""
    SYSTEM = "system"
    CLIENT = "client"
    SHARED = "shared"

class OwnershipMetadata:
    """
    Class for managing ownership metadata for components
    
    This class provides functionality for validating ownership,
    managing ownership transfers, and enforcing access control.
    """
    
    def __init__(self):
        """Initialize the ownership metadata manager"""
        self.logger = logging.getLogger(__name__)
    
    def validate_ownership(self, owner_id: Optional[str], requester_id: Optional[str]) -> bool:
        """
        Validate if a requester has access to a component based on ownership
        
        Args:
            owner_id: Owner ID of the component (None for system components)
            requester_id: ID of the requester
            
        Returns:
            True if access is allowed, False otherwise
        """
        # System components (no owner_id) can be accessed by anyone
        if owner_id is None:
            return True
            
        # Client components can only be accessed by their owner
        if owner_id == requester_id:
            return True
            
        # Access denied
        return False
    
    def transfer_ownership(self, current_owner_id: str, new_owner_id: str, 
                          component_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transfer ownership of a component from one owner to another
        
        Args:
            current_owner_id: Current owner ID
            new_owner_id: New owner ID
            component_metadata: Component metadata dictionary
            
        Returns:
            Updated component metadata with new ownership
        """
        # Validate current ownership
        if component_metadata.get('owner_id') != current_owner_id:
            self.logger.warning(f"Ownership transfer failed: {current_owner_id} is not the current owner")
            return component_metadata
            
        # Create updated metadata
        updated_metadata = component_metadata.copy()
        updated_metadata['owner_id'] = new_owner_id
        updated_metadata['ownership_transferred_at'] = datetime.now().isoformat()
        updated_metadata['previous_owner_id'] = current_owner_id
        
        self.logger.info(f"Ownership transferred from {current_owner_id} to {new_owner_id}")
        return updated_metadata
    
    def create_ownership_metadata(self, owner_id: Optional[str] = None, 
                                 ownership_type: Union[OwnershipType, str] = OwnershipType.SYSTEM,
                                 exportable: bool = False) -> Dict[str, Any]:
        """
        Create ownership metadata for a component
        
        Args:
            owner_id: Owner ID (None for system components)
            ownership_type: Type of ownership (system, client, shared)
            exportable: Whether the component can be exported
            
        Returns:
            Dictionary with ownership metadata
        """
        # Convert string to enum if needed
        if isinstance(ownership_type, str):
            try:
                ownership_type = OwnershipType(ownership_type)
            except ValueError:
                self.logger.warning(f"Invalid ownership type: {ownership_type}, defaulting to SYSTEM")
                ownership_type = OwnershipType.SYSTEM
        
        # For client ownership, owner_id is required
        if ownership_type == OwnershipType.CLIENT and owner_id is None:
            self.logger.warning("Client ownership requires an owner_id, defaulting to SYSTEM ownership")
            ownership_type = OwnershipType.SYSTEM
        
        # For system ownership, owner_id should be None
        if ownership_type == OwnershipType.SYSTEM:
            owner_id = None
            
        # Create metadata
        metadata = {
            'owner_id': owner_id,
            'ownership_type': ownership_type.value,
            'exportable': exportable,
            'created_at': datetime.now().isoformat()
        }
        
        return metadata
    
    def is_exportable(self, metadata: Dict[str, Any]) -> bool:
        """
        Check if a component is exportable based on its metadata
        
        Args:
            metadata: Component metadata
            
        Returns:
            True if the component is exportable, False otherwise
        """
        # Check if explicitly marked as exportable
        if 'exportable' in metadata and metadata['exportable']:
            return True
            
        # Client-owned components are exportable by default
        if 'ownership_type' in metadata and metadata['ownership_type'] == OwnershipType.CLIENT.value:
            return True
            
        # Otherwise not exportable
        return False
    
    def get_ownership_summary(self, components_by_owner: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Generate a summary of component ownership
        
        Args:
            components_by_owner: Dictionary mapping owner IDs to lists of component IDs
            
        Returns:
            Dictionary with ownership summary statistics
        """
        total_components = sum(len(components) for components in components_by_owner.values())
        system_components = len(components_by_owner.get(None, []))
        client_components = total_components - system_components
        
        return {
            'total_components': total_components,
            'system_components': system_components,
            'client_components': client_components,
            'client_count': len(components_by_owner) - (1 if None in components_by_owner else 0),
            'components_by_owner': {
                owner_id or 'system': len(components)
                for owner_id, components in components_by_owner.items()
            }
        }