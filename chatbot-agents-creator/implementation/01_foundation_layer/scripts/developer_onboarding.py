#!/usr/bin/env python3
"""
Developer Onboarding Script for the Foundation Layer implementation.

This script helps junior developers set up their development environment
and understand the project structure. It performs the following tasks:
1. Checks for required dependencies
2. Sets up a virtual environment
3. Installs project dependencies
4. Provides guidance on project structure
5. Opens key documentation files

Usage:
    python developer_onboarding.py

Requirements:
    - Python 3.9+
    - pip
    - virtualenv (optional)
"""

import os
import sys
import subprocess
import platform
import webbrowser
from pathlib import Path


def check_python_version():
    """Check if the Python version is 3.9 or higher."""
    required_version = (3, 9)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]} or higher is required.")
        print(f"Current version: {current_version[0]}.{current_version[1]}")
        return False
    
    print(f"✓ Python version {current_version[0]}.{current_version[1]} detected.")
    return True


def check_pip():
    """Check if pip is installed."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✓ pip is installed.")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: pip is not installed or not in PATH.")
        return False


def setup_virtual_environment():
    """Set up a virtual environment for the project."""
    venv_dir = "venv"
    
    # Check if venv already exists
    if os.path.exists(venv_dir):
        print(f"✓ Virtual environment already exists at {venv_dir}")
        return True
    
    print("Setting up virtual environment...")
    
    try:
        # Try using the built-in venv module first
        subprocess.run([sys.executable, "-m", "venv", venv_dir], 
                      check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✓ Virtual environment created at {venv_dir}")
        return True
    except subprocess.SubprocessError:
        # If that fails, try using virtualenv if available
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "virtualenv"], 
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run([sys.executable, "-m", "virtualenv", venv_dir], 
                          check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"✓ Virtual environment created at {venv_dir} using virtualenv")
            return True
        except subprocess.SubprocessError:
            print("Error: Failed to create virtual environment.")
            return False


def install_dependencies():
    """Install project dependencies."""
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"Error: {requirements_file} not found.")
        return False
    
    print("Installing dependencies...")
    
    # Determine the pip command based on the OS and virtual environment
    pip_cmd = "pip"
    if os.name == "nt":  # Windows
        pip_cmd = os.path.join("venv", "Scripts", "pip")
    else:  # Unix/Linux/Mac
        pip_cmd = os.path.join("venv", "bin", "pip")
    
    if not os.path.exists(pip_cmd):
        pip_cmd = "pip"  # Fall back to system pip if venv pip not found
    
    try:
        subprocess.run([pip_cmd, "install", "-r", requirements_file], 
                      check=True)
        print("✓ Dependencies installed successfully.")
        
        # Install the package in development mode
        subprocess.run([pip_cmd, "install", "-e", "."], 
                      check=True)
        print("✓ Package installed in development mode.")
        
        return True
    except subprocess.SubprocessError:
        print("Error: Failed to install dependencies.")
        return False


def show_project_structure():
    """Display the project structure and key files."""
    print("\n=== Project Structure ===\n")
    
    structure = {
        "src/": "Source code directory",
        "src/architecture/": "System architecture components",
        "src/config_management/": "Configuration management",
        "src/agent_framework/": "Base agent architecture",
        "src/deployment/": "Deployment abstraction",
        "src/workload_management/": "Task and resource management",
        "tests/": "Test suite",
        "tests/unit/": "Unit tests",
        "tests/integration/": "Integration tests",
        "config/": "Configuration files and schemas",
        "examples/": "Example implementations",
        "implementation_guides/": "Detailed implementation guides",
        "scripts/": "Utility scripts"
    }
    
    for path, description in structure.items():
        print(f"{path:<30} {description}")


def open_documentation():
    """Open key documentation files."""
    docs = [
        "README.md",
        "getting_started_guide.md",
        "implementation_status.md",
        "github_workflow_guide.md",
        "implementation_guides/README.md"
    ]
    
    print("\n=== Opening Documentation ===\n")
    
    for doc in docs:
        if os.path.exists(doc):
            print(f"Opening {doc}...")
            
            # Convert to file:// URL
            file_path = os.path.abspath(doc)
            url = f"file://{file_path}"
            
            try:
                webbrowser.open(url)
            except Exception as e:
                print(f"Error opening {doc}: {e}")
        else:
            print(f"Warning: {doc} not found.")


def main():
    """Main function to run the onboarding process."""
    print("\n=== Foundation Layer Developer Onboarding ===\n")
    
    # Get the foundation layer directory
    script_dir = Path(__file__).parent
    foundation_dir = script_dir.parent
    
    # Change to the foundation layer directory
    os.chdir(foundation_dir)
    print(f"Working directory: {os.getcwd()}")
    
    # Check prerequisites
    if not check_python_version() or not check_pip():
        print("\nPlease install the required dependencies and try again.")
        return
    
    # Setup virtual environment
    if not setup_virtual_environment():
        print("\nVirtual environment setup failed. Please set it up manually.")
    
    # Install dependencies
    if not install_dependencies():
        print("\nDependency installation failed. Please install them manually.")
    
    # Show project structure
    show_project_structure()
    
    # Ask if the user wants to open documentation
    print("\nWould you like to open the documentation files? (y/n)")
    response = input().strip().lower()
    
    if response == 'y':
        open_documentation()
    
    print("\n=== Onboarding Complete ===\n")
    print("Next steps:")
    print("1. Read the Getting Started Guide")
    print("2. Review the Implementation Status file")
    print("3. Check your assigned GitHub issues")
    print("4. Follow the GitHub Workflow Guide for development")
    print("\nHappy coding!")


if __name__ == "__main__":
    main()