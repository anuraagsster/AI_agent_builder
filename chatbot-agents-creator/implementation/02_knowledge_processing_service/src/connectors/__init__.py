# Connectors package
# This package contains connectors for various knowledge sources

from .connector_base import ConnectorBase, ConnectorRegistry
from .document_connector import DocumentConnector
from .database_connector import DatabaseConnector
from .api_connector import APIConnector
from .web_connector import WebConnector

# Register the DocumentConnector
registry = ConnectorRegistry()
registry.register_connector(
    source_type="document",
    connector_class=DocumentConnector,
    version="1.0.0",
    metadata={
        "description": "Connector for document-based knowledge sources (PDF, DOCX, TXT, etc.).",
        "supported_file_types": ["pdf", "docx", "txt"],
        "recursive_search": True
    }
)