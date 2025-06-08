from typing import Dict, Any, List, Optional
import json
import time
from datetime import datetime
from .connector_base import ConnectorBase

class APIConnector(ConnectorBase):
    """
    Connector for API-based knowledge sources (REST, GraphQL).
    
    This connector extracts content from API endpoints.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the API connector.
        
        Args:
            config: Configuration dictionary with the following keys:
                - api_type: Type of API ('rest', 'graphql')
                - base_url: Base URL for the API
                - endpoints: List of endpoints to query
                - headers: HTTP headers to include in requests
                - auth: Authentication information (if needed)
                - pagination: Pagination configuration (if needed)
                - rate_limit: Rate limiting configuration (if needed)
                    - requests_per_minute: Maximum requests per minute
                    - requests_per_hour: Maximum requests per hour
                    - requests_per_day: Maximum requests per day
                    - retry_after: Seconds to wait after hitting rate limit
        """
        super().__init__(config)
        self.api_type = config.get('api_type', 'rest')
        self.base_url = config.get('base_url', '')
        self.endpoints = config.get('endpoints', [])
        self.headers = config.get('headers', {})
        self.auth = config.get('auth', {})
        self.pagination = config.get('pagination', {})
        self.rate_limit = config.get('rate_limit', {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'requests_per_day': 10000,
            'retry_after': 60
        })
        
        # Rate limiting tracking
        self.request_history = []
        self.rate_limit_exceeded = False
        self.rate_limit_reset_time = None
        
    def connect(self) -> bool:
        """
        Establish connection to the API by validating the base URL.
        
        Returns:
            True if API is accessible, False otherwise
        """
        if not self.base_url:
            return False
            
        try:
            # In a real implementation, this would make a test request to the API
            # For now, this is just a placeholder
            # import requests
            # response = requests.get(self.base_url, headers=self.headers)
            # return response.status_code == 200
            return True
        except Exception as e:
            # In a real implementation, this would log the error
            print(f"Error connecting to API: {str(e)}")
            return False
        
    def validate(self) -> Dict[str, Any]:
        """
        Validate the API configuration.
        
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'endpoints': []
        }
        
        if not self.base_url:
            result['errors'].append('No base URL specified')
            
        if not self.endpoints:
            result['warnings'].append('No endpoints specified')
            
        if self.api_type not in ['rest', 'graphql']:
            result['errors'].append(f'Unsupported API type: {self.api_type}')
            
        if len(result['errors']) > 0:
            return result
            
        # Try to connect
        if not self.connect():
            result['errors'].append('Failed to connect to API')
            return result
            
        # In a real implementation, this would validate each endpoint
        result['endpoints'] = self.endpoints
            
        result['valid'] = len(result['errors']) == 0
        return result
        
    def extract(self) -> List[Dict[str, Any]]:
        """
        Extract content from the API endpoints.
        
        Returns:
            List of content items, each as a dictionary
        """
        if not self.connect():
            return []
                
        results = []
        
        for endpoint in self.endpoints:
            try:
                endpoint_data = self._query_endpoint(endpoint)
                results.extend(endpoint_data)
            except Exception as e:
                # In a real implementation, this would log the error
                print(f"Error querying endpoint {endpoint}: {str(e)}")
            
        return results
        
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the API source.
        
        Returns:
            Dictionary with source metadata
        """
        return {
            'source_id': self.source_id,
            'source_name': self.source_name,
            'source_type': 'api',
            'api_type': self.api_type,
            'base_url': self.base_url,
            'endpoint_count': len(self.endpoints),
            'metadata': self.metadata
        }
        
    def _query_endpoint(self, endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query an API endpoint.
        
        Args:
            endpoint: Endpoint configuration with:
                - path: Endpoint path
                - method: HTTP method (GET, POST, etc.)
                - params: Query parameters
                - body: Request body (for POST, PUT, etc.)
                
        Returns:
            List of content items from the endpoint
        """
        path = endpoint.get('path', '')
        method = endpoint.get('method', 'GET')
        params = endpoint.get('params', {})
        body = endpoint.get('body', {})
        
        if not path:
            return []
            
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        
        # In a real implementation, this would make the actual API request
        # For now, this is just a placeholder
        # import requests
        # response = None
        # if method.upper() == 'GET':
        #     response = requests.get(url, params=params, headers=self.headers)
        # elif method.upper() == 'POST':
        #     response = requests.post(url, params=params, json=body, headers=self.headers)
        # # ... other methods ...
        # 
        # if response and response.status_code == 200:
        #     data = response.json()
        #     # Process the data
        # else:
        #     return []
            
        # Placeholder implementation
        return [{
            'content': json.dumps({
                'endpoint': path,
                'method': method,
                'sample_data': f"[Sample data from {path}]"
            }),
            'metadata': {
                'endpoint': path,
                'method': method,
                'api_type': self.api_type
            },
            'source_path': f"{self.base_url}/{path}"
        }]
        
    def _handle_pagination(self, url: str, params: Dict[str, Any], response_data: Any) -> List[Any]:
        """
        Handle API pagination to get all results.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            response_data: Initial response data
            
        Returns:
            List of all paginated results combined
        """
        # Check if pagination configuration is provided
        if not self.pagination:
            return [response_data]
            
        pagination_type = self.pagination.get('type', '')
        if not pagination_type:
            return [response_data]
            
        all_results = [response_data]
        
        # Handle different pagination types
        if pagination_type == 'offset':
            return self._handle_offset_pagination(url, params, response_data)
        elif pagination_type == 'cursor':
            return self._handle_cursor_pagination(url, params, response_data)
        elif pagination_type == 'page':
            return self._handle_page_pagination(url, params, response_data)
        elif pagination_type == 'link':
            return self._handle_link_pagination(url, params, response_data)
        else:
            return all_results
    
    def _handle_offset_pagination(self, url: str, params: Dict[str, Any], response_data: Any) -> List[Any]:
        """
        Handle offset-based pagination.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            response_data: Initial response data
            
        Returns:
            List of all paginated results combined
        """
        # In a real implementation, this would make additional API requests
        # with increasing offset values until all results are retrieved
        
        # Pagination configuration
        limit_param = self.pagination.get('limit_param', 'limit')
        offset_param = self.pagination.get('offset_param', 'offset')
        limit = self.pagination.get('limit', 100)
        max_pages = self.pagination.get('max_pages', 10)
        total_param = self.pagination.get('total_param', 'total')
        
        # Placeholder implementation
        all_results = [response_data]
        
        # Simulate fetching additional pages
        for page in range(1, max_pages):
            # Check rate limits before making request
            if not self._check_rate_limit():
                break
                
            offset = page * limit
            
            # In a real implementation, this would make an actual API request
            # with updated offset parameter
            # For now, just simulate additional results
            next_page_data = {
                'page': page + 1,
                'offset': offset,
                'limit': limit,
                'data': [f"Offset pagination result {offset + i}" for i in range(limit)]
            }
            
            all_results.append(next_page_data)
            
            # Update request history for rate limiting
            self._update_request_history()
            
            # Simulate reaching the end of results
            if page >= 2:  # Just for demonstration
                break
                
        return all_results
    
    def _handle_cursor_pagination(self, url: str, params: Dict[str, Any], response_data: Any) -> List[Any]:
        """
        Handle cursor-based pagination.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            response_data: Initial response data
            
        Returns:
            List of all paginated results combined
        """
        # Pagination configuration
        cursor_param = self.pagination.get('cursor_param', 'cursor')
        next_cursor_path = self.pagination.get('next_cursor_path', 'meta.next_cursor')
        has_more_path = self.pagination.get('has_more_path', 'meta.has_more')
        max_pages = self.pagination.get('max_pages', 10)
        
        # Placeholder implementation
        all_results = [response_data]
        
        # Simulate fetching additional pages
        for page in range(1, max_pages):
            # Check rate limits before making request
            if not self._check_rate_limit():
                break
                
            # In a real implementation, this would extract the next cursor
            # from the response data using the next_cursor_path
            next_cursor = f"cursor_{page}"
            
            # In a real implementation, this would make an actual API request
            # with the next cursor parameter
            # For now, just simulate additional results
            next_page_data = {
                'page': page + 1,
                'data': [f"Cursor pagination result {page}_{i}" for i in range(10)],
                'meta': {
                    'next_cursor': f"cursor_{page + 1}",
                    'has_more': page < max_pages - 1
                }
            }
            
            all_results.append(next_page_data)
            
            # Update request history for rate limiting
            self._update_request_history()
            
            # Simulate reaching the end of results
            if page >= 2 or not next_page_data['meta']['has_more']:
                break
                
        return all_results
    
    def _handle_page_pagination(self, url: str, params: Dict[str, Any], response_data: Any) -> List[Any]:
        """
        Handle page-based pagination.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            response_data: Initial response data
            
        Returns:
            List of all paginated results combined
        """
        # Pagination configuration
        page_param = self.pagination.get('page_param', 'page')
        per_page_param = self.pagination.get('per_page_param', 'per_page')
        per_page = self.pagination.get('per_page', 100)
        max_pages = self.pagination.get('max_pages', 10)
        total_pages_path = self.pagination.get('total_pages_path', 'meta.total_pages')
        
        # Placeholder implementation
        all_results = [response_data]
        
        # Simulate fetching additional pages
        for page in range(2, max_pages + 1):
            # Check rate limits before making request
            if not self._check_rate_limit():
                break
                
            # In a real implementation, this would make an actual API request
            # with updated page parameter
            # For now, just simulate additional results
            next_page_data = {
                'page': page,
                'per_page': per_page,
                'data': [f"Page pagination result {page}_{i}" for i in range(per_page)],
                'meta': {
                    'total_pages': max_pages
                }
            }
            
            all_results.append(next_page_data)
            
            # Update request history for rate limiting
            self._update_request_history()
            
            # Simulate reaching the end of results
            if page >= 3:  # Just for demonstration
                break
                
        return all_results
    
    def _handle_link_pagination(self, url: str, params: Dict[str, Any], response_data: Any) -> List[Any]:
        """
        Handle link-based pagination (e.g., Link header in HTTP responses).
        
        Args:
            url: API endpoint URL
            params: Query parameters
            response_data: Initial response data
            
        Returns:
            List of all paginated results combined
        """
        # Pagination configuration
        link_header_param = self.pagination.get('link_header_param', 'Link')
        max_pages = self.pagination.get('max_pages', 10)
        
        # Placeholder implementation
        all_results = [response_data]
        
        # Simulate fetching additional pages
        for page in range(1, max_pages):
            # Check rate limits before making request
            if not self._check_rate_limit():
                break
                
            # In a real implementation, this would extract the next link
            # from the response headers
            next_link = f"{url}?page={page + 1}"
            
            # In a real implementation, this would make an actual API request
            # to the next link
            # For now, just simulate additional results
            next_page_data = {
                'page': page + 1,
                'data': [f"Link pagination result {page + 1}_{i}" for i in range(10)]
            }
            
            all_results.append(next_page_data)
            
            # Update request history for rate limiting
            self._update_request_history()
            
            # Simulate reaching the end of results
            if page >= 2:  # Just for demonstration
                break
                
        return all_results
    
    def _check_rate_limit(self) -> bool:
        """
        Check if the current request would exceed rate limits.
        
        Returns:
            True if request is allowed, False if rate limit would be exceeded
        """
        # If rate limit was previously exceeded and reset time is set
        if self.rate_limit_exceeded and self.rate_limit_reset_time:
            # Check if reset time has passed
            if datetime.now() < self.rate_limit_reset_time:
                # Rate limit still in effect
                return False
            else:
                # Reset rate limit status
                self.rate_limit_exceeded = False
                self.rate_limit_reset_time = None
        
        # Clean up old requests from history
        current_time = datetime.now()
        self.request_history = [
            timestamp for timestamp in self.request_history
            if (current_time - timestamp).total_seconds() < 86400  # Keep last 24 hours
        ]
        
        # Check minute limit
        minute_ago = current_time.timestamp() - 60
        requests_last_minute = sum(
            1 for timestamp in self.request_history
            if timestamp.timestamp() > minute_ago
        )
        if requests_last_minute >= self.rate_limit['requests_per_minute']:
            self._handle_rate_limit_exceeded()
            return False
            
        # Check hour limit
        hour_ago = current_time.timestamp() - 3600
        requests_last_hour = sum(
            1 for timestamp in self.request_history
            if timestamp.timestamp() > hour_ago
        )
        if requests_last_hour >= self.rate_limit['requests_per_hour']:
            self._handle_rate_limit_exceeded()
            return False
            
        # Check day limit
        day_ago = current_time.timestamp() - 86400
        requests_last_day = sum(
            1 for timestamp in self.request_history
            if timestamp.timestamp() > day_ago
        )
        if requests_last_day >= self.rate_limit['requests_per_day']:
            self._handle_rate_limit_exceeded()
            return False
            
        return True
    
    def _update_request_history(self) -> None:
        """
        Update the request history with the current timestamp.
        """
        self.request_history.append(datetime.now())
    
    def _handle_rate_limit_exceeded(self) -> None:
        """
        Handle the case when rate limit is exceeded.
        """
        self.rate_limit_exceeded = True
        retry_after = self.rate_limit.get('retry_after', 60)
        self.rate_limit_reset_time = datetime.now().timestamp() + retry_after
        
        # In a real implementation, this would log the rate limit exceeded event
        print(f"Rate limit exceeded. Retry after {retry_after} seconds.")
        
    def _handle_graphql_query(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a GraphQL query.
        
        Args:
            query: GraphQL query string
            variables: Variables for the GraphQL query
            
        Returns:
            GraphQL response data
        """
        # Check rate limits before making request
        if not self._check_rate_limit():
            return {
                'errors': [
                    {'message': 'Rate limit exceeded'}
                ]
            }
        
        # In a real implementation, this would execute the GraphQL query
        # For now, this is just a placeholder
        response = {
            'data': {
                'sample': f"[Sample GraphQL response for query: {query[:30]}...]"
            }
        }
        
        # Update request history for rate limiting
        self._update_request_history()
        
        return response