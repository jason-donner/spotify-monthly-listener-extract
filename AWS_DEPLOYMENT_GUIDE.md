# 🚀 AWS Deployment Guide - Spotify Monthly Listener Extract

## Why AWS?
- **Enterprise-grade reliability** and scalability
- **Multiple deployment options** to fit your needs
- **Cost-effective** with fine-grained pricing control
- **Global infrastructure** for fast worldwide access
- **Comprehensive monitoring** and logging

---

## 🎯 Recommended AWS Deployment Options

### Option 1: AWS App Runner (Easiest - Recommended)
**Perfect for**: Quick deployment with minimal configuration
**Cost**: ~$25-50/month for typical usage
**Pros**: Automatic scaling, built-in load balancing, minimal setup

### Option 2: AWS Elastic Beanstalk (Balanced)
**Perfect for**: More control while staying simple
**Cost**: ~$15-30/month + EC2 costs
**Pros**: Easy deployment, environment management, auto-scaling

### Option 3: Amazon ECS with Fargate (Most Scalable)
**Perfect for**: Production workloads needing maximum control
**Cost**: ~$20-40/month + storage
**Pros**: Containerized, serverless compute, enterprise features

### Option 4: AWS Lambda + API Gateway (Serverless)
**Perfect for**: Cost optimization for low-traffic apps
**Cost**: ~$5-15/month for moderate usage
**Pros**: Pay-per-request, automatic scaling, zero maintenance

---

## 🏆 Option 1: AWS App Runner (Recommended)

AWS App Runner is perfect for your Flask app - it's like Heroku but on AWS infrastructure.

### Prerequisites
- AWS Account
- GitHub repository (your current setup)
- Docker support (already configured)

### Step-by-Step Deployment

#### 1. Prepare Your Repository
Your app is already App Runner ready! The `Dockerfile` I created will work perfectly.

#### 2. Create App Runner Service
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure
```

#### 3. Create `apprunner.yaml` Configuration
```yaml
version: 1.0
runtime: docker
build:
  commands:
    build:
      - echo "Building Docker image..."
run:
  runtime-version: latest
  command: gunicorn app:app --workers 2 --threads 2 --timeout 60 --bind 0.0.0.0:8080
  network:
    port: 8080
    env:
      - FLASK_SECRET_KEY
      - ADMIN_PASSWORD  
      - SPOTIPY_CLIENT_ID
      - SPOTIPY_CLIENT_SECRET
      - SPOTIPY_REDIRECT_URI
      - PORT=8080
```

#### 4. Deploy via AWS Console
1. Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner/)
2. Click "Create service"
3. **Source**: GitHub repository
4. **Repository**: Select your Spotify tracker repo
5. **Branch**: main/master
6. **Build settings**: Use `apprunner.yaml`
7. **Service settings**:
   - Service name: `spotify-monthly-tracker`
   - CPU: 1 vCPU
   - Memory: 2 GB
8. **Environment variables**: Add all required vars
9. **Auto-deployment**: Enable for automatic updates

#### 5. Configure Environment Variables
In the App Runner console, add:
```
FLASK_SECRET_KEY=<your-64-char-secret>
ADMIN_PASSWORD=<your-secure-password>
SPOTIPY_CLIENT_ID=<spotify-client-id>
SPOTIPY_CLIENT_SECRET=<spotify-client-secret>
SPOTIPY_REDIRECT_URI=https://your-service-name.region.awsapprunner.com/admin/callback
PORT=8080
FLASK_DEBUG=false
LOG_LEVEL=INFO
```

#### 6. Deploy and Test
- App Runner will build and deploy automatically
- You'll get a URL like: `https://abc123.us-east-1.awsapprunner.com`
- Test your deployment!

### 💰 App Runner Pricing
- **$0.064/hour** for 1 vCPU, 2GB RAM (~$46/month)
- **$0.025/GB** for data transfer
- **No charge** when not processing requests (scales to zero)

---

## 🛠️ Option 2: AWS Elastic Beanstalk

Great for more control while keeping deployment simple.

### Step-by-Step Deployment

#### 1. Install EB CLI
```bash
pip install awsebcli
```

#### 2. Initialize Beanstalk Application
```bash
cd webapp
eb init spotify-tracker --platform python-3.11 --region us-east-1
```

#### 3. Create Environment Configuration
Create `webapp/.ebextensions/01_flask.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app:app
  aws:elasticbeanstalk:application:environment:
    FLASK_SECRET_KEY: "your-secret-key-here"
    ADMIN_PASSWORD: "your-admin-password"
    SPOTIPY_CLIENT_ID: "your-spotify-client-id"
    SPOTIPY_CLIENT_SECRET: "your-spotify-client-secret"
    FLASK_DEBUG: "false"
  aws:autoscaling:launchconfig:
    InstanceType: t3.micro
  aws:elasticbeanstalk:command:
    BatchSize: 30
    BatchSizeType: Percentage
```

#### 4. Deploy
```bash
eb create spotify-tracker-prod --instance-type t3.micro
eb open
```

### 💰 Elastic Beanstalk Pricing
- **t3.micro**: ~$8/month (free tier eligible)
- **t3.small**: ~$17/month
- **Load balancer**: ~$18/month (optional)

---

## 🐳 Option 3: Amazon ECS with Fargate

For production-grade containerized deployment.

### Step-by-Step Deployment

#### 1. Create ECS Cluster
```bash
aws ecs create-cluster --cluster-name spotify-tracker-cluster
```

#### 2. Create Task Definition
```json
{
  "family": "spotify-tracker",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "spotify-tracker",
      "image": "your-account.dkr.ecr.region.amazonaws.com/spotify-tracker:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "FLASK_SECRET_KEY", "value": "your-secret-key"},
        {"name": "ADMIN_PASSWORD", "value": "your-password"},
        {"name": "SPOTIPY_CLIENT_ID", "value": "your-client-id"},
        {"name": "SPOTIPY_CLIENT_SECRET", "value": "your-client-secret"},
        {"name": "PORT", "value": "8080"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/spotify-tracker",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### 3. Create ECS Service with Application Load Balancer
```bash
aws ecs create-service \
  --cluster spotify-tracker-cluster \
  --service-name spotify-tracker-service \
  --task-definition spotify-tracker \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

### 💰 ECS Fargate Pricing
- **0.5 vCPU, 1GB RAM**: ~$15/month
- **1 vCPU, 2GB RAM**: ~$30/month
- **Load balancer**: ~$18/month

---

## ⚡ Option 4: AWS Lambda (Serverless)

For cost-effective serverless deployment.

### Using Zappa for Lambda Deployment

#### 1. Install Zappa
```bash
pip install zappa
```

#### 2. Configure Zappa
Create `webapp/zappa_settings.json`:
```json
{
  "production": {
    "app_function": "app.app",
    "aws_region": "us-east-1",
    "profile_name": "default",
    "project_name": "spotify-tracker",
    "runtime": "python3.11",
    "s3_bucket": "spotify-tracker-zappa-deployments",
    "timeout_seconds": 900,
    "memory_size": 1024,
    "environment_variables": {
      "FLASK_SECRET_KEY": "your-secret-key",
      "ADMIN_PASSWORD": "your-password",
      "SPOTIPY_CLIENT_ID": "your-client-id",
      "SPOTIPY_CLIENT_SECRET": "your-client-secret"
    }
  }
}
```

#### 3. Deploy
```bash
cd webapp
zappa deploy production
zappa update production  # for updates
```

### 💰 Lambda Pricing
- **1M requests/month**: $0.20
- **Memory/compute**: ~$5-15/month typical usage
- **Very cost-effective** for moderate traffic

---

## 🔧 AWS Infrastructure Setup Scripts

Let me create automated setup scripts for you:

### CloudFormation Template
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Spotify Monthly Listener Extract - Complete Infrastructure'

Parameters:
  AppName:
    Type: String
    Default: spotify-tracker
  Environment:
    Type: String
    Default: production

Resources:
  # App Runner Service
  AppRunnerService:
    Type: AWS::AppRunner::Service
    Properties:
      ServiceName: !Sub '${AppName}-${Environment}'
      SourceConfiguration:
        ImageRepository:
          ImageIdentifier: 'public.ecr.aws/docker/library/python:3.11-slim'
          ImageConfiguration:
            Port: '8080'
        AutoDeploymentsEnabled: true
      InstanceConfiguration:
        Cpu: '1 vCPU'
        Memory: '2 GB'

  # CloudWatch Log Group
  LogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/apprunner/${AppName}-${Environment}'
      RetentionInDays: 30

Outputs:
  ServiceUrl:
    Description: 'App Runner Service URL'
    Value: !GetAtt AppRunnerService.ServiceUrl
```

---

## 🌐 Custom Domain Setup

### Using Route 53 + CloudFront
1. **Register domain** in Route 53 (or use existing)
2. **Create CloudFront distribution** pointing to your App Runner URL
3. **Add SSL certificate** via AWS Certificate Manager (free)
4. **Update Spotify redirect URI** to your custom domain

### DNS Configuration
```bash
# Create hosted zone
aws route53 create-hosted-zone --name your-domain.com --caller-reference unique-ref

# Add CNAME record pointing to CloudFront
aws route53 change-resource-record-sets --hosted-zone-id Z123456789 --change-batch file://dns-records.json
```

---

## 📊 Monitoring & Logging

### CloudWatch Setup
- **Application logs**: Automatic with App Runner/Beanstalk
- **Custom metrics**: Track suggestion submissions, admin logins
- **Alarms**: Set up alerts for errors or high traffic
- **Dashboards**: Monitor app performance

### X-Ray Tracing (Optional)
Add request tracing for performance insights:
```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Add to your Flask app
patch_all()
```

---

## 💾 Data Persistence

### Option 1: EFS (Shared File System)
- Mount EFS volume to store JSON data files
- Persistent across container restarts
- ~$0.30/GB/month

### Option 2: S3 + Local Cache
- Store master data in S3
- Cache locally for fast access
- Very cost-effective

### Option 3: Amazon RDS (Future Migration)
- Eventually migrate from JSON to PostgreSQL
- Better for larger datasets
- Built-in backups and scaling

---

## 🚀 Quick Start: App Runner Deployment

Here's the fastest way to get your app live on AWS:

1. **Push your code** to GitHub (already done!)
2. **Go to AWS App Runner console**
3. **Create service** from GitHub
4. **Add environment variables**
5. **Deploy and test!**

Your app will be live at a AWS URL in ~10 minutes!

---

## 💰 Cost Comparison Summary

| Option | Monthly Cost | Best For |
|--------|-------------|----------|
| **App Runner** | $46-70 | Easiest deployment |
| **Elastic Beanstalk** | $25-45 | Balanced control/ease |
| **ECS Fargate** | $33-65 | Production workloads |
| **Lambda** | $5-20 | Cost optimization |

**Recommendation**: Start with **App Runner** for simplicity, then migrate to ECS if you need more control later.

Ready to deploy? Let's start with App Runner! 🚀
