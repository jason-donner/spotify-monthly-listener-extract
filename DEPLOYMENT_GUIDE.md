# Secure AWS App Runner Deployment Guide

This guide walks you through deploying the Spotify Monthly Listener Extract app to AWS App Runner with secure secret management using AWS Secrets Manager.

## Prerequisites

1. **AWS CLI installed and configured**
   ```powershell
   aws configure
   ```

2. **Git repository pushed to GitHub**
   - Ensure your code is on the `main` branch
   - Repository should be public or have GitHub integration with AWS

3. **Spotify Developer App**
   - Create app at: https://developer.spotify.com/dashboard/
   - Note your Client ID and Client Secret

## Quick Deployment

### Step 1: Run the Deployment Script

```powershell
cd aws
.\deploy-apprunner.ps1
```

This script will:
- Generate a secure Flask secret key
- Prompt for your admin password and Spotify credentials
- Create/update secrets in AWS Secrets Manager
- Create an IAM role with appropriate permissions
- Generate deployment configuration

### Step 2: Create App Runner Service

1. Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner/)
2. Click **"Create service"**
3. Configure the service:

   **Source:**
   - Source type: **Repository**
   - Connect to GitHub (if not already connected)
   - Select your repository
   - Branch: **main**
   - Configuration: **Use configuration file (apprunner.yaml)**

   **Service settings:**
   - Service name: Use the name from the deployment script output
   - Instance role: Select the IAM role created by the script (format: `AppRunnerInstanceRole-{service-name}`)

   **Environment variables:** (Add these in the App Runner console)
   ```
   AWS_REGION=us-east-1
   AWS_SECRET_NAME={secret-name-from-script}
   PORT=8080
   FLASK_DEBUG=false
   ```

4. Click **"Create & deploy"**

### Step 3: Update Spotify Developer App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Select your app
3. Click **"Edit Settings"**
4. Under **Redirect URIs**, add:
   ```
   https://{your-service-name}.us-east-1.awsapprunner.com/admin/callback
   ```
5. Save changes

### Step 4: Test Your Deployment

1. Wait for App Runner deployment to complete (usually 5-10 minutes)
2. Visit your app URL: `https://{your-service-name}.us-east-1.awsapprunner.com`
3. Test admin login: `https://{your-service-name}.us-east-1.awsapprunner.com/admin_login`

## Security Features

### AWS Secrets Manager
- All sensitive credentials are stored securely in AWS Secrets Manager
- Secrets are loaded at application startup
- No sensitive data is committed to your repository
- IAM role provides least-privilege access to secrets

### Environment Variables
- Only non-sensitive configuration is set as environment variables
- Sensitive data (passwords, API keys) comes from Secrets Manager
- Production-safe configuration

### IAM Permissions
The deployment script creates an IAM role with minimal permissions:
- `secretsmanager:GetSecretValue` - Only for the specific secret created
- Scoped to your exact secret ARN

## Troubleshooting

### Deployment Issues

**Build fails with dependency errors:**
- Check that `boto3` is in `webapp/requirements.txt`
- Verify Dockerfile is properly configured

**App starts but can't load secrets:**
- Verify IAM role is attached to App Runner service
- Check AWS region matches in environment variables
- Confirm secret name is correct

**Spotify OAuth errors:**
- Verify redirect URI is exactly correct in Spotify Developer App
- Check that SPOTIPY_REDIRECT_URI matches your App Runner URL

### Monitoring

**View App Runner logs:**
1. Go to App Runner console
2. Select your service
3. Click "Logs" tab
4. View application logs for errors

**Check Secrets Manager:**
1. Go to [AWS Secrets Manager Console](https://console.aws.amazon.com/secretsmanager/)
2. Find your secret (named like `spotify-listener-extract/{service-name}`)
3. Verify all required keys are present

## Updating Secrets

To update secrets (e.g., change admin password):

```powershell
# Update the secret in AWS Secrets Manager
aws secretsmanager update-secret --secret-id "spotify-listener-extract/{service-name}" --secret-string '{
  "FLASK_SECRET_KEY": "your-flask-secret",
  "ADMIN_PASSWORD": "new-admin-password",
  "SPOTIPY_CLIENT_ID": "your-client-id",
  "SPOTIPY_CLIENT_SECRET": "your-client-secret",
  "SPOTIPY_REDIRECT_URI": "your-redirect-uri"
}'

# Restart App Runner service to pick up new secrets
aws apprunner start-deployment --service-arn "your-service-arn"
```

## Cleanup

To remove all AWS resources:

```powershell
# Delete App Runner service
aws apprunner delete-service --service-arn "your-service-arn"

# Delete IAM role
aws iam delete-role-policy --role-name "AppRunnerInstanceRole-{service-name}" --policy-name "SecretsManagerAccess-{service-name}"
aws iam delete-role --role-name "AppRunnerInstanceRole-{service-name}"

# Delete secret
aws secretsmanager delete-secret --secret-id "spotify-listener-extract/{service-name}" --force-delete-without-recovery
```

## Cost Considerations

- App Runner: ~$5-15/month for light usage
- Secrets Manager: ~$0.40/month per secret
- Data transfer: Typically minimal for this app

The total cost should be under $20/month for typical usage.
