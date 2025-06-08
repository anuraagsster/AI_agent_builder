from typing import Dict, Any, List, Optional
import os
from .connector_base import ConnectorBase

class DocumentConnector(ConnectorBase):
    """
    Connector for document-based knowledge sources (PDF, DOCX, TXT, etc.).
    
    This connector extracts content from document files.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the document connector.
        
        Args:
            config: Configuration dictionary with the following keys:
                - file_path: Path to the document file or directory
                - file_types: List of file extensions to process (e.g., ['pdf', 'docx'])
                - recursive: Whether to search directories recursively
        """
        super().__init__(config)
        self.file_path = config.get('file_path', '')
        self.file_types = config.get('file_types', ['pdf', 'docx', 'txt'])
        self.recursive = config.get('recursive', False)
        self.files = []
        
    def connect(self) -> bool:
        """
        Establish connection to the document source by validating file paths.
        
        Returns:
            True if files exist and are accessible, False otherwise
        """
        if not self.file_path:
            return False
            
        if os.path.isfile(self.file_path):
            # Single file
            if self._is_supported_file(self.file_path):
                self.files = [self.file_path]
                return True
            return False
            
        elif os.path.isdir(self.file_path):
            # Directory of files
            self.files = self._find_files(self.file_path, self.recursive)
            return len(self.files) > 0
            
        return False
        
    def validate(self) -> Dict[str, Any]:
        """
        Validate the document source configuration.
        
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'file_count': 0
        }
        
        if not self.file_path:
            result['errors'].append('No file path specified')
            return result
            
        if not os.path.exists(self.file_path):
            result['errors'].append(f'Path does not exist: {self.file_path}')
            return result
            
        if os.path.isfile(self.file_path):
            if not self._is_supported_file(self.file_path):
                result['errors'].append(f'Unsupported file type: {self.file_path}')
                return result
            result['file_count'] = 1
            
        elif os.path.isdir(self.file_path):
            files = self._find_files(self.file_path, self.recursive)
            result['file_count'] = len(files)
            
            if result['file_count'] == 0:
                result['warnings'].append(f'No supported files found in: {self.file_path}')
                
        result['valid'] = len(result['errors']) == 0
        return result
        
    def extract(self) -> List[Dict[str, Any]]:
        """
        Extract content from the document files.
        
        Returns:
            List of content items, each as a dictionary with:
                - content: The extracted text
                - metadata: File metadata
                - source_path: Path to the source file
        """
        if not self.files:
            if not self.connect():
                return []
                
        results = []
        
        for file_path in self.files:
            try:
                content = self._extract_file_content(file_path)
                if content:
                    results.append({
                        'content': content,
                        'metadata': self._get_file_metadata(file_path),
                        'source_path': file_path
                    })
            except Exception as e:
                # In a real implementation, this would log the error
                print(f"Error extracting content from {file_path}: {str(e)}")
                
        return results
        
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the document source.
        
        Returns:
            Dictionary with source metadata
        """
        return {
            'source_id': self.source_id,
            'source_name': self.source_name,
            'source_type': 'document',
            'file_path': self.file_path,
            'file_types': self.file_types,
            'file_count': len(self.files),
            'metadata': self.metadata
        }
        
    def _is_supported_file(self, file_path: str) -> bool:
        """Check if a file is supported based on its extension."""
        _, ext = os.path.splitext(file_path)
        return ext.lower()[1:] in self.file_types
        
    def _find_files(self, directory: str, recursive: bool) -> List[str]:
        """Find all supported files in a directory."""
        result = []
        
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._is_supported_file(file_path):
                        result.append(file_path)
        else:
            for item in os.listdir(directory):
                file_path = os.path.join(directory, item)
                if os.path.isfile(file_path) and self._is_supported_file(file_path):
                    result.append(file_path)
                    
        return result
        
    def _extract_file_content(self, file_path: str) -> str:
        """
        Extract text content from a file.
        
        In a real implementation, this would use libraries like PyPDF2, python-docx, etc.
        For now, this is just a placeholder.
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()[1:]
        
        # Placeholder implementation
        if ext == 'pdf':
            return f"[PDF content from {file_path}]"
        elif ext == 'docx':
            return f"[DOCX content from {file_path}]"
        elif ext == 'txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return f"[Error reading TXT file {file_path}]"
        else:
            return f"[Unsupported file type: {ext}]"
            
    def _get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata for a file.
        
        In a real implementation, this would extract more metadata.
        """
        return {
            'filename': os.path.basename(file_path),
            'file_size': os.path.getsize(file_path),
            'last_modified': os.path.getmtime(file_path),
            'file_type': os.path.splitext(file_path)[1][1:].lower()
        }