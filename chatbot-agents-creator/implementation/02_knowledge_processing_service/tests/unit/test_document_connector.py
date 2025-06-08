import unittest
from unittest.mock import patch, mock_open
import os
from src.connectors.document_connector import DocumentConnector

class TestDocumentConnector(unittest.TestCase):
    def setUp(self):
        self.config = {
            'file_path': '/test/path',
            'file_types': ['pdf', 'docx', 'txt'],
            'recursive': False,
            'source_id': 'test_source',
            'source_name': 'Test Source'
        }
        self.connector = DocumentConnector(self.config)
        
    @patch('os.path.isfile')
    def test_connect_with_file(self, mock_isfile):
        # Mock os.path.isfile to return True
        mock_isfile.return_value = True
        
        # Mock _is_supported_file to return True
        with patch.object(self.connector, '_is_supported_file', return_value=True):
            result = self.connector.connect()
            self.assertTrue(result)
            self.assertEqual(self.connector.files, ['/test/path'])
            
    @patch('os.path.isfile')
    def test_connect_with_unsupported_file(self, mock_isfile):
        # Mock os.path.isfile to return True
        mock_isfile.return_value = True
        
        # Mock _is_supported_file to return False
        with patch.object(self.connector, '_is_supported_file', return_value=False):
            result = self.connector.connect()
            self.assertFalse(result)
            
    @patch('os.path.isfile')
    @patch('os.path.isdir')
    def test_connect_with_directory(self, mock_isdir, mock_isfile):
        # Mock os.path.isfile to return False and os.path.isdir to return True
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        
        # Mock _find_files to return a list of files
        test_files = ['/test/path/file1.pdf', '/test/path/file2.txt']
        with patch.object(self.connector, '_find_files', return_value=test_files):
            result = self.connector.connect()
            self.assertTrue(result)
            self.assertEqual(self.connector.files, test_files)
            
    def test_is_supported_file(self):
        # Test with supported file types
        self.assertTrue(self.connector._is_supported_file('/test/path/file.pdf'))
        self.assertTrue(self.connector._is_supported_file('/test/path/file.docx'))
        self.assertTrue(self.connector._is_supported_file('/test/path/file.txt'))
        
        # Test with unsupported file type
        self.assertFalse(self.connector._is_supported_file('/test/path/file.jpg'))
        
    @patch('os.path.isfile')
    @patch('os.listdir')
    def test_find_files_non_recursive(self, mock_listdir, mock_isfile):
        # Mock os.listdir to return a list of files
        mock_listdir.return_value = ['file1.pdf', 'file2.txt', 'file3.jpg', 'subdir']
        
        # Mock os.path.isfile to return True for files and False for directories
        def mock_isfile_side_effect(path):
            return not path.endswith('subdir')
            
        mock_isfile.side_effect = mock_isfile_side_effect
        
        # Mock _is_supported_file to return True for supported file types
        def mock_is_supported_side_effect(path):
            return path.endswith(('.pdf', '.txt'))
            
        with patch.object(self.connector, '_is_supported_file', side_effect=mock_is_supported_side_effect):
            result = self.connector._find_files('/test/path', False)
            
            # Should find file1.pdf and file2.txt but not file3.jpg or subdir
            expected = [
                os.path.join('/test/path', 'file1.pdf'),
                os.path.join('/test/path', 'file2.txt')
            ]
            self.assertEqual(sorted(result), sorted(expected))
            
    def test_extract_content(self):
        # Create a test item
        item = {
            'source_path': '/test/path/file.txt'
        }
        
        # Mock _extract_from_txt to return a test string
        test_content = "This is test content"
        with patch.object(self.connector, '_extract_from_txt', return_value=test_content):
            result = self.connector._extract_content(item)
            self.assertEqual(result['content'], test_content)
            
    def test_get_metadata(self):
        # Set up the connector with files
        self.connector.files = ['/test/path/file1.pdf', '/test/path/file2.txt']
        
        # Get metadata
        metadata = self.connector.get_metadata()
        
        # Check metadata
        self.assertEqual(metadata['source_id'], 'test_source')
        self.assertEqual(metadata['source_name'], 'Test Source')
        self.assertEqual(metadata['source_type'], 'document')
        self.assertEqual(metadata['file_path'], '/test/path')
        self.assertEqual(metadata['file_types'], ['pdf', 'docx', 'txt'])
        self.assertEqual(metadata['file_count'], 2)

if __name__ == '__main__':
    unittest.main()