#!/usr/bin/env python3
"""
Contact Flow Comparison Tool Setup Script

This script helps you set up the Contact Flow Comparison GitHub Action
in your repository with all necessary AWS and GitHub configurations.
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DeploymentConfig:
    """Configuration for deployment setup"""
    github_token: str
    repo_owner: str
    repo_name: str
    aws_account_id: str
    aws_region: str = "us-east-1"
    contact_flow_path: str = "imports/resources/flows"
    environment: str = "dev"


@dataclass
class ValidationResult:
    """Result of validation checks"""
    success: bool
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]


def collect_configuration() -> DeploymentConfig:
    """Collect configuration from user input"""
    print("🚀 Contact Flow Comparison Tool Setup")
    print("=" * 50)
    
    # GitHub configuration
    print("\n📱 GitHub Configuration:")
    github_token = input("GitHub Personal Access Token: ").strip()
    repo_owner = input("Repository Owner (username/org): ").strip()
    repo_name = input("Repository Name: ").strip()
    
    # AWS configuration
    print("\n☁️  AWS Configuration:")
    aws_account_id = input("AWS Account ID: ").strip()
    aws_region = input(f"AWS Region (default: us-east-1): ").strip() or "us-east-1"
    
    # Contact flow configuration
    print("\n📁 Contact Flow Configuration:")
    contact_flow_path = input(f"Contact Flow Path (default: imports/resources/flows): ").strip() or "imports/resources/flows"
    environment = input(f"Environment (default: dev): ").strip() or "dev"
    
    return DeploymentConfig(
        github_token=github_token,
        repo_owner=repo_owner,
        repo_name=repo_name,
        aws_account_id=aws_account_id,
        aws_region=aws_region,
        contact_flow_path=contact_flow_path,
        environment=environment
    )


def validate_configuration(config: DeploymentConfig) -> ValidationResult:
    """Validate the provided configuration"""
    errors = []
    warnings = []
    recommendations = []
    
    # Validate required fields
    if not config.github_token:
        errors.append("GitHub token is required")
    if not config.repo_owner:
        errors.append("Repository owner is required")
    if not config.repo_name:
        errors.append("Repository name is required")
    if not config.aws_account_id:
        errors.append("AWS Account ID is required")
    
    # Validate AWS Account ID format
    if config.aws_account_id and not config.aws_account_id.isdigit():
        errors.append("AWS Account ID must be numeric")
    
    # Validate AWS region
    if config.aws_region != "us-east-1":
        warnings.append("Bedrock inference profiles are optimized for us-east-1")
        recommendations.append("Consider using us-east-1 for better performance")
    
    return ValidationResult(
        success=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        recommendations=recommendations
    )


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Setup Contact Flow Comparison Tool")
    parser.add_argument("--config-file", help="Load configuration from JSON file")
    parser.add_argument("--interactive", action="store_true", default=True, help="Interactive setup")
    
    args = parser.parse_args()
    
    try:
        if args.config_file and os.path.exists(args.config_file):
            with open(args.config_file, 'r') as f:
                config_data = json.load(f)
                config = DeploymentConfig(**config_data)
        else:
            config = collect_configuration()
        
        # Validate configuration
        validation = validate_configuration(config)
        
        if not validation.success:
            print("\n❌ Configuration Validation Failed:")
            for error in validation.errors:
                print(f"  • {error}")
            sys.exit(1)
        
        if validation.warnings:
            print("\n⚠️  Warnings:")
            for warning in validation.warnings:
                print(f"  • {warning}")
        
        if validation.recommendations:
            print("\n💡 Recommendations:")
            for rec in validation.recommendations:
                print(f"  • {rec}")
        
        print(f"\n✅ Configuration validated successfully!")
        print(f"Repository: {config.repo_owner}/{config.repo_name}")
        print(f"AWS Account: {config.aws_account_id}")
        print(f"Region: {config.aws_region}")
        print(f"Contact Flow Path: {config.contact_flow_path}")
        
        # Save configuration for next steps
        os.makedirs("deployment", exist_ok=True)
        with open("deployment/config.json", "w") as f:
            json.dump(config.__dict__, f, indent=2)
        
        print(f"\n📝 Configuration saved to deployment/config.json")
        print(f"\nNext steps:")
        print(f"1. Run AWS setup: python deployment/aws_setup.py")
        print(f"2. Run GitHub setup: python deployment/github_setup.py")
        print(f"3. Test deployment: python deployment/test_deployment.py")
        
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()