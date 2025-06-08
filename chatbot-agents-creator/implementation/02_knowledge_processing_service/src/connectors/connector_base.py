from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from jsonschema import validate, ValidationError
from jsonschema.exceptions import SchemaError

class ConnectorBase(ABC):
    """
    Base class for all knowledge source connectors.
    
    This abstract class defines the interface that all connectors must implement
    to extract content from different knowledge sources. It includes methods for
    connecting, validating, extracting, and retrieving metadata from the source.
    """
    
    SCHEMA = {
        "type": "object",
        "properties": {
            "source_id": {"type": "string"},
            "source_name": {"type": "string"},
            "metadata": {"type": "object"},
            "API_KEY": {"type": "string"}
        },
        "required": ["source_id", "source_name", "API_KEY"]
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the connector with configuration.
        
        Args:
            config: Configuration dictionary for the connector
        """
        try:
            validate(instance=config, schema=self.SCHEMA)
        except (ValidationError, SchemaError) as e:
            raise ValueError(f"Invalid configuration: {e}")
        
        self.config = config
        self.source_id = config.get('source_id', '')
        self.source_name = config.get('source_name', '')
        self.metadata = config.get('metadata', {})
        self.api_key = config.get('API_KEY', '')
        
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the knowledge source.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.api_key:
            print("API_KEY is missing from the configuration.")
            return False
        # Example: Use the API_KEY to establish a connection
        # response = requests.get(f"https://api.example.com/validate?api_key={self.api_key}")
        # return response.status_code == 200
        return True
        
    @abstractmethod
    def validate(self) -> Dict[str, Any]:
        """
        Validate the connection and source configuration.
        
        Returns:
            Dictionary with validation results
        """
        pass
        
    @abstractmethod
    def extract(self) -> List[Dict[str, Any]]:
        """
        Extract content from the knowledge source.
        
        Returns:
            List of content items, each as a dictionary
        """
        pass
        
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the knowledge source.
        
        Returns:
            Dictionary with source metadata
        """
        pass
        
    def close(self) -> None:
        """
        Close the connection to the knowledge source.
        """
        pass
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the connector with configuration.
        
        Args:
            config: Configuration dictionary for the connector
        """
        self.config = config
        self.source_id = config.get('source_id', '')
        self.source_name = config.get('source_name', '')
        self.metadata = config.get('metadata', {})
        self.api_key = config.get('API_KEY', '')
        
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the knowledge source.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.api_key:
            print("API_KEY is missing from the configuration.")
            return False
        # Example: Use the API_KEY to establish a connection
        # response = requests.get(f"https://api.example.com/validate?api_key={self.api_key}")
        # return response.status_code == 200
        return True
        
    @abstractmethod
    def validate(self) -> Dict[str, Any]:
        """
        Validate the connection and source configuration.
        
        Returns:
            Dictionary with validation results
        """
        pass
        
    @abstractmethod
    def extract(self) -> List[Dict[str, Any]]:
        """
        Extract content from the knowledge source.
        
        Returns:
            List of content items, each as a dictionary
        """
        pass
        
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the knowledge source.
        
        Returns:
            Dictionary with source metadata
        """
        pass
        
    def close(self) -> None:
        """
        Close the connection to the knowledge source.
        """
        pass


class ConnectorRegistry:
    """
    Registry for all available connectors.
    
    This class manages the registration, retrieval, and metadata management of
    connector classes for different source types. It also supports versioning and
    compatibility checking for connectors.
    """
    
    def __init__(self):
        """Initialize the connector registry."""
        self.connectors = {}
        self.metadata = {}
        
    def register_connector(self, source_type: str, connector_class, version: str, metadata: Dict[str, Any]) -> None:
        """
        Register a connector class for a specific source type.
        
        Args:
            source_type: Type of knowledge source
            connector_class: Connector class to register
            version: Version of the connector
            metadata: Metadata for the connector
        """
        self.connectors[source_type] = connector_class
        self.metadata[source_type] = {
            "version": version,
            "metadata": metadata
        }
        
    def get_connector(self, source_type: str) -> Optional[type]:
        """
        Get a connector class for a specific source type.
        
        Args:
            source_type: Type of knowledge source
            
        Returns:
            Connector class if registered, None otherwise
        """
        return self.connectors.get(source_type)
        
    def create_connector(self, source_type: str, config: Dict[str, Any]) -> Optional[ConnectorBase]:
        """
        Create a connector instance for a specific source type.
        
        Args:
            source_type: Type of knowledge source
            config: Configuration for the connector
            
        Returns:
            Connector instance if source type is registered, None otherwise
        """
        connector_class = self.get_connector(source_type)
        if connector_class:
            return connector_class(config)
        return None
        
    def list_connectors(self) -> List[str]:
        """
        List all registered connector types.
        
        Returns:
            List of registered source types
        """
        return list(self.connectors.keys())
        
    def get_connector_metadata(self, source_type: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific connector.
        
        Args:
            source_type: Type of knowledge source
            
        Returns:
            Metadata dictionary if available, None otherwise
        """
        return self.metadata.get(source_type)
        
    def check_compatibility(self, source_type: str, required_version: str) -> bool:
        """
        Check if a connector is compatible with a required version.
        
        Args:
            source_type: Type of knowledge source
            required_version: Required version for compatibility
            
        Returns:
            True if compatible, False otherwise
        """
        metadata = self.get_connector_metadata(source_type)
        if metadata and metadata.get("version") == required_version:
            return True
        return False
    
    def __init__(self):
        """Initialize the connector registry."""
        self.connectors = {}
        
    def register_connector(self, source_type: str, connector_class) -> None:
        """
        Register a connector class for a specific source type.
        
        Args:
            source_type: Type of knowledge source
            connector_class: Connector class to register
        """
        self.connectors[source_type] = connector_class
        
    def get_connector(self, source_type: str) -> Optional[type]:
        """
        Get a connector class for a specific source type.
        
        Args:
            source_type: Type of knowledge source
            
        Returns:
            Connector class if registered, None otherwise
        """
        return self.connectors.get(source_type)
        
    def create_connector(self, source_type: str, config: Dict[str, Any]) -> Optional[ConnectorBase]:
        """
        Create a connector instance for a specific source type.
        
        Args:
            source_type: Type of knowledge source
            config: Configuration for the connector
            
        Returns:
            Connector instance if source type is registered, None otherwise
        """
        connector_class = self.get_connector(source_type)
        if connector_class:
            return connector_class(config)
        return None
        
    def list_connectors(self) -> List[str]:
        """
        List all registered connector types.
        
        Returns:
            List of registered source types
        """
        return list(self.connectors.keys())