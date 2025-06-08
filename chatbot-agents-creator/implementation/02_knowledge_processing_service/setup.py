from setuptools import setup, find_packages

setup(
    name="knowledge_processing_service",
    version="0.1.0",
    description="Knowledge Processing Service for Autonomous AI Agent Creator System",
    author="AI Agent Creator Team",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "requests>=2.28.0",
        "python-dotenv>=1.0.0",
        "beautifulsoup4>=4.10.0",  # For HTML parsing
        "PyPDF2>=2.0.0",           # For PDF parsing
        "python-docx>=0.8.11",     # For DOCX parsing
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ],
        "vector_db": [
            "faiss-cpu>=1.7.0",    # For efficient vector search
            "hnswlib>=0.6.0",      # Alternative vector search library
        ],
        "graph_db": [
            "networkx>=2.8.0",     # For graph operations
        ],
    },
    python_requires=">=3.10",
)