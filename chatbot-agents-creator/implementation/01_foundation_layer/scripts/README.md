# Foundation Layer Scripts

This directory contains utility scripts for managing the Foundation Layer implementation.

## GitHub Repository Setup Scripts

### 1. GitHub Issue Creation Script

The `create_github_issues.py` script helps automate the creation of GitHub issues for implementation tasks based on the templates in the `sample_issues` directory.

#### Prerequisites

- Python 3.6+
- GitHub Personal Access Token with repo permissions
- Required Python packages:
  ```
  pip install requests pyyaml
  ```

#### Usage

```bash
# Create issues for day 1
./create_github_issues.py --token YOUR_GITHUB_TOKEN --repo your-org/your-repo --day 1

# Create issues for a specific day
./create_github_issues.py --token YOUR_GITHUB_TOKEN --repo your-org/your-repo --day 3
```

#### Parameters

- `--token`: Your GitHub Personal Access Token
- `--repo`: The GitHub repository in the format `owner/repo`
- `--day`: (Optional) The day number to create issues for (default: 1)

#### Example

```bash
./create_github_issues.py --token ghp_your_token_here --repo your-organization/chatbot-agents-creator --day 1
```

### 2. Branch Protection Setup Script

The `setup_branch_protection.py` script configures branch protection rules for the main branch and creates a CODEOWNERS file.

#### Prerequisites

- Python 3.6+
- GitHub Personal Access Token with admin:repo permissions
- Required Python packages:
  ```
  pip install requests
  ```

#### Usage

```bash
./setup_branch_protection.py --token YOUR_GITHUB_TOKEN --repo your-org/your-repo
```

#### Parameters

- `--token`: Your GitHub Personal Access Token
- `--repo`: The GitHub repository in the format `owner/repo`
- `--branch`: (Optional) The branch to protect (default: main)

#### Example

```bash
./setup_branch_protection.py --token ghp_your_token_here --repo your-organization/chatbot-agents-creator
```

### 3. Project Board Setup Script

The `setup_project_board.py` script creates a GitHub project board with columns for tracking implementation tasks.

#### Prerequisites

- Python 3.6+
- GitHub Personal Access Token with repo permissions
- Required Python packages:
  ```
  pip install requests
  ```

#### Usage

```bash
./setup_project_board.py --token YOUR_GITHUB_TOKEN --repo your-org/your-repo
```

#### Parameters

- `--token`: Your GitHub Personal Access Token
- `--repo`: The GitHub repository in the format `owner/repo`

#### Example

```bash
./setup_project_board.py --token ghp_your_token_here --repo your-organization/chatbot-agents-creator
```

## Repository Initialization

To fully initialize the GitHub repository for the Foundation Layer implementation, run the following commands in order:

```bash
# 1. Set up branch protection rules
./setup_branch_protection.py --token YOUR_GITHUB_TOKEN --repo your-org/your-repo

# 2. Set up project board
./setup_project_board.py --token YOUR_GITHUB_TOKEN --repo your-org/your-repo

# 3. Create day 1 issues
./create_github_issues.py --token YOUR_GITHUB_TOKEN --repo your-org/your-repo --day 1
```

This will configure the repository with all necessary protection rules, create a project board for tracking tasks, and create the initial set of issues for the first day of implementation.

## Developer Onboarding Script

The `developer_onboarding.py` script helps junior developers set up their development environment and understand the project structure.

### Prerequisites

- Python 3.9+
- pip

### Usage

```bash
# Run the onboarding script
./developer_onboarding.py
```

### What It Does

1. Checks for required dependencies (Python version, pip)
2. Sets up a virtual environment
3. Installs project dependencies
4. Provides guidance on project structure
5. Opens key documentation files

### Example

```bash
cd chatbot-agents-creator/implementation/01_foundation_layer
./scripts/developer_onboarding.py
```

This script is particularly useful for junior developers who are new to the project and need help setting up their development environment.