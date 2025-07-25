# Contact Flow Comparison Tool Setup Guide

## Step 1: Create GitHub Repository

### Option A: Create via GitHub Web Interface (Recommended)
1. Go to [GitHub](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Fill in the details:
   - **Repository name**: `contact-flow-comparison` (or your preferred name)
   - **Description**: `Amazon Connect Contact Flow Comparison Repository`
   - **Visibility**: Choose Public or Private
   - ✅ Check "Add a README file"
   - ✅ Check "Add .gitignore" and select "Python"
5. Click "Create repository"

### Option B: Create via Command Line
```bash
# Install GitHub CLI if you haven't already
brew install gh  # macOS
# or
sudo apt install gh  # Ubuntu

# Authenticate with GitHub
gh auth login

# Create repository
gh repo create contact-flow-comparison --public --description "Amazon Connect Contact Flow Comparison Repository" --gitignore Python --license MIT
```

## Step 2: Clone and Set Up Local Repository

```bash
# Clone your new repository
git clone https://github.com/YOUR_USERNAME/contact-flow-comparison.git
cd contact-flow-comparison

# Copy the deployment tools
cp -r /path/to/your/current/deployment ./
cp -r /path/to/your/current/connect-contact-flow-comparison-github-action ./
```

## Step 3: Create Directory Structure

```bash
# Create the required directories
mkdir -p imports/resources/flows
mkdir -p .github/workflows
mkdir -p docs

# Create a sample contact flow
cat > imports/resources/flows/welcome-flow.json << 'EOF'
{
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
EOF
```

## Step 4: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install boto3 ghapi
```

## Step 5: Run Setup Scripts

### 5.1 Initial Configuration
```bash
source venv/bin/activate
python deployment/setup.py
```

This will prompt you for:
- GitHub Personal Access Token
- Repository owner (your GitHub username)
- Repository name
- AWS Account ID
- AWS Region (default: us-east-1)
- Contact flow path (default: imports/resources/flows)
- Environment (default: dev)

### 5.2 AWS Infrastructure Setup
```bash
python deployment/aws_setup.py
```

This will:
- Create GitHub OIDC Identity Provider
- Create IAM role with minimal permissions
- Set up Bedrock access
- Validate the configuration

### 5.3 GitHub Repository Configuration
```bash
python deployment/github_setup.py
```

This will:
- Create the GitHub Actions workflow file
- Set up repository variables
- Guide you through setting up secrets

## Step 6: Manual GitHub Configuration

After running the setup scripts, you'll need to manually set one secret:

1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `FLOW_COMPARE_PAT`
5. Value: Your GitHub Personal Access Token
6. Click "Add secret"

## Step 7: Test the Setup

1. Make a change to a contact flow in `imports/resources/flows/`
2. Commit and push the changes:
   ```bash
   git add .
   git commit -m "Test contact flow change"
   git push
   ```
3. Check the Actions tab in your GitHub repository
4. The workflow should run and generate comparison reports

## GitHub Personal Access Token Setup

To create a GitHub Personal Access Token:

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name like "Contact Flow Comparison"
4. Select these scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
5. Click "Generate token"
6. Copy the token immediately (you won't see it again)

## AWS Prerequisites

Before running the AWS setup, ensure you have:

1. **AWS CLI configured** with appropriate credentials:
   ```bash
   aws configure
   ```

2. **Required AWS permissions** for your user/role:
   - `iam:CreateRole`
   - `iam:CreatePolicy`
   - `iam:AttachRolePolicy`
   - `iam:CreateOpenIDConnectProvider`
   - `bedrock-runtime:InvokeModel`
   - `sts:GetCallerIdentity`

3. **Bedrock model access** in us-east-1 region (or your chosen region)

## Troubleshooting

### Common Issues

1. **"No module named 'setuptools'"**
   ```bash
   pip install setuptools wheel
   ```

2. **AWS permissions errors**
   - Ensure your AWS credentials have the required IAM permissions
   - Check that Bedrock is available in your chosen region

3. **GitHub token issues**
   - Ensure the token has `repo` and `workflow` scopes
   - Check that the token hasn't expired

4. **Workflow not triggering**
   - Ensure changes are made to files in the `contact_flow_path`
   - Check that the workflow file is in `.github/workflows/`

### Getting Help

If you encounter issues:
1. Check the GitHub Actions logs in your repository
2. Review the AWS CloudTrail logs for permission issues
3. Validate your configuration files in the `deployment/` directory

## Next Steps

Once everything is set up:
1. Add your actual Amazon Connect contact flows to `imports/resources/flows/`
2. Customize the workflow triggers if needed
3. Set up notifications or integrations as required
4. Monitor the generated reports for contact flow changes