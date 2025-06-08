from setuptools import setup, find_packages

setup(
    name="foundation_layer",
    version="0.1.0",
    description="Foundation Layer for Autonomous AI Agent Creator System",
    author="AI Agent Creator Team",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.28.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ],
    },
    python_requires=">=3.10",
)