#!/usr/bin/env python3
"""
GitHub Repository Creation Script

This script helps you create a new GitHub repository for the Contact Flow Comparison tool
and sets up the initial structure.
"""

import json
import os
import sys
from ghapi.all import GhApi


def get_github_token():
    """Get GitHub token from user"""
    print("🔑 GitHub Authentication")
    print("You need a GitHub Personal Access Token with 'repo' permissions.")
    print("Create one at: https://github.com/settings/tokens")
    print()
    
    token = input("Enter your GitHub Personal Access Token: ").strip()
    if not token:
        print("❌ GitHub token is required")
        sys.exit(1)
    
    return token


def create_repository(api, repo_name, description="", private=False):
    """Create a new GitHub repository"""
    print(f"📁 Creating repository: {repo_name}")
    
    try:
        # Check if repo already exists
        try:
            existing_repo = api.repos.get(repo=repo_name)
            print(f"✅ Repository already exists: {existing_repo.html_url}")
            return existing_repo
        except Exception:
            pass  # Repo doesn't exist, continue with creation
        
        # Create new repository
        repo_data = {
            "name": repo_name,
            "description": description,
            "private": private,
            "auto_init": True,  # Initialize with README
            "gitignore_template": "Python"
        }
        
        repo = api.repos.create(**repo_data)
        print(f"✅ Repository created successfully!")
        print(f"🔗 URL: {repo.html_url}")
        
        return repo
        
    except Exception as e:
        print(f"❌ Failed to create repository: {e}")
        sys.exit(1)


def setup_initial_structure(repo_owner, repo_name):
    """Set up initial directory structure"""
    print("📂 Setting up initial directory structure...")
    
    # Create directories
    directories = [
        "imports/resources/flows",
        ".github/workflows",
        "docs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create initial README
    readme_content = f"""# {repo_name}

Amazon Connect Contact Flow Comparison Repository

This repository contains Amazon Connect contact flows and is configured with automated comparison tools to track changes.

## Structure

- `imports/resources/flows/` - Contact flow JSON files
- `.github/workflows/` - GitHub Actions workflows
- `docs/` - Documentation

## Setup

This repository is configured to use the Contact Flow Comparison GitHub Action.
When you push changes to contact flows, the action will automatically generate comparison reports.

## Contact Flows

Add your Amazon Connect contact flow JSON files to the `imports/resources/flows/` directory.

## Generated Reports

After pushing contact flow changes, check the GitHub Actions artifacts for:
- Individual flow comparison HTML files
- Bedrock metrics and performance data
- Summary index of all changes
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    print("✅ Created README.md")
    
    # Create sample contact flow
    sample_flow = {
        "Version": "2019-10-30",
        "StartAction": "start-action-id",
        "Actions": [
            {
                "Identifier": "start-action-id",
                "Type": "MessageParticipant",
                "Parameters": {
                    "Text": "Welcome to our contact center. How can we help you today?"
                },
                "Transitions": {
                    "NextAction": "end-action-id"
                }
            },
            {
                "Identifier": "end-action-id",
                "Type": "DisconnectParticipant",
                "Parameters": {}
            }
        ]
    }
    
    sample_path = "imports/resources/flows/welcome-flow.json"
    with open(sample_path, "w") as f:
        json.dump(sample_flow, f, indent=2)
    print(f"✅ Created sample contact flow: {sample_path}")
    
    # Create .gitignore additions
    gitignore_additions = """
# Contact Flow Comparison Tool
deployment/config.json
deployment/aws_config.json
deployment/github_config.json
*.html
venv/
.env
"""
    
    with open(".gitignore", "a") as f:
        f.write(gitignore_additions)
    print("✅ Updated .gitignore")


def initialize_git_repo(repo_url):
    """Initialize local git repository"""
    print("🔧 Initializing local git repository...")
    
    import subprocess
    
    try:
        # Initialize git if not already done
        if not os.path.exists(".git"):
            subprocess.run(["git", "init"], check=True)
            print("✅ Git repository initialized")
        
        # Add remote origin
        try:
            subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
            print("✅ Remote origin added")
        except subprocess.CalledProcessError:
            # Remote might already exist
            subprocess.run(["git", "remote", "set-url", "origin", repo_url], check=True)
            print("✅ Remote origin updated")
        
        # Add and commit initial files
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial setup for Contact Flow Comparison"], check=True)
        print("✅ Initial commit created")
        
        # Push to GitHub
        subprocess.run(["git", "branch", "-M", "main"], check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
        print("✅ Pushed to GitHub")
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git operation failed: {e}")
        print("You may need to push manually later")


def main():
    """Main repository creation function"""
    print("🚀 GitHub Repository Setup for Contact Flow Comparison")
    print("=" * 60)
    
    # Get GitHub token
    github_token = get_github_token()
    
    # Initialize GitHub API
    try:
        api = GhApi(token=github_token)
        user = api.user.get()
        print(f"👤 Authenticated as: {user.login}")
    except Exception as e:
        print(f"❌ GitHub authentication failed: {e}")
        sys.exit(1)
    
    # Get repository details
    print("\n📝 Repository Configuration:")
    repo_name = input("Repository name: ").strip()
    if not repo_name:
        print("❌ Repository name is required")
        sys.exit(1)
    
    description = input("Repository description (optional): ").strip()
    if not description:
        description = "Amazon Connect Contact Flow Comparison Repository"
    
    private_input = input("Make repository private? (y/N): ").strip().lower()
    private = private_input in ['y', 'yes']
    
    # Create repository
    repo = create_repository(api, repo_name, description, private)
    
    # Set up local structure
    setup_initial_structure(user.login, repo_name)
    
    # Initialize git repository
    initialize_git_repo(repo.clone_url)
    
    # Save configuration for next steps
    repo_config = {
        "github_token": github_token,
        "repo_owner": user.login,
        "repo_name": repo_name,
        "repo_url": repo.html_url,
        "clone_url": repo.clone_url
    }
    
    os.makedirs("deployment", exist_ok=True)
    with open("deployment/repo_config.json", "w") as f:
        json.dump(repo_config, f, indent=2)
    
    print(f"\n✅ Repository setup completed successfully!")
    print(f"📝 Configuration saved to deployment/repo_config.json")
    print(f"🔗 Repository URL: {repo.html_url}")
    
    print(f"\n📋 Next steps:")
    print(f"1. Run the main setup: python deployment/setup.py")
    print(f"2. Configure AWS: python deployment/aws_setup.py")
    print(f"3. Configure GitHub Actions: python deployment/github_setup.py")
    
    print(f"\n💡 Your repository is ready with:")
    print(f"   • Sample contact flow in imports/resources/flows/")
    print(f"   • Proper directory structure")
    print(f"   • Initial README and documentation")


if __name__ == "__main__":
    main()