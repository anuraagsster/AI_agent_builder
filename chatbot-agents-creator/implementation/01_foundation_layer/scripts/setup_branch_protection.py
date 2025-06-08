#!/usr/bin/env python3
"""
Script to set up branch protection rules for the Foundation Layer repository.
This script uses the GitHub API to configure branch protection rules for the main branch.

Usage:
    python setup_branch_protection.py --token <github_token> --repo <owner/repo>

Requirements:
    - requests
"""

import argparse
import requests
import json


def setup_branch_protection(token, repo, branch="main"):
    """Set up branch protection rules for the specified branch."""
    url = f"https://api.github.com/repos/{repo}/branches/{branch}/protection"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Define branch protection rules
    data = {
        "required_status_checks": {
            "strict": True,
            "contexts": ["Foundation Layer CI"]
        },
        "enforce_admins": False,
        "required_pull_request_reviews": {
            "dismissal_restrictions": {},
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 1
        },
        "restrictions": None
    }
    
    response = requests.put(url, headers=headers, data=json.dumps(data))
    if response.status_code in [200, 201]:
        print(f"Branch protection rules set up successfully for {branch}")
        return True
    else:
        print(f"Failed to set up branch protection rules: {response.status_code}")
        print(response.text)
        return False


def setup_codeowners(token, repo):
    """Create a CODEOWNERS file in the .github directory."""
    url = f"https://api.github.com/repos/{repo}/contents/.github/CODEOWNERS"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    content = """# Code Owners for Foundation Layer
# These owners will be automatically requested for review on PRs

# Default owners for everything
*       @project-lead

# Foundation Layer specific owners
/implementation/01_foundation_layer/src/config_management/       @config-expert
/implementation/01_foundation_layer/src/architecture/           @architecture-expert
/implementation/01_foundation_layer/src/agent_framework/         @agent-expert
/implementation/01_foundation_layer/src/workload_management/    @workload-expert
/implementation/01_foundation_layer/src/deployment/             @deployment-expert

# Tests
/implementation/01_foundation_layer/tests/                      @test-expert
"""
    
    data = {
        "message": "Add CODEOWNERS file",
        "content": content.encode("utf-8").hex(),
        "branch": "main"
    }
    
    response = requests.put(url, headers=headers, data=json.dumps(data))
    if response.status_code in [200, 201]:
        print("CODEOWNERS file created successfully")
        return True
    else:
        print(f"Failed to create CODEOWNERS file: {response.status_code}")
        print(response.text)
        return False


def main():
    parser = argparse.ArgumentParser(description="Set up branch protection rules")
    parser.add_argument("--token", required=True, help="GitHub personal access token")
    parser.add_argument("--repo", required=True, help="GitHub repository in the format owner/repo")
    parser.add_argument("--branch", default="main", help="Branch to protect (default: main)")
    args = parser.parse_args()
    
    # Set up branch protection rules
    setup_branch_protection(args.token, args.repo, args.branch)
    
    # Create CODEOWNERS file
    setup_codeowners(args.token, args.repo)


if __name__ == "__main__":
    main()