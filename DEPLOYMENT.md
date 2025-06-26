# 🚀 Deploy Your Spotify Monthly Listener Extract App

## 🎯 AWS App Runner Deployment (Recommended)

AWS App Runner provides enterprise-grade hosting with secure secret management:

### Why AWS App Runner?
- **🚀 Simple Deployment**: Deploy directly from GitHub with zero configuration
- **🏢 Enterprise-grade**: Built on AWS infrastructure with 99.9% uptime
- **💰 Cost-effective**: ~$6-16/month for typical usage
- **🔄 Auto-scaling**: Automatically handles traffic spikes
- **🔐 Built-in security**: HTTPS, VPC, IAM integration, AWS Secrets Manager
- **📊 Monitoring**: CloudWatch integration for logs and metrics

### Quick Deploy Steps:

#### 1. Run the Secure Deployment Script
```powershell
cd "C:\Users\Jason\Spotify Monthly Listener Extract\aws"
.\deploy-apprunner.ps1
```

This script:
- ✅ Creates secrets in AWS Secrets Manager
- ✅ Generates IAM roles with proper permissions
- ✅ Provides step-by-step deployment instructions
- ✅ Ensures no sensitive data is exposed

#### 2. Create App Runner Service
1. Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner/)
2. Follow the generated instructions from the script
3. Use the secure IAM role created by the script

#### 3. Configure Spotify OAuth
Update your Spotify Developer App with the redirect URI provided by the script.

#### 4. Your App is Live! 🎉

**📖 Detailed Guide**: See `AWS_QUICK_START.md` for complete instructions.

---

## 🔧 Alternative: Docker Deployment

For other platforms, use the included Dockerfile:

### Supported Platforms:
- **DigitalOcean App Platform** (~$5/month)
- **Google Cloud Run** (pay-per-use)
- **AWS ECS/Fargate** (variable pricing)
- **Azure Container Instances** (pay-per-use)

### Steps:
1. **Build**: `docker build -t spotify-tracker .`
2. **Run locally**: `docker run -p 8080:8080 --env-file .env spotify-tracker`
3. **Deploy** to your chosen platform

---

## 🔐 Security Features

### AWS Secrets Manager Integration
- All sensitive credentials stored securely in AWS
- Application loads secrets at runtime
- Zero sensitive data in repository
- Automatic encryption at rest and in transit

### IAM Best Practices
- Least-privilege access permissions
- Service-specific roles
- No hardcoded credentials

### Production Security Checklist
- [ ] **Secrets in AWS Secrets Manager** (handled by deployment script)
- [ ] **Unique service names** (auto-generated)
- [ ] **HTTPS enabled** (automatic with App Runner)
- [ ] **Spotify OAuth configured** with correct redirect URI
- [ ] **IAM roles properly configured** (handled by script)

---

## 🎵 Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create a new app
3. Add your deployment URL + `/admin/callback` to redirect URIs:
   - Example: `https://spotify-listener-extract-7342.us-east-1.awsapprunner.com/admin/callback`
4. Client ID and Secret are handled securely by the deployment script

---

## 📊 Monitoring & Management

### AWS CloudWatch Integration
- **Application logs** automatically sent to CloudWatch
- **Metrics** for performance monitoring
- **Alarms** can be set up for error rates or response times

### Updating Secrets
```powershell
# Update any secret value
aws secretsmanager update-secret --secret-id "spotify-listener-extract/{service-name}" --secret-string '{...}'

# Restart service to pick up changes
aws apprunner start-deployment --service-arn "{your-service-arn}"
```

### Health Monitoring
- Built-in health checks in App Runner
- Automatic restart on failures
- Load balancing across instances

---

## � Cost Breakdown

### AWS App Runner
- **Base cost**: ~$5-15/month for light usage
- **Secrets Manager**: ~$0.40/month per secret
- **Data transfer**: Minimal for typical usage
- **Total**: ~$6-16/month

### Scaling Costs
- Automatically scales based on traffic
- Pay only for what you use
- No upfront costs or commitments

---

## 🚀 Go Live!

Your deployed Spotify Monthly Listener Extract app includes:

- 🔍 **Public search** for artists and monthly listeners
- 💡 **Suggestion system** for users to recommend new artists
- 🔐 **Secure admin panel** for managing data and scraping
- 📊 **Beautiful leaderboards** and analytics
- 🎵 **Spotify integration** for automatic following
- 🔒 **Enterprise-grade security** with AWS Secrets Manager

**Ready to deploy?** Run the deployment script and follow the generated instructions!

**Need help?** Check `AWS_QUICK_START.md` for step-by-step guidance.
