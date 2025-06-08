# Connectors package
# This package contains connectors for various knowledge sources

from .connector_base import ConnectorBase, ConnectorRegistry
from .document_connector import DocumentConnector
from .database_connector import DatabaseConnector
from .api_connector import APIConnector
from .web_connector import WebConnector

# Create the connector registry
registry = ConnectorRegistry()

# Register the DocumentConnector
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

# Register the DatabaseConnector
registry.register_connector(
    source_type="database",
    connector_class=DatabaseConnector,
    version="1.0.0",
    metadata={
        "description": "Connector for database knowledge sources (SQL, NoSQL).",
        "supported_db_types": ["mysql", "postgresql", "mongodb", "sqlite", "oracle", "sqlserver"],
        "features": ["schema_discovery", "connection_pooling", "table_extraction"]
    }
)

# Register the APIConnector
registry.register_connector(
    source_type="api",
    connector_class=APIConnector,
    version="1.0.0",
    metadata={
        "description": "Connector for API-based knowledge sources (REST, GraphQL).",
        "supported_api_types": ["rest", "graphql"],
        "features": ["rate_limiting", "pagination", "authentication"]
    }
)

# Register the WebConnector
registry.register_connector(
    source_type="web",
    connector_class=WebConnector,
    version="0.9.0",
    metadata={
        "description": "Connector for web-based knowledge sources (HTML pages).",
        "features": ["html_extraction", "link_discovery", "crawling"]
    }
)