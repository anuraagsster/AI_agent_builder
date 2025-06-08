from typing import Dict, Any, List, Optional
import re
from .pipeline import PipelineStage

class ContentStructurer(PipelineStage):
    """
    Pipeline stage for structuring content into chunks and segments.
    
    This stage breaks down content into manageable chunks, identifies
    sections, and extracts relationships between content pieces.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the content structurer.
        
        Args:
            config: Configuration dictionary with the following keys:
                - chunk_size: Target size for content chunks
                - chunk_overlap: Overlap between chunks
                - detect_sections: Whether to detect document sections
                - extract_relationships: Whether to extract relationships
                - chunking_strategy: Strategy for chunking ('fixed', 'semantic', 'hybrid')
        """
        super().__init__(config)
        self.chunk_size = self.config.get('chunk_size', 1000)
        self.chunk_overlap = self.config.get('chunk_overlap', 200)
        self.detect_sections = self.config.get('detect_sections', True)
        self.extract_relationships = self.config.get('extract_relationships', True)
        self.chunking_strategy = self.config.get('chunking_strategy', 'hybrid')
        
    def process(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of items by structuring their content.
        
        Args:
            items: List of items to process
            
        Returns:
            Processed items with structured content
        """
        results = []
        
        for item in items:
            try:
                if 'content' not in item:
                    # Skip items without content
                    results.append(item)
                    continue
                    
                # Create a new item to avoid modifying the original
                processed_item = item.copy()
                
                # Detect sections if enabled
                if self.detect_sections:
                    processed_item['sections'] = self._detect_sections(processed_item['content'])
                    
                # Chunk the content
                chunks = self._chunk_content(processed_item['content'])
                processed_item['chunks'] = chunks
                
                # Extract relationships if enabled
                if self.extract_relationships:
                    processed_item['relationships'] = self._extract_relationships(chunks)
                    
                results.append(processed_item)
            except Exception as e:
                # In a real implementation, this would log the error
                print(f"Error structuring content: {str(e)}")
                results.append(item)  # Keep the original item
                
        return results
        
    def _chunk_content(self, content: str) -> List[Dict[str, Any]]:
        """
        Chunk content based on the configured strategy.
        
        Args:
            content: Content to chunk
            
        Returns:
            List of content chunks
        """
        if self.chunking_strategy == 'fixed':
            return self._fixed_size_chunking(content)
        elif self.chunking_strategy == 'semantic':
            return self._semantic_chunking(content)
        elif self.chunking_strategy == 'hybrid':
            return self._hybrid_chunking(content)
        else:
            # Default to fixed-size chunking
            return self._fixed_size_chunking(content)
            
    def _fixed_size_chunking(self, content: str) -> List[Dict[str, Any]]:
        """
        Chunk content into fixed-size chunks.
        
        Args:
            content: Content to chunk
            
        Returns:
            List of content chunks
        """
        chunks = []
        
        # Split content into sentences (simple implementation)
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        current_chunk = ""
        current_chunk_size = 0
        
        for i, sentence in enumerate(sentences):
            sentence_size = len(sentence)
            
            if current_chunk_size + sentence_size > self.chunk_size and current_chunk:
                # Add the current chunk to the list
                chunks.append({
                    'content': current_chunk,
                    'index': len(chunks),
                    'size': current_chunk_size
                })
                
                # Start a new chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + sentence
                current_chunk_size = len(current_chunk)
            else:
                # Add the sentence to the current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_chunk_size += sentence_size
                
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append({
                'content': current_chunk,
                'index': len(chunks),
                'size': current_chunk_size
            })
            
        return chunks
        
    def _semantic_chunking(self, content: str) -> List[Dict[str, Any]]:
        """
        Chunk content based on semantic boundaries.
        
        In a real implementation, this would use NLP to identify semantic boundaries.
        For now, this is just a placeholder that uses paragraph breaks.
        
        Args:
            content: Content to chunk
            
        Returns:
            List of content chunks
        """
        chunks = []
        
        # Split content into paragraphs
        paragraphs = re.split(r'\n\s*\n', content)
        
        current_chunk = ""
        current_chunk_size = 0
        current_paragraphs = []
        
        for i, paragraph in enumerate(paragraphs):
            paragraph_size = len(paragraph)
            
            if current_chunk_size + paragraph_size > self.chunk_size and current_chunk:
                # Add the current chunk to the list
                chunks.append({
                    'content': current_chunk,
                    'index': len(chunks),
                    'size': current_chunk_size,
                    'paragraphs': current_paragraphs
                })
                
                # Start a new chunk
                current_chunk = paragraph
                current_chunk_size = paragraph_size
                current_paragraphs = [i]
            else:
                # Add the paragraph to the current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_chunk_size += paragraph_size
                current_paragraphs.append(i)
                
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append({
                'content': current_chunk,
                'index': len(chunks),
                'size': current_chunk_size,
                'paragraphs': current_paragraphs
            })
            
        return chunks
        
    def _hybrid_chunking(self, content: str) -> List[Dict[str, Any]]:
        """
        Chunk content using a hybrid approach that considers both
        fixed size and semantic boundaries.
        
        In a real implementation, this would be more sophisticated.
        For now, this is just a placeholder that combines the approaches.
        
        Args:
            content: Content to chunk
            
        Returns:
            List of content chunks
        """
        # First, split by semantic boundaries (paragraphs)
        paragraphs = re.split(r'\n\s*\n', content)
        
        chunks = []
        
        for i, paragraph in enumerate(paragraphs):
            # If paragraph is larger than chunk size, use fixed-size chunking
            if len(paragraph) > self.chunk_size:
                paragraph_chunks = self._fixed_size_chunking(paragraph)
                for chunk in paragraph_chunks:
                    chunk['paragraph_index'] = i
                    chunks.append(chunk)
            else:
                # Keep paragraph as a single chunk
                chunks.append({
                    'content': paragraph,
                    'index': len(chunks),
                    'size': len(paragraph),
                    'paragraph_index': i
                })
                
        return chunks
        
    def _detect_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Detect sections in the content.
        
        In a real implementation, this would use more sophisticated techniques.
        For now, this is just a placeholder that looks for headings.
        
        Args:
            content: Content to analyze
            
        Returns:
            List of detected sections
        """
        sections = []
        
        # Simple heading detection (e.g., "# Heading", "## Subheading")
        heading_pattern = r'^(#{1,6})\s+(.+?)$'
        
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for i, line in enumerate(lines):
            heading_match = re.match(heading_pattern, line)
            
            if heading_match:
                # Found a heading
                if current_section:
                    # Save the previous section
                    current_section['content'] = '\n'.join(current_content)
                    current_section['end_line'] = i - 1
                    sections.append(current_section)
                    
                # Start a new section
                level = len(heading_match.group(1))
                title = heading_match.group(2)
                
                current_section = {
                    'title': title,
                    'level': level,
                    'start_line': i,
                    'end_line': None,
                    'content': None
                }
                
                current_content = []
            elif current_section:
                # Add line to current section
                current_content.append(line)
                
        # Save the last section
        if current_section:
            current_section['content'] = '\n'.join(current_content)
            current_section['end_line'] = len(lines) - 1
            sections.append(current_section)
            
        return sections
        
    def _extract_relationships(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract relationships between content chunks.
        
        In a real implementation, this would use NLP to identify relationships.
        For now, this is just a placeholder that creates sequential relationships.
        
        Args:
            chunks: Content chunks
            
        Returns:
            List of relationships between chunks
        """
        relationships = []
        
        # Create sequential relationships
        for i in range(len(chunks) - 1):
            relationships.append({
                'type': 'next',
                'source': i,
                'target': i + 1
            })
            
        return relationships