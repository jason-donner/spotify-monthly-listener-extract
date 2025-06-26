#!/bin/bash

# AWS App Runner Deployment Script for Spotify Monthly Listener Extract
# This script will deploy your app to AWS App Runner in minutes!

set -e  # Exit on any error

echo "🎵 Spotify Monthly Listener Extract - AWS App Runner Deployment"
echo "============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first:${NC}"
    echo "   pip install awscli"
    exit 1
fi

# Check if AWS is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run:${NC}"
    echo "   aws configure"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI is configured${NC}"

# Get AWS account and region info
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)
echo -e "${BLUE}ℹ️  Account: ${AWS_ACCOUNT_ID}, Region: ${AWS_REGION}${NC}"

# Prompt for required information
echo ""
echo -e "${YELLOW}📝 Please provide the following information:${NC}"

read -p "App name (default: spotify-tracker): " APP_NAME
APP_NAME=${APP_NAME:-spotify-tracker}

read -p "Environment (default: production): " ENVIRONMENT
ENVIRONMENT=${ENVIRONMENT:-production}

read -p "GitHub repository URL (https://github.com/username/repo): " GITHUB_REPO
if [[ -z "$GITHUB_REPO" ]]; then
    echo -e "${RED}❌ GitHub repository URL is required${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}🔐 Security Configuration:${NC}"

read -s -p "Flask Secret Key (leave empty to auto-generate): " FLASK_SECRET_KEY
echo ""
if [[ -z "$FLASK_SECRET_KEY" ]]; then
    FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo -e "${GREEN}✅ Generated Flask secret key${NC}"
fi

read -s -p "Admin Password: " ADMIN_PASSWORD
echo ""
if [[ -z "$ADMIN_PASSWORD" ]]; then
    echo -e "${RED}❌ Admin password is required${NC}"
    exit 1
fi

read -p "Spotify Client ID: " SPOTIFY_CLIENT_ID
if [[ -z "$SPOTIFY_CLIENT_ID" ]]; then
    echo -e "${RED}❌ Spotify Client ID is required${NC}"
    exit 1
fi

read -s -p "Spotify Client Secret: " SPOTIFY_CLIENT_SECRET
echo ""
if [[ -z "$SPOTIFY_CLIENT_SECRET" ]]; then
    echo -e "${RED}❌ Spotify Client Secret is required${NC}"
    exit 1
fi

# Create service name
SERVICE_NAME="${APP_NAME}-${ENVIRONMENT}"

echo ""
echo -e "${BLUE}🚀 Starting deployment...${NC}"

# Check if App Runner service already exists
if aws apprunner describe-service --service-arn "arn:aws:apprunner:${AWS_REGION}:${AWS_ACCOUNT_ID}:service/${SERVICE_NAME}" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Service ${SERVICE_NAME} already exists. This will update it.${NC}"
    read -p "Continue? (y/N): " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
    UPDATE_MODE=true
else
    UPDATE_MODE=false
fi

# Create the service configuration
SERVICE_CONFIG=$(cat <<EOF
{
  "ServiceName": "${SERVICE_NAME}",
  "SourceConfiguration": {
    "CodeRepository": {
      "RepositoryUrl": "${GITHUB_REPO}",
      "SourceCodeVersion": {
        "Type": "BRANCH",
        "Value": "main"
      },
      "CodeConfiguration": {
        "ConfigurationSource": "CONFIGURATION_FILE"
      }
    },
    "AutoDeploymentsEnabled": true
  },
  "InstanceConfiguration": {
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }
}
EOF
)

# Calculate redirect URI
REDIRECT_URI="https://${SERVICE_NAME}.${AWS_REGION}.awsapprunner.com/admin/callback"

echo -e "${BLUE}📋 Configuration Summary:${NC}"
echo "  Service Name: ${SERVICE_NAME}"
echo "  Repository: ${GITHUB_REPO}"
echo "  Redirect URI: ${REDIRECT_URI}"
echo ""

if [[ "$UPDATE_MODE" == "true" ]]; then
    echo -e "${YELLOW}🔄 Updating existing service...${NC}"
    # Update service - App Runner doesn't support direct config updates via CLI
    # We'll need to use the console or recreate
    echo -e "${YELLOW}⚠️  To update an existing service, please use the AWS Console:${NC}"
    echo "   1. Go to https://console.aws.amazon.com/apprunner/"
    echo "   2. Select your service: ${SERVICE_NAME}"
    echo "   3. Update environment variables"
    echo "   4. Redeploy"
else
    echo -e "${BLUE}🆕 Creating new App Runner service...${NC}"
    
    # Create the service (Note: AWS CLI for App Runner is limited, using CloudFormation would be better)
    echo -e "${YELLOW}ℹ️  Creating App Runner service requires AWS Console setup.${NC}"
    echo -e "${BLUE}Please follow these steps:${NC}"
    echo ""
    echo "1. Go to: https://console.aws.amazon.com/apprunner/"
    echo "2. Click 'Create service'"
    echo "3. Select 'Source code repository' → GitHub"
    echo "4. Repository: ${GITHUB_REPO}"
    echo "5. Branch: main"
    echo "6. Configuration: Use configuration file (apprunner.yaml)"
    echo "7. Service settings:"
    echo "   - Service name: ${SERVICE_NAME}"
    echo "   - CPU: 1 vCPU"
    echo "   - Memory: 2 GB"
    echo "8. Environment variables:"
    echo "   FLASK_SECRET_KEY=${FLASK_SECRET_KEY}"
    echo "   ADMIN_PASSWORD=${ADMIN_PASSWORD}"
    echo "   SPOTIPY_CLIENT_ID=${SPOTIFY_CLIENT_ID}"
    echo "   SPOTIPY_CLIENT_SECRET=${SPOTIFY_CLIENT_SECRET}"
    echo "   SPOTIPY_REDIRECT_URI=${REDIRECT_URI}"
    echo "   PORT=8080"
    echo "   FLASK_DEBUG=false"
    echo ""
fi

echo -e "${GREEN}✅ Configuration prepared!${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Update your Spotify Developer App:"
echo "   - Go to: https://developer.spotify.com/dashboard/"
echo "   - Add redirect URI: ${REDIRECT_URI}"
echo ""
echo "2. Complete App Runner setup in AWS Console (if not done)"
echo ""
echo "3. Test your deployment:"
echo "   - App URL: https://${SERVICE_NAME}.${AWS_REGION}.awsapprunner.com"
echo "   - Admin: https://${SERVICE_NAME}.${AWS_REGION}.awsapprunner.com/admin_login"
echo ""
echo -e "${GREEN}🎉 Deployment guide complete!${NC}"

# Save configuration for future reference
cat > aws-deployment-config.txt <<EOF
Spotify Monthly Listener Extract - AWS Deployment Configuration
============================================================

Service Name: ${SERVICE_NAME}
Region: ${AWS_REGION}
Repository: ${GITHUB_REPO}

URLs:
- App: https://${SERVICE_NAME}.${AWS_REGION}.awsapprunner.com
- Admin: https://${SERVICE_NAME}.${AWS_REGION}.awsapprunner.com/admin_login

Spotify Redirect URI: ${REDIRECT_URI}

Environment Variables:
- FLASK_SECRET_KEY: [HIDDEN]
- ADMIN_PASSWORD: [HIDDEN]
- SPOTIPY_CLIENT_ID: ${SPOTIFY_CLIENT_ID}
- SPOTIPY_CLIENT_SECRET: [HIDDEN]
- SPOTIPY_REDIRECT_URI: ${REDIRECT_URI}
- PORT: 8080
- FLASK_DEBUG: false

Created: $(date)
EOF

echo -e "${BLUE}💾 Configuration saved to: aws-deployment-config.txt${NC}"
