from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
import json
import copy

class ChangeTracker:
    """
    Tracks changes to knowledge items.
    
    This class tracks changes to knowledge items, recording what changed,
    when it changed, and who made the change.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the change tracker.
        
        Args:
            config: Configuration dictionary with the following keys:
                - track_content_changes: Whether to track content changes
                - track_metadata_changes: Whether to track metadata changes
                - max_changes: Maximum number of changes to keep per item
        """
        self.config = config or {}
        self.track_content_changes = self.config.get('track_content_changes', True)
        self.track_metadata_changes = self.config.get('track_metadata_changes', True)
        self.max_changes = self.config.get('max_changes', 100)
        
        # Change storage
        self.changes = {}  # item_id -> list of changes
        
    def record_change(self, item_id: str, change_type: str, details: Dict[str, Any], user_id: str = None) -> int:
        """
        Record a change to an item.
        
        Args:
            item_id: Unique identifier for the item
            change_type: Type of change (e.g., 'create', 'update', 'delete')
            details: Details of the change
            user_id: Optional identifier for the user who made the change
            
        Returns:
            Change ID
        """
        if item_id not in self.changes:
            self.changes[item_id] = []
            
        # Create change record
        change = {
            'id': len(self.changes[item_id]) + 1,
            'timestamp': datetime.now().isoformat(),
            'type': change_type,
            'details': copy.deepcopy(details),
            'user_id': user_id
        }
        
        # Add change to list
        self.changes[item_id].append(change)
        
        # Limit number of changes if needed
        if len(self.changes[item_id]) > self.max_changes:
            self.changes[item_id] = self.changes[item_id][-self.max_changes:]
            
        return change['id']
        
    def get_changes(self, item_id: str, limit: int = None, change_type: str = None) -> List[Dict[str, Any]]:
        """
        Get changes for an item.
        
        Args:
            item_id: Unique identifier for the item
            limit: Maximum number of changes to return
            change_type: Optional type of changes to filter by
            
        Returns:
            List of changes
        """
        if item_id not in self.changes:
            return []
            
        # Filter changes by type if specified
        if change_type:
            changes = [c for c in self.changes[item_id] if c['type'] == change_type]
        else:
            changes = self.changes[item_id]
            
        # Sort changes by timestamp (newest first)
        changes = sorted(changes, key=lambda c: c['timestamp'], reverse=True)
        
        # Limit number of changes if specified
        if limit:
            changes = changes[:limit]
            
        return copy.deepcopy(changes)
        
    def track_content_change(self, item_id: str, old_content: Any, new_content: Any, user_id: str = None) -> Optional[int]:
        """
        Track a change to item content.
        
        Args:
            item_id: Unique identifier for the item
            old_content: Previous content
            new_content: New content
            user_id: Optional identifier for the user who made the change
            
        Returns:
            Change ID if change was recorded, None otherwise
        """
        if not self.track_content_changes:
            return None
            
        # Detect if content actually changed
        if old_content == new_content:
            return None
            
        # Record the change
        details = {
            'old_content_hash': self._hash_content(old_content),
            'new_content_hash': self._hash_content(new_content),
            'diff_summary': self._generate_diff_summary(old_content, new_content)
        }
        
        return self.record_change(item_id, 'content_change', details, user_id)
        
    def track_metadata_change(self, item_id: str, old_metadata: Dict[str, Any], new_metadata: Dict[str, Any], user_id: str = None) -> Optional[int]:
        """
        Track a change to item metadata.
        
        Args:
            item_id: Unique identifier for the item
            old_metadata: Previous metadata
            new_metadata: New metadata
            user_id: Optional identifier for the user who made the change
            
        Returns:
            Change ID if change was recorded, None otherwise
        """
        if not self.track_metadata_changes:
            return None
            
        # Detect what changed in metadata
        added_keys, removed_keys, modified_keys = self._compare_metadata(old_metadata, new_metadata)
        
        if not added_keys and not removed_keys and not modified_keys:
            return None
            
        # Record the change
        details = {
            'added_keys': list(added_keys),
            'removed_keys': list(removed_keys),
            'modified_keys': list(modified_keys)
        }
        
        return self.record_change(item_id, 'metadata_change', details, user_id)
        
    def track_creation(self, item_id: str, content: Any, metadata: Dict[str, Any], user_id: str = None) -> int:
        """
        Track the creation of an item.
        
        Args:
            item_id: Unique identifier for the item
            content: Initial content
            metadata: Initial metadata
            user_id: Optional identifier for the user who created the item
            
        Returns:
            Change ID
        """
        details = {
            'content_hash': self._hash_content(content),
            'metadata_keys': list(metadata.keys()) if metadata else []
        }
        
        return self.record_change(item_id, 'create', details, user_id)
        
    def track_deletion(self, item_id: str, user_id: str = None) -> int:
        """
        Track the deletion of an item.
        
        Args:
            item_id: Unique identifier for the item
            user_id: Optional identifier for the user who deleted the item
            
        Returns:
            Change ID
        """
        return self.record_change(item_id, 'delete', {}, user_id)
        
    def get_change_history(self, item_id: str) -> List[Dict[str, Any]]:
        """
        Get the complete change history for an item.
        
        Args:
            item_id: Unique identifier for the item
            
        Returns:
            List of changes in chronological order
        """
        if item_id not in self.changes:
            return []
            
        # Sort changes by timestamp (oldest first)
        changes = sorted(self.changes[item_id], key=lambda c: c['timestamp'])
        
        return copy.deepcopy(changes)
        
    def get_recent_changes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent changes across all items.
        
        Args:
            limit: Maximum number of changes to return
            
        Returns:
            List of recent changes
        """
        all_changes = []
        
        # Collect changes from all items
        for item_id, item_changes in self.changes.items():
            for change in item_changes:
                change_copy = copy.deepcopy(change)
                change_copy['item_id'] = item_id
                all_changes.append(change_copy)
                
        # Sort changes by timestamp (newest first)
        all_changes = sorted(all_changes, key=lambda c: c['timestamp'], reverse=True)
        
        # Limit number of changes
        return all_changes[:limit]
        
    def clear_changes(self, item_id: str) -> bool:
        """
        Clear all changes for an item.
        
        Args:
            item_id: Unique identifier for the item
            
        Returns:
            True if successful, False otherwise
        """
        if item_id not in self.changes:
            return False
            
        try:
            del self.changes[item_id]
            return True
        except Exception as e:
            print(f"Error clearing changes: {str(e)}")
            return False
            
    def _hash_content(self, content: Any) -> str:
        """
        Generate a hash of content.
        
        In a real implementation, this would use a proper hashing algorithm.
        For now, just use a simple string representation.
        
        Args:
            content: Content to hash
            
        Returns:
            Hash of the content
        """
        try:
            # Try to convert to JSON
            content_str = json.dumps(content, sort_keys=True)
        except:
            # Fall back to string representation
            content_str = str(content)
            
        # In a real implementation, this would use a proper hash function
        # For now, just return a truncated string
        return content_str[:100] + "..." if len(content_str) > 100 else content_str
        
    def _generate_diff_summary(self, old_content: Any, new_content: Any) -> str:
        """
        Generate a summary of differences between old and new content.
        
        In a real implementation, this would use a proper diff algorithm.
        For now, just return a simple message.
        
        Args:
            old_content: Old content
            new_content: New content
            
        Returns:
            Summary of differences
        """
        # In a real implementation, this would generate a proper diff
        return "Content changed"
        
    def _compare_metadata(self, old_metadata: Dict[str, Any], new_metadata: Dict[str, Any]) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        Compare old and new metadata to find changes.
        
        Args:
            old_metadata: Old metadata
            new_metadata: New metadata
            
        Returns:
            Tuple of (added_keys, removed_keys, modified_keys)
        """
        old_keys = set(old_metadata.keys())
        new_keys = set(new_metadata.keys())
        
        added_keys = new_keys - old_keys
        removed_keys = old_keys - new_keys
        
        # Find modified keys (keys that exist in both but have different values)
        common_keys = old_keys.intersection(new_keys)
        modified_keys = {key for key in common_keys if old_metadata[key] != new_metadata[key]}
        
        return added_keys, removed_keys, modified_keys