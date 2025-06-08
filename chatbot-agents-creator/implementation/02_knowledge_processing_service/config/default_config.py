"""
Default configuration for the Knowledge Processing Service.
This file contains default settings that can be overridden by environment-specific configurations.
"""

# Connector Configuration
CONNECTORS = {
    "document": {
        "enabled": True,
        "file_types": ["pdf", "docx", "txt", "md", "html"],
        "recursive": True,
        "max_file_size": 10485760,  # 10MB
    },
    "database": {
        "enabled": True,
        "supported_types": ["mysql", "postgresql", "mongodb"],
        "connection_timeout": 30,
        "max_rows": 10000,
    },
    "api": {
        "enabled": True,
        "request_timeout": 30,
        "max_retries": 3,
        "retry_delay": 1,
    },
    "web": {
        "enabled": True,
        "max_depth": 3,
        "max_pages": 100,
        "request_timeout": 30,
        "user_agent": "KnowledgeProcessingService/0.1.0",
        "respect_robots_txt": True,
        "crawl_delay": 1,
    },
}

# Processing Pipeline Configuration
PROCESSING = {
    "content_extractor": {
        "extract_metadata": True,
        "clean_html": True,
        "normalize_whitespace": True,
        "min_content_length": 10,
        "max_content_length": 100000,
    },
    "content_structurer": {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "detect_sections": True,
        "extract_relationships": True,
        "chunking_strategy": "hybrid",
    },
    "embedding_generator": {
        "model_name": "default",
        "embedding_dim": 768,
        "batch_size": 32,
        "cache_embeddings": True,
        "normalize_embeddings": True,
    },
}

# Storage Configuration
STORAGE = {
    "vector_store": {
        "type": "in_memory",  # Options: in_memory, faiss, hnswlib
        "distance_metric": "cosine",
        "index_params": {
            "M": 16,
            "efConstruction": 200,
            "efSearch": 50,
        },
    },
    "knowledge_graph": {
        "type": "in_memory",  # Options: in_memory, networkx
        "relationship_types": [
            "contains", "references", "similar_to", "precedes", "follows"
        ],
    },
    "metadata_store": {
        "type": "in_memory",  # Options: in_memory, indexed
        "indexed_fields": [
            "source_type", "file_type", "creation_date", "author", "tags"
        ],
    },
}

# Versioning Configuration
VERSIONING = {
    "version_controller": {
        "max_versions": 10,
        "auto_snapshot": True,
        "snapshot_interval": 3600,  # 1 hour
    },
    "change_tracker": {
        "track_content_changes": True,
        "track_metadata_changes": True,
        "max_changes": 100,
    },
}

# Integration Configuration
INTEGRATION = {
    "foundation_layer": {
        "config_path": "../01_foundation_layer/config",
    },
    "agent_generation": {
        "knowledge_format": "structured",
        "include_metadata": True,
    },
}