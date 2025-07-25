#!/usr/bin/env python3
"""
AWS Infrastructure Setup for Contact Flow Comparison Tool

This script sets up the required AWS infrastructure including:
- OIDC Identity Provider for GitHub Actions
- IAM Role with minimal required permissions
- Bedrock access configuration
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError


def load_config():
    """Load deployment configuration"""
    try:
        with open("deployment/config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Configuration file not found. Run setup.py first.")
        sys.exit(1)


def create_oidc_provider(iam_client, repo_owner, repo_name):
    """Create GitHub OIDC identity provider"""
    print("🔐 Setting up GitHub OIDC Identity Provider...")
    
    oidc_url = "https://token.actions.githubusercontent.com"
    thumbprint = "6938fd4d98bab03faadb97b34396831e3780aea1"  # GitHub's thumbprint
    
    try:
        # Check if provider already exists
        try:
            response = iam_client.get_open_id_connect_provider(
                OpenIDConnectProviderArn=f"arn:aws:iam::{config['aws_account_id']}:oidc-provider/token.actions.githubusercontent.com"
            )
            print("✅ OIDC Provider already exists")
            return response['Arn']
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchEntity':
                raise
        
        # Create new OIDC provider
        response = iam_client.create_open_id_connect_provider(
            Url=oidc_url,
            ThumbprintList=[thumbprint],
            ClientIDList=["sts.amazonaws.com"]
        )
        
        print("✅ OIDC Provider created successfully")
        return response['OpenIDConnectProviderArn']
        
    except ClientError as e:
        print(f"❌ Failed to create OIDC provider: {e}")
        sys.exit(1)


def create_iam_role(iam_client, config, oidc_provider_arn):
    """Create IAM role for GitHub Actions"""
    print("👤 Creating IAM Role...")
    
    role_name = f"GitHubActions-ContactFlowComparison-{config['environment']}"
    
    # Trust policy for GitHub Actions
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": oidc_provider_arn
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": f"repo:{config['repo_owner']}/{config['repo_name']}:*"
                    }
                }
            }
        ]
    }
    
    # Permissions policy
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["bedrock-runtime:InvokeModel"],
                "Resource": f"arn:aws:bedrock:{config['aws_region']}:{config['aws_account_id']}:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
            },
            {
                "Effect": "Allow",
                "Action": ["sts:GetCallerIdentity"],
                "Resource": "*"
            }
        ]
    }
    
    try:
        # Create role
        try:
            role_response = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for GitHub Actions Contact Flow Comparison"
            )
            print(f"✅ IAM Role created: {role_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"✅ IAM Role already exists: {role_name}")
                role_response = iam_client.get_role(RoleName=role_name)
            else:
                raise
        
        # Create and attach policy
        policy_name = f"ContactFlowComparisonPolicy-{config['environment']}"
        try:
            policy_response = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(permissions_policy),
                Description="Policy for Contact Flow Comparison GitHub Action"
            )
            policy_arn = policy_response['Policy']['Arn']
            print(f"✅ Policy created: {policy_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                policy_arn = f"arn:aws:iam::{config['aws_account_id']}:policy/{policy_name}"
                print(f"✅ Policy already exists: {policy_name}")
            else:
                raise
        
        # Attach policy to role
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        print("✅ Policy attached to role")
        
        role_arn = f"arn:aws:iam::{config['aws_account_id']}:role/{role_name}"
        return role_arn
        
    except ClientError as e:
        print(f"❌ Failed to create IAM role: {e}")
        sys.exit(1)


def validate_bedrock_access(bedrock_client, config):
    """Validate Bedrock model access"""
    print("🧠 Validating Bedrock access...")
    
    try:
        # Test inference profile access
        model_id = f"arn:aws:bedrock:{config['aws_region']}:{config['aws_account_id']}:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        
        test_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(test_request)
        )
        
        print("✅ Bedrock access validated successfully")
        return True
        
    except ClientError as e:
        print(f"⚠️  Bedrock validation warning: {e}")
        print("   This might be expected if the role hasn't propagated yet")
        return False


def main():
    """Main AWS setup function"""
    print("☁️  AWS Infrastructure Setup")
    print("=" * 40)
    
    config = load_config()
    
    try:
        # Initialize AWS clients
        iam_client = boto3.client('iam', region_name=config['aws_region'])
        bedrock_client = boto3.client('bedrock-runtime', region_name=config['aws_region'])
        
        # Verify AWS credentials
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        print(f"🔍 AWS Account: {identity['Account']}")
        
        if identity['Account'] != config['aws_account_id']:
            print(f"❌ Account mismatch. Expected: {config['aws_account_id']}, Got: {identity['Account']}")
            sys.exit(1)
        
        # Set up infrastructure
        oidc_provider_arn = create_oidc_provider(iam_client, config['repo_owner'], config['repo_name'])
        role_arn = create_iam_role(iam_client, config, oidc_provider_arn)
        validate_bedrock_access(bedrock_client, config)
        
        # Save results
        aws_config = {
            "oidc_provider_arn": oidc_provider_arn,
            "role_arn": role_arn,
            "role_name": role_arn.split('/')[-1]
        }
        
        with open("deployment/aws_config.json", "w") as f:
            json.dump(aws_config, f, indent=2)
        
        print(f"\n✅ AWS setup completed successfully!")
        print(f"📝 Configuration saved to deployment/aws_config.json")
        print(f"\n🔑 Role ARN: {role_arn}")
        print(f"\nNext step: Run GitHub setup with:")
        print(f"python deployment/github_setup.py")
        
    except Exception as e:
        print(f"❌ AWS setup failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()