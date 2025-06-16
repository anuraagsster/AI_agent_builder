#!/usr/bin/env python3
"""
Environment setup script for the Tool Management Service.
This script sets up the development environment with all necessary dependencies.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version meets requirements."""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]} or higher is required")
        sys.exit(1)

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
    else:
        print("Virtual environment already exists")

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    subprocess.run([
        "venv/bin/pip" if os.name != "nt" else "venv\\Scripts\\pip",
        "install", "-r", "requirements.txt"
    ])

def setup_development_environment():
    """Set up the development environment."""
    print("Setting up development environment...")
    
    # Create necessary directories
    directories = [
        "logs",
        "data/tools",         # Tool definitions
        "data/executions",    # Tool execution records
        "data/versions",      # Tool version history
        "config/local",
        "tests/data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Create example configuration files
    config_template = """
# Tool Management Service Configuration
environment: development
log_level: DEBUG

# Tool Registry Settings
registry:
  storage_path: "data/tools"
  version_control: true
  auto_update: true
  
# Tool Execution Settings
execution:
  max_concurrent: 10
  timeout: 300
  retry_attempts: 3
  
# Client Settings
client:
  tool_isolation: true
  access_control: true
    """
    
    with open("config/local/config.yaml", "w") as f:
        f.write(config_template)

def main():
    """Main function to set up the environment."""
    print("Starting environment setup...")
    
    check_python_version()
    create_virtual_environment()
    install_dependencies()
    setup_development_environment()
    
    print("Environment setup completed successfully!")

if __name__ == "__main__":
    main() 