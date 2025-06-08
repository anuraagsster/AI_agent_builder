from typing import Dict, Any, List, Optional
import re
from .pipeline import PipelineStage

class ContentExtractor(PipelineStage):
    """
    Pipeline stage for extracting and cleaning content from raw sources.
    
    This stage extracts text content from various formats and performs
    initial cleaning and normalization.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the content extractor.
        
        Args:
            config: Configuration dictionary with the following keys:
                - extract_metadata: Whether to extract metadata
                - clean_html: Whether to clean HTML tags
                - normalize_whitespace: Whether to normalize whitespace
                - min_content_length: Minimum content length to keep
                - max_content_length: Maximum content length to keep
        """
        super().__init__(config)
        self.extract_metadata = self.config.get('extract_metadata', True)
        self.clean_html = self.config.get('clean_html', True)
        self.normalize_whitespace = self.config.get('normalize_whitespace', True)
        self.min_content_length = self.config.get('min_content_length', 10)
        self.max_content_length = self.config.get('max_content_length', 100000)
        
    def process(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of items by extracting and cleaning content.
        
        Args:
            items: List of items to process
            
        Returns:
            Processed items with extracted content
        """
        results = []
        
        for item in items:
            try:
                # Extract content based on source type
                processed_item = self._extract_content(item)
                
                if processed_item:
                    # Apply content cleaning
                    if self.clean_html and 'content' in processed_item:
                        processed_item['content'] = self._clean_html(processed_item['content'])
                        
                    if self.normalize_whitespace and 'content' in processed_item:
                        processed_item['content'] = self._normalize_whitespace(processed_item['content'])
                        
                    # Check content length
                    if 'content' in processed_item:
                        content_length = len(processed_item['content'])
                        if content_length < self.min_content_length:
                            # Skip items that are too short
                            continue
                            
                        if content_length > self.max_content_length:
                            # Truncate items that are too long
                            processed_item['content'] = processed_item['content'][:self.max_content_length]
                            processed_item['truncated'] = True
                            
                    results.append(processed_item)
            except Exception as e:
                # In a real implementation, this would log the error
                print(f"Error extracting content: {str(e)}")
                
        return results
        
    def _extract_content(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract content from an item based on its format.
        
        Args:
            item: Item to extract content from
            
        Returns:
            Item with extracted content
        """
        # Create a new item to avoid modifying the original
        result = item.copy()
        
        # Extract content based on format
        if 'content' in item:
            # Content is already extracted
            pass
        elif 'html' in item:
            # Extract from HTML
            result['content'] = self._extract_from_html(item['html'])
        elif 'text' in item:
            # Use text directly
            result['content'] = item['text']
        elif 'source_path' in item:
            # Try to infer content type from source path
            source_path = item['source_path']
            if source_path.endswith('.pdf'):
                result['content'] = self._extract_from_pdf(item)
            elif source_path.endswith('.docx'):
                result['content'] = self._extract_from_docx(item)
            elif source_path.endswith('.txt'):
                result['content'] = self._extract_from_txt(item)
            else:
                # Unknown format
                result['content'] = str(item)
        else:
            # Unknown format
            result['content'] = str(item)
            
        # Extract metadata if needed
        if self.extract_metadata:
            result['extracted_metadata'] = self._extract_metadata(item)
            
        return result
        
    def _clean_html(self, content: str) -> str:
        """
        Clean HTML tags from content.
        
        In a real implementation, this would use a proper HTML parser.
        For now, this is just a simple regex-based implementation.
        """
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)
        
        # Decode HTML entities
        content = content.replace('&nbsp;', ' ')
        content = content.replace('&amp;', '&')
        content = content.replace('&lt;', '<')
        content = content.replace('&gt;', '>')
        content = content.replace('&quot;', '"')
        
        return content
        
    def _normalize_whitespace(self, content: str) -> str:
        """
        Normalize whitespace in content.
        """
        # Replace multiple whitespace with a single space
        content = re.sub(r'\s+', ' ', content)
        
        # Remove leading/trailing whitespace
        content = content.strip()
        
        return content
        
    def _extract_from_html(self, html: str) -> str:
        """
        Extract text content from HTML.
        
        In a real implementation, this would use BeautifulSoup or similar.
        For now, this is just a placeholder.
        """
        # Placeholder implementation
        return self._clean_html(html)
        
    def _extract_from_pdf(self, item: Dict[str, Any]) -> str:
        """
        Extract text content from PDF.
        
        In a real implementation, this would use PyPDF2 or similar.
        For now, this is just a placeholder.
        """
        # Placeholder implementation
        return f"[PDF content from {item.get('source_path', 'unknown')}]"
        
    def _extract_from_docx(self, item: Dict[str, Any]) -> str:
        """
        Extract text content from DOCX.
        
        In a real implementation, this would use python-docx or similar.
        For now, this is just a placeholder.
        """
        # Placeholder implementation
        return f"[DOCX content from {item.get('source_path', 'unknown')}]"
        
    def _extract_from_txt(self, item: Dict[str, Any]) -> str:
        """
        Extract text content from TXT.
        
        In a real implementation, this would read the file.
        For now, this is just a placeholder.
        """
        # Placeholder implementation
        return f"[TXT content from {item.get('source_path', 'unknown')}]"
        
    def _extract_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from an item.
        
        Args:
            item: Item to extract metadata from
            
        Returns:
            Extracted metadata
        """
        metadata = {}
        
        # Extract basic metadata
        if 'source_path' in item:
            metadata['source_path'] = item['source_path']
            
        if 'metadata' in item:
            metadata.update(item['metadata'])
            
        # Extract content-based metadata
        if 'content' in item:
            content = item['content']
            metadata['content_length'] = len(content)
            metadata['word_count'] = len(content.split())
            
        return metadata