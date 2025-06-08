from setuptools import setup, find_packages

setup(
    name="tool_management_service",
    version="0.1.0",
    description="Tool Management Service for Autonomous AI Agent Creator System",
    author="AI Agent Creator Team",
    packages=find_packages(),
    install_requires=[
        "jsonschema>=4.0.0",
        "semver>=2.13.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ],
        "mcp": [
            "mcp-sdk>=0.1.0",  # Placeholder for MCP SDK
        ],
    },
    python_requires=">=3.10",
)