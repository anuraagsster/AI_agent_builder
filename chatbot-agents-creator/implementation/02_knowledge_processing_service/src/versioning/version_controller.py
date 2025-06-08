from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import copy

class VersionController:
    """
    Controls versioning of knowledge items.
    
    This class manages versions of knowledge items, allowing for tracking changes,
    rolling back to previous versions, and comparing versions.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the version controller.
        
        Args:
            config: Configuration dictionary with the following keys:
                - max_versions: Maximum number of versions to keep per item
                - auto_snapshot: Whether to automatically create snapshots
                - snapshot_interval: Interval between automatic snapshots
        """
        self.config = config or {}
        self.max_versions = self.config.get('max_versions', 10)
        self.auto_snapshot = self.config.get('auto_snapshot', True)
        self.snapshot_interval = self.config.get('snapshot_interval', 3600)  # 1 hour
        
        # Version storage
        self.versions = {}  # item_id -> list of versions
        self.current_versions = {}  # item_id -> current version number
        self.last_snapshot = {}  # item_id -> timestamp of last snapshot
        
    def create_version(self, item_id: str, content: Any, metadata: Dict[str, Any] = None) -> int:
        """
        Create a new version of an item.
        
        Args:
            item_id: Unique identifier for the item
            content: Content of the item
            metadata: Optional metadata for the version
            
        Returns:
            Version number
        """
        if item_id not in self.versions:
            self.versions[item_id] = []
            self.current_versions[item_id] = 0
            
        # Create version metadata
        version_metadata = metadata or {}
        version_metadata.update({
            'timestamp': datetime.now().isoformat(),
            'version': self.current_versions[item_id] + 1
        })
        
        # Create version
        version = {
            'content': copy.deepcopy(content),
            'metadata': version_metadata
        }
        
        # Add version to list
        self.versions[item_id].append(version)
        
        # Update current version
        self.current_versions[item_id] += 1
        
        # Limit number of versions if needed
        if len(self.versions[item_id]) > self.max_versions:
            self.versions[item_id] = self.versions[item_id][-self.max_versions:]
            
        # Update last snapshot timestamp
        self.last_snapshot[item_id] = datetime.now().timestamp()
        
        return self.current_versions[item_id]
        
    def get_version(self, item_id: str, version: int = None) -> Tuple[Any, Dict[str, Any]]:
        """
        Get a specific version of an item.
        
        Args:
            item_id: Unique identifier for the item
            version: Version number to get (None for current version)
            
        Returns:
            Tuple of (content, metadata)
        """
        if item_id not in self.versions:
            raise KeyError(f"Item with ID {item_id} not found")
            
        if version is None:
            # Get current version
            version = self.current_versions[item_id]
            
        if version <= 0 or version > self.current_versions[item_id]:
            raise ValueError(f"Invalid version number: {version}")
            
        # Get version from list
        version_index = version - 1
        version_data = self.versions[item_id][version_index]
        
        return copy.deepcopy(version_data['content']), copy.deepcopy(version_data['metadata'])
        
    def get_current_version(self, item_id: str) -> int:
        """
        Get the current version number of an item.
        
        Args:
            item_id: Unique identifier for the item
            
        Returns:
            Current version number
        """
        if item_id not in self.current_versions:
            raise KeyError(f"Item with ID {item_id} not found")
            
        return self.current_versions[item_id]
        
    def list_versions(self, item_id: str) -> List[Dict[str, Any]]:
        """
        List all versions of an item.
        
        Args:
            item_id: Unique identifier for the item
            
        Returns:
            List of version metadata
        """
        if item_id not in self.versions:
            raise KeyError(f"Item with ID {item_id} not found")
            
        return [version['metadata'] for version in self.versions[item_id]]
        
    def rollback(self, item_id: str, version: int) -> Tuple[Any, Dict[str, Any]]:
        """
        Roll back to a previous version of an item.
        
        This creates a new version with the content of the specified version.
        
        Args:
            item_id: Unique identifier for the item
            version: Version number to roll back to
            
        Returns:
            Tuple of (content, metadata) of the new version
        """
        if item_id not in self.versions:
            raise KeyError(f"Item with ID {item_id} not found")
            
        if version <= 0 or version > self.current_versions[item_id]:
            raise ValueError(f"Invalid version number: {version}")
            
        # Get version from list
        version_index = version - 1
        version_data = self.versions[item_id][version_index]
        
        # Create new version with rollback metadata
        rollback_metadata = {
            'rollback_from': self.current_versions[item_id],
            'rollback_to': version
        }
        
        # Create new version
        new_version = self.create_version(
            item_id,
            version_data['content'],
            rollback_metadata
        )
        
        return self.get_version(item_id, new_version)
        
    def compare_versions(self, item_id: str, version1: int, version2: int) -> Dict[str, Any]:
        """
        Compare two versions of an item.
        
        Args:
            item_id: Unique identifier for the item
            version1: First version number
            version2: Second version number
            
        Returns:
            Comparison result
        """
        if item_id not in self.versions:
            raise KeyError(f"Item with ID {item_id} not found")
            
        if version1 <= 0 or version1 > self.current_versions[item_id]:
            raise ValueError(f"Invalid version number: {version1}")
            
        if version2 <= 0 or version2 > self.current_versions[item_id]:
            raise ValueError(f"Invalid version number: {version2}")
            
        # Get versions from list
        version1_index = version1 - 1
        version2_index = version2 - 1
        
        version1_data = self.versions[item_id][version1_index]
        version2_data = self.versions[item_id][version2_index]
        
        # Compare versions
        # In a real implementation, this would use a proper diff algorithm
        # For now, just return a simple comparison
        return {
            'version1': version1,
            'version2': version2,
            'timestamp1': version1_data['metadata'].get('timestamp'),
            'timestamp2': version2_data['metadata'].get('timestamp'),
            'is_same_content': version1_data['content'] == version2_data['content']
        }
        
    def delete_item(self, item_id: str) -> bool:
        """
        Delete all versions of an item.
        
        Args:
            item_id: Unique identifier for the item
            
        Returns:
            True if successful, False otherwise
        """
        if item_id not in self.versions:
            return False
            
        try:
            del self.versions[item_id]
            del self.current_versions[item_id]
            
            if item_id in self.last_snapshot:
                del self.last_snapshot[item_id]
                
            return True
        except Exception as e:
            print(f"Error deleting item: {str(e)}")
            return False
            
    def check_snapshot_needed(self, item_id: str, content: Any) -> bool:
        """
        Check if a snapshot is needed for an item.
        
        Args:
            item_id: Unique identifier for the item
            content: Current content of the item
            
        Returns:
            True if snapshot is needed, False otherwise
        """
        if not self.auto_snapshot:
            return False
            
        if item_id not in self.last_snapshot:
            return True
            
        # Check if enough time has passed since last snapshot
        now = datetime.now().timestamp()
        time_since_last = now - self.last_snapshot[item_id]
        
        if time_since_last >= self.snapshot_interval:
            # Check if content has changed
            if item_id in self.versions:
                current_version = self.versions[item_id][-1]
                return current_version['content'] != content
                
            return True
            
        return False
        
    def create_snapshot_if_needed(self, item_id: str, content: Any, metadata: Dict[str, Any] = None) -> Optional[int]:
        """
        Create a snapshot of an item if needed.
        
        Args:
            item_id: Unique identifier for the item
            content: Content of the item
            metadata: Optional metadata for the version
            
        Returns:
            Version number if snapshot was created, None otherwise
        """
        if self.check_snapshot_needed(item_id, content):
            snapshot_metadata = metadata or {}
            snapshot_metadata['snapshot'] = True
            
            return self.create_version(item_id, content, snapshot_metadata)
            
        return None