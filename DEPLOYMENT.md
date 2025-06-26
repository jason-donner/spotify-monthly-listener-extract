# 🚀 Deploy Your Spotify Monthly Listener Extract App

## Quick Deployment Options

### � Option 1: AWS App Runner (Recommended - Enterprise Grade)

AWS App Runner provides the best balance of simplicity, performance, and scalability:

#### Why AWS App Runner?
- **🚀 Simple Deployment**: Deploy directly from GitHub with zero configuration
- **🏢 Enterprise-grade**: Built on AWS infrastructure with 99.9% uptime
- **💰 Cost-effective**: ~$46/month for 1 vCPU, 2GB RAM
- **🔄 Auto-scaling**: Automatically handles traffic spikes
- **🔐 Built-in security**: HTTPS, VPC, IAM integration
- **📊 Monitoring**: CloudWatch integration for logs and metrics

#### Quick Deploy Steps:
1. **Run the deployment script**:
   ```powershell
   # For Windows
   .\aws\deploy-apprunner.ps1
   
   # For Mac/Linux  
   ./aws/deploy-apprunner.sh
   ```
2. **Follow the AWS Console setup** (script provides exact steps)
3. **Update Spotify Developer App** with the provided redirect URI
4. **Your app is live!** 🎉

**📖 Full AWS Guide**: See `AWS_DEPLOYMENT_GUIDE.md` for detailed options including ECS, Lambda, and Elastic Beanstalk.

---

### 🎯 Option 2: Railway (Simple & Fast)

### 🎯 Option 2: Railway (Simple & Fast)

Railway is perfect for quick deployments with minimal setup:

#### Steps:
1. **Create Railway Account**: Visit [railway.app](https://railway.app) and sign up
2. **Connect GitHub**: Link your GitHub account to Railway
3. **Deploy from GitHub**: 
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects it's a Python app
4. **Set Environment Variables** in Railway dashboard:
   ```
   FLASK_SECRET_KEY=your-super-secret-key-here
   ADMIN_PASSWORD=your-admin-password
   SPOTIPY_CLIENT_ID=your-spotify-client-id
   SPOTIPY_CLIENT_SECRET=your-spotify-client-secret
   SPOTIPY_REDIRECT_URI=https://your-app-name.railway.app/admin/callback
   PORT=8080
   ```
5. **Deploy**: Railway automatically deploys and gives you a public URL

#### 💰 Cost: Free tier with 512MB RAM, $5/month for 1GB+

---

### 🔧 Option 2: Heroku (Reliable but Paid)

#### Steps:
1. **Install Heroku CLI**: Download from [heroku.com](https://heroku.com)
2. **Login**: `heroku login`
3. **Create app**: `heroku create your-app-name`
4. **Set environment variables**:
   ```bash
   heroku config:set FLASK_SECRET_KEY=your-secret-key
   heroku config:set ADMIN_PASSWORD=your-admin-password
   heroku config:set SPOTIPY_CLIENT_ID=your-spotify-client-id
   heroku config:set SPOTIPY_CLIENT_SECRET=your-spotify-client-secret
   heroku config:set SPOTIPY_REDIRECT_URI=https://your-app-name.herokuapp.com/admin/callback
   ```
5. **Deploy**: `git push heroku main`

#### 💰 Cost: $7/month minimum (no free tier)

---

### 🐳 Option 3: Docker (Any Platform)

I've included Docker support for maximum flexibility:

#### Steps:
1. **Build**: `docker build -t spotify-tracker .`
2. **Run**: `docker run -p 8080:8080 --env-file .env spotify-tracker`
3. **Deploy** to any Docker-compatible platform:
   - **DigitalOcean App Platform** ($5/month)
   - **Google Cloud Run** (pay-per-use)
   - **AWS ECS/Fargate** (variable pricing)

---

## 🔐 Security Checklist

Before going live, ensure:

- [ ] **Change default admin password** in environment variables
- [ ] **Generate new Flask secret key**: 
  ```python
  import secrets
  print(secrets.token_hex(32))
  ```
- [ ] **Set up Spotify app** in [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
- [ ] **Update redirect URI** to your deployed domain
- [ ] **Enable HTTPS** (most platforms do this automatically)

---

## 🎵 Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create a new app
3. Add your deployment URL + `/admin/callback` to redirect URIs:
   - `https://your-app-name.railway.app/admin/callback`
   - `https://your-app-name.herokuapp.com/admin/callback`
4. Copy Client ID and Client Secret to environment variables

---

## 🌐 Custom Domain (Optional)

Most platforms support custom domains:

### Railway:
- Go to project settings → Custom Domain
- Add your domain (e.g., `spotifytracker.yourdomain.com`)
- Update DNS records as instructed

### Heroku:
- `heroku domains:add yourdomain.com`
- Update DNS to point to Heroku

---

## 📊 Monitoring & Maintenance

After deployment:

1. **Monitor logs** through your platform's dashboard
2. **Set up alerts** for errors or downtime
3. **Regular backups** of your data files
4. **Update dependencies** monthly for security

---

## 🚀 Go Live!

Choose your platform and follow the steps above. Your Spotify Monthly Listener Extract app will be publicly accessible with:

- 🔍 **Public search** for artists and monthly listeners
- 💡 **Suggestion system** for users to recommend new artists
- 🔐 **Secure admin panel** for managing data and scraping
- 📊 **Beautiful leaderboards** and analytics
- 🎵 **Spotify integration** for automatic following

**Need help?** All platforms have excellent documentation and support!
