from typing import Dict, Any, List, Optional
import re
from urllib.parse import urljoin, urlparse
from .connector_base import ConnectorBase

class WebConnector(ConnectorBase):
    """
    Connector for web-based knowledge sources.
    
    This connector crawls websites and extracts content from web pages.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the web connector.
        
        Args:
            config: Configuration dictionary with the following keys:
                - start_urls: List of URLs to start crawling from
                - allowed_domains: List of domains to restrict crawling to
                - max_depth: Maximum crawl depth
                - max_pages: Maximum number of pages to crawl
                - follow_links: Whether to follow links on pages
                - url_patterns: List of regex patterns for URLs to include
                - exclude_patterns: List of regex patterns for URLs to exclude
        """
        super().__init__(config)
        self.start_urls = config.get('start_urls', [])
        self.allowed_domains = config.get('allowed_domains', [])
        self.max_depth = config.get('max_depth', 3)
        self.max_pages = config.get('max_pages', 100)
        self.follow_links = config.get('follow_links', True)
        self.url_patterns = config.get('url_patterns', [])
        self.exclude_patterns = config.get('exclude_patterns', [])
        
        # Compile regex patterns
        self.url_regex = [re.compile(pattern) for pattern in self.url_patterns] if self.url_patterns else []
        self.exclude_regex = [re.compile(pattern) for pattern in self.exclude_patterns] if self.exclude_patterns else []
        
        # Crawling state
        self.visited_urls = set()
        self.queue = []
        self.current_depth = 0
        
    def connect(self) -> bool:
        """
        Establish connection by validating start URLs.
        
        Returns:
            True if at least one start URL is valid, False otherwise
        """
        if not self.start_urls:
            return False
            
        valid_urls = []
        
        for url in self.start_urls:
            try:
                # In a real implementation, this would make a test request to the URL
                # For now, this is just a placeholder
                # import requests
                # response = requests.head(url, allow_redirects=True)
                # if response.status_code == 200:
                #     valid_urls.append(url)
                valid_urls.append(url)
            except Exception as e:
                # In a real implementation, this would log the error
                print(f"Error connecting to URL {url}: {str(e)}")
                
        if valid_urls:
            self.start_urls = valid_urls
            self.queue = [(url, 0) for url in valid_urls]  # (url, depth)
            return True
            
        return False
        
    def validate(self) -> Dict[str, Any]:
        """
        Validate the web crawler configuration.
        
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'start_urls': []
        }
        
        if not self.start_urls:
            result['errors'].append('No start URLs specified')
            
        if self.max_depth <= 0:
            result['errors'].append('Max depth must be greater than 0')
            
        if self.max_pages <= 0:
            result['errors'].append('Max pages must be greater than 0')
            
        if len(result['errors']) > 0:
            return result
            
        # Validate start URLs
        valid_urls = []
        for url in self.start_urls:
            try:
                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc:
                    valid_urls.append(url)
                else:
                    result['warnings'].append(f'Invalid URL format: {url}')
            except:
                result['warnings'].append(f'Invalid URL: {url}')
                
        if not valid_urls:
            result['errors'].append('No valid start URLs')
            return result
            
        result['start_urls'] = valid_urls
        result['valid'] = True
        return result
        
    def extract(self) -> List[Dict[str, Any]]:
        """
        Extract content by crawling web pages.
        
        Returns:
            List of content items, each as a dictionary
        """
        if not self.queue:
            if not self.connect():
                return []
                
        results = []
        
        while self.queue and len(self.visited_urls) < self.max_pages:
            url, depth = self.queue.pop(0)
            
            if url in self.visited_urls:
                continue
                
            if depth > self.max_depth:
                continue
                
            try:
                page_content, links = self._fetch_page(url)
                self.visited_urls.add(url)
                
                if page_content:
                    results.append({
                        'content': page_content,
                        'metadata': {
                            'url': url,
                            'depth': depth,
                            'title': self._extract_title(page_content)
                        },
                        'source_path': url
                    })
                    
                # Add links to queue if following links
                if self.follow_links and depth < self.max_depth:
                    for link in links:
                        if self._should_follow(link):
                            self.queue.append((link, depth + 1))
            except Exception as e:
                # In a real implementation, this would log the error
                print(f"Error crawling URL {url}: {str(e)}")
            
        return results
        
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the web source.
        
        Returns:
            Dictionary with source metadata
        """
        return {
            'source_id': self.source_id,
            'source_name': self.source_name,
            'source_type': 'web',
            'start_urls': self.start_urls,
            'allowed_domains': self.allowed_domains,
            'max_depth': self.max_depth,
            'max_pages': self.max_pages,
            'pages_visited': len(self.visited_urls),
            'metadata': self.metadata
        }
        
    def _fetch_page(self, url: str) -> tuple:
        """
        Fetch a web page and extract its content and links.
        
        In a real implementation, this would use requests or a similar library.
        For now, this is just a placeholder.
        """
        # Placeholder implementation
        content = f"[Web page content from {url}]"
        links = [
            urljoin(url, f"/page{i}") 
            for i in range(1, 4)
        ]
        return content, links
        
    def _should_follow(self, url: str) -> bool:
        """
        Determine if a URL should be followed based on configuration.
        """
        if url in self.visited_urls:
            return False
            
        parsed = urlparse(url)
        
        # Check allowed domains
        if self.allowed_domains and parsed.netloc not in self.allowed_domains:
            return False
            
        # Check exclude patterns
        for pattern in self.exclude_regex:
            if pattern.search(url):
                return False
                
        # Check include patterns
        if self.url_regex:
            for pattern in self.url_regex:
                if pattern.search(url):
                    return True
            return False
            
        return True
        
    def _extract_title(self, content: str) -> str:
        """
        Extract the title from HTML content.
        
        In a real implementation, this would use BeautifulSoup or similar.
        For now, this is just a placeholder.
        """
        # Placeholder implementation
        return "Page Title"
        
    def _extract_text(self, html: str) -> str:
        """
        Extract plain text from HTML content.
        
        In a real implementation, this would use BeautifulSoup or similar.
        For now, this is just a placeholder.
        """
        # Placeholder implementation
        return "Extracted text from HTML"