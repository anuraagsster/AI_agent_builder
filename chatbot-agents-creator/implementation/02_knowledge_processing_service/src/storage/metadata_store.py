from typing import Dict, Any, List, Optional, Set, Tuple
from abc import ABC, abstractmethod

class MetadataStore(ABC):
    """
    Abstract base class for metadata storage backends.
    
    This class defines the interface for storing and retrieving metadata
    about knowledge items.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the metadata store.
        
        Args:
            config: Configuration dictionary for the metadata store
        """
        self.config = config or {}
        
    @abstractmethod
    def add(self, id: str, metadata: Dict[str, Any]) -> bool:
        """
        Add metadata to the store.
        
        Args:
            id: Unique identifier for the metadata
            metadata: Metadata to store
            
        Returns:
            True if successful, False otherwise
        """
        pass
        
    @abstractmethod
    def get(self, id: str) -> Dict[str, Any]:
        """
        Get metadata from the store by ID.
        
        Args:
            id: Unique identifier for the metadata
            
        Returns:
            Stored metadata
        """
        pass
        
    @abstractmethod
    def update(self, id: str, metadata: Dict[str, Any], merge: bool = True) -> bool:
        """
        Update metadata in the store.
        
        Args:
            id: Unique identifier for the metadata
            metadata: New metadata to store
            merge: Whether to merge with existing metadata or replace it
            
        Returns:
            True if successful, False otherwise
        """
        pass
        
    @abstractmethod
    def delete(self, id: str) -> bool:
        """
        Delete metadata from the store.
        
        Args:
            id: Unique identifier for the metadata
            
        Returns:
            True if successful, False otherwise
        """
        pass
        
    @abstractmethod
    def search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for metadata matching a query.
        
        Args:
            query: Query to match against metadata
            
        Returns:
            List of matching metadata items with their IDs
        """
        pass
        
    @abstractmethod
    def list_all(self) -> List[str]:
        """
        List all metadata IDs in the store.
        
        Returns:
            List of all metadata IDs
        """
        pass


class InMemoryMetadataStore(MetadataStore):
    """
    In-memory implementation of a metadata store.
    
    This is a simple implementation that stores metadata in memory.
    It's suitable for development and testing, but not for production use.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the in-memory metadata store.
        """
        super().__init__(config)
        self.metadata = {}  # id -> metadata
        
    def add(self, id: str, metadata: Dict[str, Any]) -> bool:
        """
        Add metadata to the store.
        
        Args:
            id: Unique identifier for the metadata
            metadata: Metadata to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.metadata[id] = metadata.copy()
            return True
        except Exception as e:
            print(f"Error adding metadata: {str(e)}")
            return False
        
    def get(self, id: str) -> Dict[str, Any]:
        """
        Get metadata from the store by ID.
        
        Args:
            id: Unique identifier for the metadata
            
        Returns:
            Stored metadata
        """
        if id not in self.metadata:
            raise KeyError(f"Metadata with ID {id} not found")
            
        return self.metadata[id].copy()
        
    def update(self, id: str, metadata: Dict[str, Any], merge: bool = True) -> bool:
        """
        Update metadata in the store.
        
        Args:
            id: Unique identifier for the metadata
            metadata: New metadata to store
            merge: Whether to merge with existing metadata or replace it
            
        Returns:
            True if successful, False otherwise
        """
        if id not in self.metadata:
            return False
            
        try:
            if merge:
                # Merge with existing metadata
                self.metadata[id].update(metadata)
            else:
                # Replace existing metadata
                self.metadata[id] = metadata.copy()
                
            return True
        except Exception as e:
            print(f"Error updating metadata: {str(e)}")
            return False
        
    def delete(self, id: str) -> bool:
        """
        Delete metadata from the store.
        
        Args:
            id: Unique identifier for the metadata
            
        Returns:
            True if successful, False otherwise
        """
        if id not in self.metadata:
            return False
            
        try:
            del self.metadata[id]
            return True
        except Exception as e:
            print(f"Error deleting metadata: {str(e)}")
            return False
        
    def search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for metadata matching a query.
        
        Args:
            query: Query to match against metadata
            
        Returns:
            List of matching metadata items with their IDs
        """
        results = []
        
        for id, metadata in self.metadata.items():
            if self._matches_query(metadata, query):
                result = metadata.copy()
                result['id'] = id
                results.append(result)
                
        return results
        
    def list_all(self) -> List[str]:
        """
        List all metadata IDs in the store.
        
        Returns:
            List of all metadata IDs
        """
        return list(self.metadata.keys())
        
    def _matches_query(self, metadata: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """
        Check if metadata matches a query.
        
        Args:
            metadata: Metadata to check
            query: Query to match against
            
        Returns:
            True if metadata matches query, False otherwise
        """
        for key, value in query.items():
            # Handle nested keys (e.g., "source.type")
            if "." in key:
                parts = key.split(".")
                current = metadata
                for part in parts[:-1]:
                    if part not in current or not isinstance(current[part], dict):
                        return False
                    current = current[part]
                    
                if parts[-1] not in current or current[parts[-1]] != value:
                    return False
            elif key not in metadata or metadata[key] != value:
                return False
                
        return True


class IndexedMetadataStore(InMemoryMetadataStore):
    """
    In-memory metadata store with indexing for faster searches.
    
    This extends the basic in-memory store with indexes for common search fields.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the indexed metadata store.
        
        Args:
            config: Configuration dictionary with the following keys:
                - indexed_fields: List of fields to index
        """
        super().__init__(config)
        self.indexed_fields = self.config.get('indexed_fields', [])
        self.indexes = {field: {} for field in self.indexed_fields}
        
    def add(self, id: str, metadata: Dict[str, Any]) -> bool:
        """
        Add metadata to the store and update indexes.
        
        Args:
            id: Unique identifier for the metadata
            metadata: Metadata to store
            
        Returns:
            True if successful, False otherwise
        """
        success = super().add(id, metadata)
        
        if success:
            self._update_indexes(id, metadata)
            
        return success
        
    def update(self, id: str, metadata: Dict[str, Any], merge: bool = True) -> bool:
        """
        Update metadata in the store and update indexes.
        
        Args:
            id: Unique identifier for the metadata
            metadata: New metadata to store
            merge: Whether to merge with existing metadata or replace it
            
        Returns:
            True if successful, False otherwise
        """
        if id not in self.metadata:
            return False
            
        # Remove from indexes first
        self._remove_from_indexes(id)
        
        success = super().update(id, metadata, merge)
        
        if success:
            self._update_indexes(id, self.metadata[id])
            
        return success
        
    def delete(self, id: str) -> bool:
        """
        Delete metadata from the store and update indexes.
        
        Args:
            id: Unique identifier for the metadata
            
        Returns:
            True if successful, False otherwise
        """
        if id not in self.metadata:
            return False
            
        # Remove from indexes first
        self._remove_from_indexes(id)
        
        return super().delete(id)
        
    def search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for metadata matching a query, using indexes when possible.
        
        Args:
            query: Query to match against metadata
            
        Returns:
            List of matching metadata items with their IDs
        """
        # Check if we can use an index for this query
        indexed_key = None
        for key in query:
            if key in self.indexed_fields:
                indexed_key = key
                break
                
        if indexed_key is not None:
            # Use index for initial filtering
            value = query[indexed_key]
            if value in self.indexes[indexed_key]:
                candidate_ids = self.indexes[indexed_key][value]
                
                # Filter candidates by the rest of the query
                results = []
                for id in candidate_ids:
                    metadata = self.metadata[id]
                    if self._matches_query(metadata, query):
                        result = metadata.copy()
                        result['id'] = id
                        results.append(result)
                        
                return results
                
        # Fall back to full scan if no suitable index
        return super().search(query)
        
    def _update_indexes(self, id: str, metadata: Dict[str, Any]) -> None:
        """
        Update indexes for a metadata item.
        
        Args:
            id: Unique identifier for the metadata
            metadata: Metadata to index
        """
        for field in self.indexed_fields:
            if field in metadata:
                value = metadata[field]
                
                # Handle different types of values
                if isinstance(value, (str, int, float, bool)) or value is None:
                    # Simple value
                    if value not in self.indexes[field]:
                        self.indexes[field][value] = set()
                    self.indexes[field][value].add(id)
                elif isinstance(value, list):
                    # List of values
                    for item in value:
                        if item not in self.indexes[field]:
                            self.indexes[field][item] = set()
                        self.indexes[field][item].add(id)
                        
    def _remove_from_indexes(self, id: str) -> None:
        """
        Remove a metadata item from all indexes.
        
        Args:
            id: Unique identifier for the metadata to remove
        """
        metadata = self.metadata.get(id)
        if not metadata:
            return
            
        for field in self.indexed_fields:
            if field in metadata:
                value = metadata[field]
                
                # Handle different types of values
                if isinstance(value, (str, int, float, bool)) or value is None:
                    # Simple value
                    if value in self.indexes[field]:
                        self.indexes[field][value].discard(id)
                elif isinstance(value, list):
                    # List of values
                    for item in value:
                        if item in self.indexes[field]:
                            self.indexes[field][item].discard(id)