from typing import Dict, Any, List, Optional
import numpy as np
from .pipeline import PipelineStage

class EmbeddingGenerator(PipelineStage):
    """
    Pipeline stage for generating embeddings from content.
    
    This stage creates vector embeddings for content chunks that can be
    used for semantic search and retrieval.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the embedding generator.
        
        Args:
            config: Configuration dictionary with the following keys:
                - model_name: Name of the embedding model to use
                - embedding_dim: Dimension of the embeddings
                - batch_size: Batch size for embedding generation
                - cache_embeddings: Whether to cache embeddings
                - normalize_embeddings: Whether to normalize embeddings
        """
        super().__init__(config)
        self.model_name = self.config.get('model_name', 'default')
        self.embedding_dim = self.config.get('embedding_dim', 768)
        self.batch_size = self.config.get('batch_size', 32)
        self.cache_embeddings = self.config.get('cache_embeddings', True)
        self.normalize_embeddings = self.config.get('normalize_embeddings', True)
        self.embedding_model = None
        self.embedding_cache = {}
        
    def process(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of items by generating embeddings.
        
        Args:
            items: List of items to process
            
        Returns:
            Processed items with embeddings
        """
        results = []
        
        # Ensure the embedding model is loaded
        if not self.embedding_model:
            self._load_embedding_model()
            
        for item in items:
            try:
                processed_item = item.copy()
                
                # Generate embeddings for the item
                if 'chunks' in item:
                    # Generate embeddings for each chunk
                    chunks_with_embeddings = []
                    
                    for chunk in item['chunks']:
                        chunk_with_embedding = chunk.copy()
                        chunk_with_embedding['embedding'] = self._generate_embedding(chunk['content'])
                        chunks_with_embeddings.append(chunk_with_embedding)
                        
                    processed_item['chunks'] = chunks_with_embeddings
                elif 'content' in item:
                    # Generate embedding for the entire content
                    processed_item['embedding'] = self._generate_embedding(item['content'])
                    
                results.append(processed_item)
            except Exception as e:
                # In a real implementation, this would log the error
                print(f"Error generating embeddings: {str(e)}")
                results.append(item)  # Keep the original item
                
        return results
        
    def _load_embedding_model(self):
        """
        Load the embedding model.
        
        In a real implementation, this would load a model from a library like
        sentence-transformers, OpenAI, etc.
        For now, this is just a placeholder.
        """
        # Placeholder implementation
        self.embedding_model = "MockEmbeddingModel"
        print(f"Loaded embedding model: {self.model_name}")
        
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a text.
        
        In a real implementation, this would use the loaded model.
        For now, this is just a placeholder that generates random vectors.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector
        """
        # Check cache first if enabled
        if self.cache_embeddings:
            cache_key = f"{self.model_name}:{text[:100]}"
            if cache_key in self.embedding_cache:
                return self.embedding_cache[cache_key]
                
        # In a real implementation, this would use the model
        # For now, generate a deterministic random vector based on the text
        np.random.seed(hash(text) % 2**32)
        embedding = np.random.randn(self.embedding_dim).tolist()
        
        # Normalize if enabled
        if self.normalize_embeddings:
            embedding = self._normalize_vector(embedding)
            
        # Cache the result if enabled
        if self.cache_embeddings:
            cache_key = f"{self.model_name}:{text[:100]}"
            self.embedding_cache[cache_key] = embedding
            
        return embedding
        
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """
        Normalize a vector to unit length.
        
        Args:
            vector: Vector to normalize
            
        Returns:
            Normalized vector
        """
        norm = np.sqrt(sum(x**2 for x in vector))
        if norm > 0:
            return [x / norm for x in vector]
        return vector
        
    def _batch_texts(self, texts: List[str]) -> List[List[str]]:
        """
        Split a list of texts into batches.
        
        Args:
            texts: List of texts to batch
            
        Returns:
            List of batches
        """
        return [texts[i:i + self.batch_size] for i in range(0, len(texts), self.batch_size)]
        
    def validate(self) -> Dict[str, Any]:
        """
        Validate the embedding generator configuration.
        
        Returns:
            Dictionary with validation results
        """
        result = super().validate()
        
        # Check embedding dimension
        if self.embedding_dim <= 0:
            result['valid'] = False
            result['errors'] = result.get('errors', []) + ["Embedding dimension must be positive"]
            
        # Check batch size
        if self.batch_size <= 0:
            result['valid'] = False
            result['errors'] = result.get('errors', []) + ["Batch size must be positive"]
            
        # Add model information
        result['model_name'] = self.model_name
        result['embedding_dim'] = self.embedding_dim
        
        return result