from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
from abc import ABC, abstractmethod

class VectorStore(ABC):
    """
    Abstract base class for vector storage backends.
    
    This class defines the interface for storing and retrieving vector embeddings.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the vector store.
        
        Args:
            config: Configuration dictionary for the vector store
        """
        self.config = config or {}
        
    @abstractmethod
    def add(self, id: str, vector: List[float], metadata: Dict[str, Any] = None) -> bool:
        """
        Add a vector to the store.
        
        Args:
            id: Unique identifier for the vector
            vector: The vector to store
            metadata: Optional metadata to store with the vector
            
        Returns:
            True if successful, False otherwise
        """
        pass
        
    @abstractmethod
    def add_batch(self, ids: List[str], vectors: List[List[float]], metadatas: List[Dict[str, Any]] = None) -> bool:
        """
        Add a batch of vectors to the store.
        
        Args:
            ids: List of unique identifiers for the vectors
            vectors: List of vectors to store
            metadatas: Optional list of metadata to store with the vectors
            
        Returns:
            True if successful, False otherwise
        """
        pass
        
    @abstractmethod
    def get(self, id: str) -> Tuple[List[float], Dict[str, Any]]:
        """
        Get a vector from the store by ID.
        
        Args:
            id: Unique identifier for the vector
            
        Returns:
            Tuple of (vector, metadata)
        """
        pass
        
    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 10, filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Vector to search for
            top_k: Number of results to return
            filter: Optional filter to apply to the search
            
        Returns:
            List of search results, each with id, vector, metadata, and score
        """
        pass
        
    @abstractmethod
    def delete(self, id: str) -> bool:
        """
        Delete a vector from the store.
        
        Args:
            id: Unique identifier for the vector
            
        Returns:
            True if successful, False otherwise
        """
        pass
        
    @abstractmethod
    def count(self) -> int:
        """
        Get the number of vectors in the store.
        
        Returns:
            Number of vectors
        """
        pass


class InMemoryVectorStore(VectorStore):
    """
    In-memory implementation of a vector store.
    
    This is a simple implementation that stores vectors in memory.
    It's suitable for development and testing, but not for production use.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the in-memory vector store.
        
        Args:
            config: Configuration dictionary with the following keys:
                - distance_metric: Distance metric to use ('cosine', 'euclidean', 'dot')
        """
        super().__init__(config)
        self.distance_metric = self.config.get('distance_metric', 'cosine')
        self.vectors = {}  # id -> vector
        self.metadatas = {}  # id -> metadata
        
    def add(self, id: str, vector: List[float], metadata: Dict[str, Any] = None) -> bool:
        """
        Add a vector to the store.
        
        Args:
            id: Unique identifier for the vector
            vector: The vector to store
            metadata: Optional metadata to store with the vector
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.vectors[id] = vector
            self.metadatas[id] = metadata or {}
            return True
        except Exception as e:
            print(f"Error adding vector: {str(e)}")
            return False
        
    def add_batch(self, ids: List[str], vectors: List[List[float]], metadatas: List[Dict[str, Any]] = None) -> bool:
        """
        Add a batch of vectors to the store.
        
        Args:
            ids: List of unique identifiers for the vectors
            vectors: List of vectors to store
            metadatas: Optional list of metadata to store with the vectors
            
        Returns:
            True if successful, False otherwise
        """
        if len(ids) != len(vectors):
            return False
            
        if metadatas and len(ids) != len(metadatas):
            return False
            
        try:
            for i, id in enumerate(ids):
                self.vectors[id] = vectors[i]
                self.metadatas[id] = metadatas[i] if metadatas else {}
            return True
        except Exception as e:
            print(f"Error adding batch of vectors: {str(e)}")
            return False
        
    def get(self, id: str) -> Tuple[List[float], Dict[str, Any]]:
        """
        Get a vector from the store by ID.
        
        Args:
            id: Unique identifier for the vector
            
        Returns:
            Tuple of (vector, metadata)
        """
        if id not in self.vectors:
            raise KeyError(f"Vector with ID {id} not found")
            
        return self.vectors[id], self.metadatas[id]
        
    def search(self, query_vector: List[float], top_k: int = 10, filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Vector to search for
            top_k: Number of results to return
            filter: Optional filter to apply to the search
            
        Returns:
            List of search results, each with id, vector, metadata, and score
        """
        if not self.vectors:
            return []
            
        results = []
        
        for id, vector in self.vectors.items():
            metadata = self.metadatas[id]
            
            # Apply filter if provided
            if filter and not self._apply_filter(metadata, filter):
                continue
                
            # Calculate similarity score
            score = self._calculate_similarity(query_vector, vector)
            
            results.append({
                'id': id,
                'vector': vector,
                'metadata': metadata,
                'score': score
            })
            
        # Sort by score (higher is better)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top_k results
        return results[:top_k]
        
    def delete(self, id: str) -> bool:
        """
        Delete a vector from the store.
        
        Args:
            id: Unique identifier for the vector
            
        Returns:
            True if successful, False otherwise
        """
        if id not in self.vectors:
            return False
            
        try:
            del self.vectors[id]
            del self.metadatas[id]
            return True
        except Exception as e:
            print(f"Error deleting vector: {str(e)}")
            return False
        
    def count(self) -> int:
        """
        Get the number of vectors in the store.
        
        Returns:
            Number of vectors
        """
        return len(self.vectors)
        
    def _calculate_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """
        Calculate similarity between two vectors.
        
        Args:
            vector1: First vector
            vector2: Second vector
            
        Returns:
            Similarity score (higher is more similar)
        """
        v1 = np.array(vector1)
        v2 = np.array(vector2)
        
        if self.distance_metric == 'cosine':
            # Cosine similarity
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 == 0 or norm2 == 0:
                return 0
            return np.dot(v1, v2) / (norm1 * norm2)
        elif self.distance_metric == 'euclidean':
            # Euclidean distance (converted to similarity)
            dist = np.linalg.norm(v1 - v2)
            return 1.0 / (1.0 + dist)
        elif self.distance_metric == 'dot':
            # Dot product
            return np.dot(v1, v2)
        else:
            # Default to cosine similarity
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 == 0 or norm2 == 0:
                return 0
            return np.dot(v1, v2) / (norm1 * norm2)
        
    def _apply_filter(self, metadata: Dict[str, Any], filter: Dict[str, Any]) -> bool:
        """
        Apply a filter to metadata.
        
        Args:
            metadata: Metadata to filter
            filter: Filter to apply
            
        Returns:
            True if metadata passes filter, False otherwise
        """
        for key, value in filter.items():
            if key not in metadata:
                return False
                
            if isinstance(value, list):
                # Check if metadata value is in the list
                if metadata[key] not in value:
                    return False
            elif metadata[key] != value:
                return False
                
        return True