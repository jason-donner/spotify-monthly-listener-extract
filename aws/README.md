# 🚀 AWS Deployment Files

This directory contains everything you need to deploy your Spotify Monthly Listener Extract app to AWS.

## 🎯 Quick Start

### Option 1: Interactive Setup (Recommended)
Run the interactive deployment script:

**Windows:**
```powershell
.\deploy-apprunner.ps1
```

**Mac/Linux:**
```bash
chmod +x deploy-apprunner.sh
./deploy-apprunner.sh
```

The script will:
- ✅ Check your AWS setup
- ✅ Generate secure credentials
- ✅ Provide step-by-step AWS Console instructions
- ✅ Create Spotify redirect URIs
- ✅ Save configuration for future reference

### Option 2: Manual Setup
If you prefer manual configuration, follow the detailed guides:
- `../AWS_DEPLOYMENT_GUIDE.md` - Complete deployment options
- `../AWS_QUICK_START.md` - 10-minute quick start

## 📁 Files in this Directory

### Deployment Scripts
- `deploy-apprunner.ps1` - PowerShell deployment script (Windows)
- `deploy-apprunner.sh` - Bash deployment script (Mac/Linux)

### AWS Configuration Files
- `apprunner.yaml` - App Runner service configuration
- `cloudformation-template.yaml` - Full infrastructure as code
- `ecs-task-definition.json` - ECS Fargate deployment config
- `../webapp/.ebextensions/01_flask.config` - Elastic Beanstalk config

## 🎯 Deployment Options

### 1. AWS App Runner (Recommended)
- **Best for**: Quick deployment with minimal configuration
- **Cost**: ~$46/month for 1 vCPU, 2GB RAM
- **Setup**: Use deployment scripts + AWS Console

### 2. AWS Elastic Beanstalk
- **Best for**: More control while staying simple
- **Cost**: ~$25-45/month
- **Setup**: Use EB CLI or AWS Console

### 3. Amazon ECS with Fargate
- **Best for**: Production workloads needing maximum control
- **Cost**: ~$33-65/month
- **Setup**: Use CloudFormation template or ECS CLI

### 4. AWS Lambda (Serverless)
- **Best for**: Cost optimization for low-traffic apps
- **Cost**: ~$5-20/month
- **Setup**: Use Zappa or AWS SAM

## 🔐 Security Features

All deployment options include:
- ✅ **Secrets Manager** for secure credential storage
- ✅ **IAM roles** with least privilege access
- ✅ **VPC networking** for network isolation
- ✅ **HTTPS encryption** with automatic certificates
- ✅ **CloudWatch logging** for monitoring
- ✅ **Auto-scaling** for traffic handling

## 💰 Cost Comparison

| Service | Monthly Cost | Best For |
|---------|-------------|----------|
| **App Runner** | $46-70 | Simplicity + performance |
| **Elastic Beanstalk** | $25-45 | Balanced control |
| **ECS Fargate** | $33-65 | Production workloads |
| **Lambda** | $5-20 | Cost optimization |

## 🚀 After Deployment

Once deployed, your app provides:

### Public Features (No Login Required)
- 🔍 **Search artists** and view monthly listener data
- 📊 **Browse leaderboards** with current month focus
- 🎵 **Preview top tracks** for each artist
- 💡 **Suggest new artists** for tracking

### Admin Features (Password Protected)
- 👨‍💼 **Review suggestions** with approve/reject workflow
- 🎵 **Auto-follow artists** on Spotify
- 🤖 **Run data scraping** with real-time progress
- 📊 **Monitor system** performance and logs

## 🆘 Need Help?

1. **Quick issues**: Check `../AWS_QUICK_START.md`
2. **Detailed setup**: See `../AWS_DEPLOYMENT_GUIDE.md`
3. **General deployment**: Reference `../DEPLOYMENT.md`
4. **Security checklist**: Review `../SECURITY_CHECKLIST.md`

**Ready to deploy?** Run the deployment script and follow the instructions! 🎉
