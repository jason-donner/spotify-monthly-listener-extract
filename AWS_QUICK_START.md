# AWS App Runner Quick Start - Secure Deployment

Deploy the Spotify Monthly Listener Extract app to AWS App Runner with enterprise-grade security using AWS Secrets Manager.

## Prerequisites

✅ **AWS CLI installed and configured**
```powershell
aws --version
aws configure  # If not already configured
```

✅ **Git repository on GitHub (main branch)**
```powershell
cd "C:\Users\Jason\Spotify Monthly Listener Extract"
git status  # Ensure you're on main branch
git push origin main  # Ensure latest code is pushed
```

✅ **Spotify Developer Account**
- Visit: https://developer.spotify.com/dashboard/
- Create app and note Client ID/Secret

## 🚀 One-Click Secure Deployment

### Step 1: Run Deployment Script
```powershell
cd "C:\Users\Jason\Spotify Monthly Listener Extract\aws"
.\deploy-apprunner.ps1
```

**What this does:**
- ✅ Generates secure Flask secret key
- ✅ Prompts for your credentials (secure input)
- ✅ Creates/updates AWS Secrets Manager secret
- ✅ Creates IAM role with least-privilege permissions
- ✅ Generates deployment configuration
- ✅ No sensitive data touches your repository

### Step 2: Complete App Runner Setup

1. **Open AWS Console**
   - Go to: https://console.aws.amazon.com/apprunner/

2. **Create Service**
   - Click **"Create service"**
   - Source: **Repository**
   - Connect to GitHub
   - Repository: **spotify-monthly-listener-extract**
   - Branch: **main**
   - Configuration: **Use configuration file (apprunner.yaml)**

3. **Security Configuration**
   - Service name: Use name from script output
   - **Instance role**: Select `AppRunnerInstanceRole-{service-name}`
   
4. **Environment Variables** (non-sensitive only):
   ```
   AWS_REGION=us-east-1
   AWS_SECRET_NAME={from-script-output}
   PORT=8080
   FLASK_DEBUG=false
   ```

5. **Deploy**
   - Click **"Create & deploy"**
   - Wait 5-10 minutes for deployment

### Step 3: Configure Spotify OAuth

1. **Get your App Runner URL** from AWS console
2. **Update Spotify App**:
   - Go to: https://developer.spotify.com/dashboard/
   - Select your app → **Edit Settings**
   - Add Redirect URI: `https://{your-url}/admin/callback`

### Step 4: Test Deployment

- **App URL**: `https://{your-service-name}.us-east-1.awsapprunner.com`
- **Admin Login**: `https://{your-service-name}.us-east-1.awsapprunner.com/admin_login`

## 🔒 Security Features

### ✅ AWS Secrets Manager Integration
- Sensitive credentials stored securely in AWS
- Application loads secrets at runtime
- Zero sensitive data in repository
- Automatic encryption at rest and in transit

### ✅ IAM Best Practices
- Least-privilege access (only read specific secret)
- Service-specific roles
- No hardcoded credentials

### ✅ Production Ready
- Proper logging and monitoring
- Scalable architecture
- Health checks included

## 📊 Monitoring & Management

### View Logs
1. AWS App Runner Console → Your Service → **Logs** tab
2. CloudWatch integration for advanced monitoring

### Update Secrets
```powershell
# Update any secret value
aws secretsmanager update-secret --secret-id "spotify-listener-extract/{service-name}" --secret-string '{...}'

# Restart service to pick up changes
aws apprunner start-deployment --service-arn "{your-service-arn}"
```

## 💰 Cost Estimate

- **App Runner**: ~$5-15/month (light usage)
- **Secrets Manager**: ~$0.40/month per secret
- **Total**: ~$6-16/month

## 🆘 Troubleshooting

**Build Issues:**
- Check Dockerfile and requirements.txt
- View build logs in App Runner console

**Secret Access Issues:**
- Verify IAM role is attached
- Check AWS region consistency
- Confirm secret name matches

**Spotify OAuth Issues:**
- Verify exact redirect URI in Spotify app
- Check case sensitivity

## 📚 Full Documentation

For detailed documentation, see: `DEPLOYMENT_GUIDE.md`

---

**Ready to deploy?** Run the script and follow the steps above! 🚀
- **Backups**: Configure S3 data backups
- **Scaling**: Upgrade resources as needed

**Need help?** Check `AWS_DEPLOYMENT_GUIDE.md` for detailed guides on all AWS options!
