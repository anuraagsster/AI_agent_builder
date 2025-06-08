from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class ConnectorBase(ABC):
    """
    Base class for all knowledge source connectors.
    
    This abstract class defines the interface that all connectors must implement
    to extract content from different knowledge sources.
    """
    
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
        
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the knowledge source.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
        
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
    
    This class manages the registration and retrieval of connector classes
    for different source types.
    """
    
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