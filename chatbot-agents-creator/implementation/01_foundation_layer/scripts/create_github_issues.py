#!/usr/bin/env python3
"""
Script to create GitHub issues for the Foundation Layer implementation tasks.
This script uses the GitHub API to create issues based on the sample issues in the
sample_issues directory.

Usage:
    python create_github_issues.py --token <github_token> --repo <owner/repo>

Requirements:
    - requests
    - PyYAML
"""

import argparse
import os
import re
import yaml
import requests
import json
from pathlib import Path


def parse_issue_file(file_path):
    """Parse a GitHub issue template file and extract the front matter and content."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Extract front matter
    front_matter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not front_matter_match:
        raise ValueError(f"No front matter found in {file_path}")

    front_matter_str = front_matter_match.group(1)
    front_matter = yaml.safe_load(front_matter_str)

    # Extract content (everything after the front matter)
    body = content[front_matter_match.end():]

    return front_matter, body


def create_github_issue(token, repo, title, body, labels=None, assignees=None):
    """Create a GitHub issue using the GitHub API."""
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body,
        "labels": labels or [],
        "assignees": assignees or []
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        issue = response.json()
        print(f"Created issue #{issue['number']}: {issue['title']}")
        print(f"URL: {issue['html_url']}")
        return issue
    else:
        print(f"Failed to create issue: {response.status_code}")
        print(response.text)
        return None


def main():
    parser = argparse.ArgumentParser(description="Create GitHub issues from template files")
    parser.add_argument("--token", required=True, help="GitHub personal access token")
    parser.add_argument("--repo", required=True, help="GitHub repository in the format owner/repo")
    parser.add_argument("--day", type=int, default=1, help="Day number to create issues for (default: 1)")
    args = parser.parse_args()

    # Find all sample issue files for the specified day
    sample_issues_dir = Path(__file__).parent.parent / "sample_issues"
    day_pattern = f"day{args.day}_"
    
    issue_files = [f for f in os.listdir(sample_issues_dir) if f.startswith(day_pattern) and f.endswith(".md")]
    
    if not issue_files:
        print(f"No issue templates found for day {args.day}")
        return

    for issue_file in issue_files:
        file_path = sample_issues_dir / issue_file
        try:
            front_matter, body = parse_issue_file(file_path)
            
            title = front_matter.get("title", f"Day {args.day} Task")
            labels = front_matter.get("labels", "").split(", ") if isinstance(front_matter.get("labels"), str) else front_matter.get("labels", [])
            assignees = front_matter.get("assignees", "").split(", ") if isinstance(front_matter.get("assignees"), str) else front_matter.get("assignees", [])
            
            # Remove placeholder assignees
            if assignees and assignees[0] == 'developer-name':
                assignees = []
                
            create_github_issue(args.token, args.repo, title, body, labels, assignees)
            
        except Exception as e:
            print(f"Error processing {issue_file}: {e}")


if __name__ == "__main__":
    main()