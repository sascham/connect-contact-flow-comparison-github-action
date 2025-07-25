#!/usr/bin/env python3
"""
GitHub Repository Setup for Contact Flow Comparison Tool

This script sets up the GitHub repository with:
- Workflow file creation
- Repository secrets configuration
- Repository variables setup
"""

import json
import os
import sys
from ghapi.all import GhApi


def load_configs():
    """Load deployment and AWS configurations"""
    try:
        with open("deployment/config.json", "r") as f:
            config = json.load(f)
        with open("deployment/aws_config.json", "r") as f:
            aws_config = json.load(f)
        return config, aws_config
    except FileNotFoundError as e:
        print(f"❌ Configuration file not found: {e}")
        print("Run setup.py and aws_setup.py first.")
        sys.exit(1)


def create_workflow_file(config, aws_config):
    """Create GitHub Actions workflow file"""
    print("📝 Creating GitHub Actions workflow...")
    
    workflow_content = f"""name: Contact Flows Comparison Action

on:
  push:
    paths:
      - "{config['contact_flow_path']}/**"

concurrency:
  group: ${{{{ github.workflow }}}}-${{{{ github.ref }}}}
  cancel-in-progress: true

permissions:
  id-token: write
  contents: read

jobs:
  compare_flows:
    name: compare
    runs-on: ubuntu-latest
    environment: {config['environment']}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2  # Fetch the current and previous commit

      # Initial AWS Authentication
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: {aws_config['role_arn']}
          aws-region: {config['aws_region']}

      - name: Run Compare Action
        uses: aws-samples/connect-contact-flow-comparison-github-action@main
        env:
          ENVIRONMENT: {config['environment']}
        with:
          github_pat: ${{{{ secrets.FLOW_COMPARE_PAT }}}}
          repo_owner: {config['repo_owner']}
          repo: {config['repo_name']}
          commit_sha: ${{{{ github.sha }}}}
          contact_flow_path: ${{{{ vars.CONTACT_FLOW_PATH }}}}
"""
    
    # Create .github/workflows directory
    os.makedirs(".github/workflows", exist_ok=True)
    
    # Write workflow file
    workflow_path = ".github/workflows/compare-flows.yml"
    with open(workflow_path, "w") as f:
        f.write(workflow_content)
    
    print(f"✅ Workflow file created: {workflow_path}")
    return workflow_path


def setup_github_secrets_and_variables(config, aws_config):
    """Set up GitHub repository secrets and variables"""
    print("🔐 Setting up GitHub secrets and variables...")
    
    try:
        # Initialize GitHub API
        api = GhApi(token=config['github_token'])
        
        # Test repository access
        repo_info = api.repos.get(owner=config['repo_owner'], repo=config['repo_name'])
        print(f"✅ Repository access confirmed: {repo_info.full_name}")
        
        # Set up secrets
        secrets_to_set = {
            "FLOW_COMPARE_PAT": config['github_token']
        }
        
        for secret_name, secret_value in secrets_to_set.items():
            try:
                # Get repository public key for encryption
                public_key = api.actions.get_repo_public_key(
                    owner=config['repo_owner'],
                    repo=config['repo_name']
                )
                
                # Note: In a real implementation, you'd encrypt the secret value
                # For now, we'll just indicate what needs to be set
                print(f"🔑 Secret '{secret_name}' needs to be set manually in GitHub")
                print(f"   Go to: https://github.com/{config['repo_owner']}/{config['repo_name']}/settings/secrets/actions")
                
            except Exception as e:
                print(f"⚠️  Could not set secret {secret_name}: {e}")
        
        # Set up variables
        variables_to_set = {
            "CONTACT_FLOW_PATH": config['contact_flow_path'],
            "ACCOUNT": config['aws_account_id']
        }
        
        for var_name, var_value in variables_to_set.items():
            try:
                # Check if variable exists
                try:
                    api.actions.get_repo_variable(
                        owner=config['repo_owner'],
                        repo=config['repo_name'],
                        name=var_name
                    )
                    # Update existing variable
                    api.actions.update_repo_variable(
                        owner=config['repo_owner'],
                        repo=config['repo_name'],
                        name=var_name,
                        value=var_value
                    )
                    print(f"✅ Updated variable: {var_name}")
                except:
                    # Create new variable
                    api.actions.create_repo_variable(
                        owner=config['repo_owner'],
                        repo=config['repo_name'],
                        name=var_name,
                        value=var_value
                    )
                    print(f"✅ Created variable: {var_name}")
                    
            except Exception as e:
                print(f"⚠️  Could not set variable {var_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub setup failed: {e}")
        return False


def create_sample_contact_flow():
    """Create sample contact flow for testing"""
    print("📁 Creating sample contact flow structure...")
    
    config, _ = load_configs()
    flow_dir = config['contact_flow_path']
    
    # Create directory structure
    os.makedirs(flow_dir, exist_ok=True)
    
    # Sample contact flow
    sample_flow = {
        "Version": "2019-10-30",
        "StartAction": "12345678-1234-1234-1234-123456789012",
        "Actions": [
            {
                "Identifier": "12345678-1234-1234-1234-123456789012",
                "Type": "MessageParticipant",
                "Parameters": {
                    "Text": "Hello! Welcome to our contact center."
                },
                "Transitions": {
                    "NextAction": "87654321-4321-4321-4321-210987654321"
                }
            },
            {
                "Identifier": "87654321-4321-4321-4321-210987654321",
                "Type": "DisconnectParticipant",
                "Parameters": {}
            }
        ]
    }
    
    # Write sample flow
    sample_path = os.path.join(flow_dir, "sample-flow.json")
    with open(sample_path, "w") as f:
        json.dump(sample_flow, f, indent=2)
    
    print(f"✅ Sample contact flow created: {sample_path}")
    return sample_path


def main():
    """Main GitHub setup function"""
    print("📱 GitHub Repository Setup")
    print("=" * 40)
    
    config, aws_config = load_configs()
    
    try:
        # Create workflow file
        workflow_path = create_workflow_file(config, aws_config)
        
        # Setup secrets and variables
        github_success = setup_github_secrets_and_variables(config, aws_config)
        
        # Create sample contact flow
        sample_path = create_sample_contact_flow()
        
        # Save GitHub configuration
        github_config = {
            "workflow_path": workflow_path,
            "sample_flow_path": sample_path,
            "setup_complete": github_success
        }
        
        with open("deployment/github_config.json", "w") as f:
            json.dump(github_config, f, indent=2)
        
        print(f"\n✅ GitHub setup completed!")
        print(f"📝 Configuration saved to deployment/github_config.json")
        
        print(f"\n📋 Manual steps required:")
        print(f"1. Set the FLOW_COMPARE_PAT secret in GitHub:")
        print(f"   https://github.com/{config['repo_owner']}/{config['repo_name']}/settings/secrets/actions")
        print(f"2. Commit and push the workflow file: {workflow_path}")
        print(f"3. Test by modifying a contact flow in: {config['contact_flow_path']}")
        
        print(f"\nNext step: Test the deployment with:")
        print(f"python deployment/test_deployment.py")
        
    except Exception as e:
        print(f"❌ GitHub setup failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()