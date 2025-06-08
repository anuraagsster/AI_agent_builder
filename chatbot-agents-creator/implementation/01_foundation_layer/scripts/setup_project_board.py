#!/usr/bin/env python3
"""
Script to set up a GitHub project board for the Foundation Layer implementation.
This script uses the GitHub API to create a project board with columns for tracking tasks.

Usage:
    python setup_project_board.py --token <github_token> --repo <owner/repo>

Requirements:
    - requests
"""

import argparse
import requests
import json


def create_project(token, repo, name, description):
    """Create a new GitHub project."""
    url = f"https://api.github.com/repos/{repo}/projects"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.inertia-preview+json"
    }
    
    data = {
        "name": name,
        "body": description
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code in [200, 201]:
        project = response.json()
        print(f"Project '{name}' created successfully with ID {project['id']}")
        return project
    else:
        print(f"Failed to create project: {response.status_code}")
        print(response.text)
        return None


def create_column(token, project_id, name):
    """Create a column in the GitHub project."""
    url = f"https://api.github.com/projects/{project_id}/columns"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.inertia-preview+json"
    }
    
    data = {
        "name": name
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code in [200, 201]:
        column = response.json()
        print(f"Column '{name}' created successfully with ID {column['id']}")
        return column
    else:
        print(f"Failed to create column: {response.status_code}")
        print(response.text)
        return None


def main():
    parser = argparse.ArgumentParser(description="Set up a GitHub project board")
    parser.add_argument("--token", required=True, help="GitHub personal access token")
    parser.add_argument("--repo", required=True, help="GitHub repository in the format owner/repo")
    args = parser.parse_args()
    
    # Create the project
    project = create_project(
        args.token, 
        args.repo, 
        "Foundation Layer Implementation", 
        "Project board for tracking the implementation of the Foundation Layer components"
    )
    
    if project:
        # Create columns
        columns = [
            "To Do",
            "In Progress",
            "Code Review",
            "Testing",
            "Done"
        ]
        
        for column_name in columns:
            create_column(args.token, project["id"], column_name)


if __name__ == "__main__":
    main()