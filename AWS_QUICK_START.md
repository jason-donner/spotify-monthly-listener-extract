# 🚀 AWS Quick Start - 10 Minutes to Live App

## Prerequisites
- ✅ AWS Account
- ✅ GitHub repository with your code
- ✅ Spotify Developer App

## Step 1: Run Deployment Script (2 minutes)

### Windows:
```powershell
# Navigate to your project directory first
cd "C:\Users\Jason\Spotify Monthly Listener Extract"
cd aws
.\deploy-apprunner.ps1
```

**Or in one command:**
```powershell
cd "C:\Users\Jason\Spotify Monthly Listener Extract\aws"
.\deploy-apprunner.ps1
```

### Mac/Linux:
```bash
cd aws
chmod +x deploy-apprunner.sh
./deploy-apprunner.sh
```

The script will:
- ✅ Check AWS CLI configuration
- ✅ Generate secure Flask secret key
- ✅ Collect your Spotify credentials
- ✅ Provide exact AWS Console steps
- ✅ Save configuration for future reference

## Step 2: AWS Console Setup (5 minutes)

1. **Go to**: [AWS App Runner Console](https://console.aws.amazon.com/apprunner/)
2. **Click**: "Create service"
3. **Select**: Source code repository → GitHub
4. **Repository**: Your GitHub repo URL
5. **Branch**: main
6. **Configuration**: Use configuration file (apprunner.yaml)
7. **Service name**: Use the name from the script
8. **Environment variables**: Copy from script output
9. **Click**: "Create & deploy"

## Step 3: Spotify Setup (2 minutes)

1. **Go to**: [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. **Select**: Your app
3. **Edit Settings** → Redirect URIs
4. **Add**: The redirect URI from the script
5. **Save**

## Step 4: Test Your App (1 minute)

1. **Public app**: `https://your-service-name.region.awsapprunner.com`
2. **Admin login**: `https://your-service-name.region.awsapprunner.com/admin_login`
3. **Test suggestion**: Submit an artist from the public interface
4. **Test admin**: Login and approve the suggestion

## 🎉 You're Live!

Your Spotify Monthly Listener Extract app is now:
- ✅ **Publicly accessible** for users to search and suggest artists
- ✅ **Securely managed** through your admin panel
- ✅ **Auto-scaling** to handle traffic
- ✅ **Monitored** through CloudWatch
- ✅ **HTTPS secured** with automatic certificates

## 💰 Monthly Cost
- **~$46/month** for 1 vCPU, 2GB RAM
- **First month often free** with AWS credits
- **Scales with usage** - pay only for what you use

## 🛠️ Next Steps
- **Custom domain**: Add your own domain in CloudFront
- **Monitoring**: Set up CloudWatch alarms
- **Backups**: Configure S3 data backups
- **Scaling**: Upgrade resources as needed

**Need help?** Check `AWS_DEPLOYMENT_GUIDE.md` for detailed guides on all AWS options!
