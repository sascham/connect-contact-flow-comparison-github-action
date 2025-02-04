# Contact Flow Comparison Action Setup Guide

## Overview

This guide explains how to use the Contact Flow Comparison GitHub Action - a tool designed to monitor and compare changes in Amazon Connect contact flows. The workflow automatically runs whenever changes are made to contact flow files in your specified directory and pushed into Github. Upon running, it compares the current version of the contact flows with the previous version. Results are provided as HTML files in your GitHub Actions workflow artifacts. These include:

- A main index page linking to individual flow comparisons
- A metrics page showing Bedrock API performance data (such as token usage, response times, and retry attempts)

## Prerequisites

- GitHub repository with Amazon Connect contact flows
- GitHub Actions enabled in your repository
- AWS Account with the following permissions:

```
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["bedrock-runtime:InvokeModel"],
        "Resource": "arn:aws:bedrock:us-east-1:YOUR_ACCOUNT_ID:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
      },
      {
        "Effect": "Allow",
        "Action": ["sts:GetCallerIdentity"],
        "Resource": "*"
      }
    ]
  }
```

- This solution is using OIDC between Github and AWS as it is the preferred method to [authenticate securely](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services). You could also use an access key and access secret if unable to use OIDC.

## Required Permissions

    permissions:
    id-token: write
    contents: read

## Required Secrets

Github_PAT: GitHub Personal Access Token with repository access

## Required Variables

ACCOUNT: AWS Account ID (should be set in repository variables)

## Directory Structure

Your repository should have a structure similar to:

    repository/
    ├── imports/
    │ └── resources/
    │ └── flows/ # Default contact flow directory
    └── [other directories]

## Workflow Setup

Create a new workflow file (e.g., .github/workflows/workflow.yml)

Add the following workflow configuration:

Create a new workflow file (e.g., .github/workflows/compare-flows.yml):

    name: Contact Flows Comparison Action

    on:
      push:
        paths:
          - "imports/resources/flows/**"

    concurrency:
      group: ${{ github.workflow }}-${{ github.ref }}
      cancel-in-progress: true

    permissions:
      id-token: write
      contents: read

    jobs:
      compare_flows:
        name: compare
        runs-on: ubuntu-latest
        environment: dev
        steps:
          - uses: actions/checkout@v4
            with:
              fetch-depth: 2  # Fetch the current and previous commit

          # Initial AWS Authentication
          - name: Configure AWS Credentials
            uses: aws-actions/configure-aws-credentials@v4
            with:
              role-to-assume: arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_OIDC_ROLE
              aws-region: us-east-1

          - name: Run Compare Action
            uses: aws-samples/connect-contact-flow-comparison-github-action@main
            env:
              ENVIRONMENT: dev
            with:
              github_pat: ${{ secrets.FLOW_COMPARE_PAT }}
              repo_owner: YOUR_GITHUB_USERNAME
              repo: YOUR_REPOSITORY_NAME
              commit_sha: ${{ github.sha }}
              contact_flow_path: ${{ vars.CONTACT_FLOW_PATH }}

## Configuration Parameters

### Action Inputs

| Input               | Description                  | Required |
| ------------------- | ---------------------------- | -------- |
| `github_pat`        | GitHub Personal Access Token | Yes      |
| `repo_owner`        | Owner of the repository      | Yes      |
| `repo`              | Repository name              | Yes      |
| `commit_sha`        | Commit SHA for comparison    | Yes      |
| `contact_flow_path` | Path to contact flow files   | Yes      |

### Usage

Set up the required secrets in your GitHub repository:

- Go to Settings > Secrets and Variables > Actions
- Add required secrets (FLOW_COMPARE_PAT)

Set up repository variables:

- Add required variables (ACCOUNT)

The workflow will automatically trigger when:

- Changes are pushed to files in the specified contact flow path

The action will compare contact flows between the current and previous commit

Results will be html pages available in the GitHub Actions workflow run as an artifact

- index.html will link to all of the individual flows
- bedrock_metrics.html will show various metrics from bedrock including token usage, latencies, retries, etc.,

### Notes

- Ensure your contact flows are in the correct format and location
- Make sure AWS credentials are properly configured

### Example of a simple contact flow change

![[example]](./images/contact_flow_change.png)

### Contributing

[Contributing](./CONTRIBUTING.md)

### License

[License](./LICENSE)
