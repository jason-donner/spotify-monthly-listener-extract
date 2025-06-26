# Public Deployment Guide

## Overview

This guide covers deploying the Spotify Monthly Listener Extract app publicly while maintaining security and functionality. The deployment will allow users to search artists and submit suggestions while keeping admin functionality secure.

---

## 🚀 Deployment Options

### Option 1: Railway (Recommended)
**Pros**: Easy setup, automatic deployments, good free tier
**Cost**: Free tier available, then $5/month
**Best for**: Quick deployment with minimal configuration

### Option 2: Heroku
**Pros**: Well-documented, many tutorials available
**Cost**: $7/month minimum (no free tier anymore)
**Best for**: Established deployment platform

### Option 3: DigitalOcean App Platform
**Pros**: Good performance, reasonable pricing
**Cost**: $5/month minimum
**Best for**: More control and better performance

### Option 4: AWS/GCP/Azure
**Pros**: Enterprise-grade, highly scalable
**Cost**: Variable, can be complex
**Best for**: Large scale deployments

---

## 🔧 Pre-Deployment Setup

### 1. Production Configuration

Create `webapp/config_production.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

class ProductionConfig:
    # Flask settings
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'your-production-secret-key'
    DEBUG = False
    TESTING = False
    
    # Admin settings
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    
    # Spotify API settings
    SPOTIFY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
    SPOTIFY_REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI')
    
    # Production-specific settings
    FORCE_HTTPS = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Logging
    LOG_LEVEL = "INFO"
```

### 2. Update Main App for Production

Modify `webapp/app.py` to support production config:
```python
import os
from flask import Flask
from dotenv import load_dotenv

def create_app(config_name=None):
    load_dotenv()
    
    app = Flask(__name__)
    
    # Determine configuration
    if config_name == 'production' or os.environ.get('FLASK_ENV') == 'production':
        from config_production import ProductionConfig
        app.config.from_object(ProductionConfig)
    else:
        from app.config import Config
        app.config.from_object(Config)
    
    # Initialize components...
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))
```

### 3. Create Production Requirements

Create `webapp/requirements_production.txt`:
```txt
# All existing requirements from requirements.txt
flask==2.3.3
spotipy==2.22.1
python-dotenv==1.0.0
requests==2.31.0
flask-cors==4.0.0

# Production-specific additions
gunicorn==21.2.0
flask-limiter==3.5.0
flask-talisman==1.1.0
```

### 4. Security Enhancements

Create `webapp/security.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

def configure_security(app):
    """Configure security settings for production"""
    
    # Rate limiting
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Apply rate limits to specific endpoints
    @limiter.limit("10 per minute")
    def limit_suggestions():
        pass
    
    # Security headers
    Talisman(app, {
        'force_https': app.config.get('FORCE_HTTPS', False),
        'strict_transport_security': True,
        'content_security_policy': {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com",
            'style-src': "'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com",
            'img-src': "'self' data: i.scdn.co",
            'connect-src': "'self' api.spotify.com"
        }
    })
    
    return limiter
```

---

## 🔒 Security Considerations

### 1. Environment Variables for Production

You'll need these environment variables in production:
```env
# Required
FLASK_SECRET_KEY=your-very-secure-random-secret-key
ADMIN_PASSWORD=your-very-secure-admin-password
SPOTIPY_CLIENT_ID=your-spotify-client-id
SPOTIPY_CLIENT_SECRET=your-spotify-client-secret
SPOTIPY_REDIRECT_URI=https://yourdomain.com/admin/callback

# Optional
FLASK_ENV=production
PORT=5000
```

### 2. Spotify App Configuration

Update your Spotify Developer App settings:
1. **Redirect URIs**: Add your production domain
   - `https://yourdomain.com/admin/callback`
   - Keep localhost for development: `http://127.0.0.1:5000/admin/callback`

2. **App Description**: Update for public use

3. **Website**: Add your production URL

### 3. Admin Access Security

Create `webapp/admin_security.py`:
```python
import os
import hashlib
from functools import wraps
from flask import request, abort

def secure_admin_access():
    """Enhanced admin security for production"""
    
    # IP whitelist (optional)
    ALLOWED_ADMIN_IPS = os.environ.get('ADMIN_IP_WHITELIST', '').split(',')
    
    def check_admin_ip(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if ALLOWED_ADMIN_IPS and ALLOWED_ADMIN_IPS[0]:  # If whitelist is configured
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                if client_ip not in ALLOWED_ADMIN_IPS:
                    abort(403)  # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    
    return check_admin_ip
```

---

## 📦 Deployment Files

### 1. Railway Deployment

Create `railway.toml`:
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "cd webapp && gunicorn --bind 0.0.0.0:$PORT app:app"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### 2. Heroku Deployment

Create `Procfile` in the root directory:
```
web: cd webapp && gunicorn --bind 0.0.0.0:$PORT app:app
```

Create `runtime.txt`:
```
python-3.11.5
```

### 3. Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY webapp/requirements_production.txt .
RUN pip install --no-cache-dir -r requirements_production.txt

# Copy application code
COPY webapp/ ./webapp/
COPY data/ ./data/
COPY scraping/ ./scraping/

WORKDIR /app/webapp

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - SPOTIPY_CLIENT_ID=${SPOTIPY_CLIENT_ID}
      - SPOTIPY_CLIENT_SECRET=${SPOTIPY_CLIENT_SECRET}
      - SPOTIPY_REDIRECT_URI=${SPOTIPY_REDIRECT_URI}
    volumes:
      - ./data:/app/data
```

---

## 🚀 Step-by-Step Deployment (Railway)

### 1. Prepare Your Repository

```bash
# Commit all changes
git add .
git commit -m "Prepare for production deployment"
git push origin main
```

### 2. Deploy to Railway

1. **Sign up at Railway.app**
2. **Connect GitHub repository**
3. **Set environment variables**:
   - `FLASK_SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
   - `ADMIN_PASSWORD`: Your secure admin password
   - `SPOTIPY_CLIENT_ID`: From Spotify Developer Dashboard
   - `SPOTIPY_CLIENT_SECRET`: From Spotify Developer Dashboard
   - `SPOTIPY_REDIRECT_URI`: `https://your-app-name.railway.app/admin/callback`
   - `FLASK_ENV`: `production`

4. **Deploy**: Railway will automatically build and deploy

### 3. Update Spotify App Settings

1. Go to Spotify Developer Dashboard
2. Edit your app settings
3. Add redirect URI: `https://your-app-name.railway.app/admin/callback`

### 4. Test Deployment

1. Visit your Railway app URL
2. Test public features (search, suggest artists)
3. Test admin login at `/admin_login`

---

## 🔧 Production Optimizations

### 1. Database Migration (Optional)

For high traffic, consider migrating from JSON to a proper database:

```python
# Example with SQLite (simple) or PostgreSQL (production)
import sqlite3
import json

def migrate_to_database():
    # Create tables
    conn = sqlite3.connect('spotify_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artists (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT,
            date_added DATE,
            removed BOOLEAN DEFAULT FALSE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_listeners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist_id TEXT,
            date DATE,
            listeners INTEGER,
            FOREIGN KEY (artist_id) REFERENCES artists (id),
            UNIQUE(artist_id, date)
        )
    ''')
    
    # Migrate existing JSON data
    # ... migration logic ...
    
    conn.commit()
    conn.close()
```

### 2. Caching Layer

Add Redis caching for better performance:

```python
import redis
from functools import wraps
import json

redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))

def cache_result(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f"{f.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Generate result and cache it
            result = f(*args, **kwargs)
            redis_client.setex(cache_key, timeout, json.dumps(result))
            return result
        return decorated_function
    return decorator
```

### 3. Content Delivery Network (CDN)

For static assets, consider using a CDN:
- Cloudflare (free tier available)
- AWS CloudFront
- Google Cloud CDN

---

## 📊 Monitoring and Analytics

### 1. Application Monitoring

Add basic monitoring:

```python
import logging
from datetime import datetime

def setup_production_logging(app):
    if not app.debug:
        # File logging
        file_handler = logging.FileHandler('logs/production.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Spotify Listener Tracker startup')

# Add to your app creation
@app.before_request
def log_request_info():
    app.logger.info('Request: %s %s', request.method, request.url)

@app.after_request
def log_response_info(response):
    app.logger.info('Response: %s', response.status_code)
    return response
```

### 2. Simple Analytics

Track usage without compromising privacy:

```python
from collections import defaultdict
import json
from datetime import datetime, date

class SimpleAnalytics:
    def __init__(self, app):
        self.app = app
        self.stats = defaultdict(int)
        
    def track_event(self, event_name):
        today = date.today().isoformat()
        key = f"{today}:{event_name}"
        self.stats[key] += 1
        
    def get_daily_stats(self):
        return dict(self.stats)

# Usage
analytics = SimpleAnalytics(app)

@app.route('/suggest_artist', methods=['POST'])
def suggest_artist():
    analytics.track_event('artist_suggestion')
    # ... rest of the function
```

---

## 🔄 Continuous Deployment

### 1. GitHub Actions (Free)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Use Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        
    - name: Install Railway CLI
      run: npm install -g @railway/cli
      
    - name: Deploy to Railway
      run: railway up --service your-service-name
      env:
        RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### 2. Automated Testing

Create `tests/test_public_endpoints.py`:

```python
import pytest
from webapp.app import create_app

@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        yield client

def test_home_page(client):
    rv = client.get('/')
    assert rv.status_code == 200

def test_search_page(client):
    rv = client.get('/search')
    assert rv.status_code == 200

def test_suggest_artist_get(client):
    rv = client.get('/suggest_artist')
    assert rv.status_code in [200, 405]  # GET might not be allowed

def test_admin_requires_auth(client):
    rv = client.get('/admin')
    assert rv.status_code == 302  # Redirect to login
```

---

## 📋 Pre-Launch Checklist

### Security
- [ ] Admin password is strong and unique
- [ ] All environment variables are set correctly
- [ ] HTTPS is enforced
- [ ] Rate limiting is configured
- [ ] Security headers are enabled
- [ ] IP whitelist for admin (optional)

### Functionality
- [ ] Public pages load correctly
- [ ] Search functionality works
- [ ] Artist suggestion form works
- [ ] Admin panel is accessible and secure
- [ ] Spotify OAuth works with production URLs

### Performance
- [ ] Static files are served efficiently
- [ ] Database queries are optimized
- [ ] Caching is configured (if applicable)
- [ ] Logging is set up correctly

### Monitoring
- [ ] Error tracking is configured
- [ ] Performance monitoring is set up
- [ ] Backup strategy is in place
- [ ] Update process is documented

---

## 🚨 Common Issues and Solutions

### Issue: "Internal Server Error"
**Solution**: Check application logs for detailed error messages

### Issue: Admin panel not accessible
**Solution**: Verify environment variables and Spotify app configuration

### Issue: Slow performance
**Solution**: Implement caching and consider database migration

### Issue: Rate limiting too strict
**Solution**: Adjust rate limits in security configuration

---

## 💡 Cost Optimization Tips

1. **Start Small**: Use free tiers initially (Railway, Vercel)
2. **Monitor Usage**: Track resource consumption
3. **Optimize Queries**: Minimize database/file operations
4. **Use CDN**: For static assets to reduce server load
5. **Implement Caching**: Reduce repeated calculations

---

## 🎯 Post-Deployment Tasks

1. **Monitor Performance**: Watch response times and error rates
2. **User Feedback**: Set up a way for users to report issues
3. **Regular Backups**: Implement automated data backups
4. **Security Updates**: Keep dependencies updated
5. **Scale Planning**: Plan for increased traffic

This deployment guide provides a solid foundation for making your Spotify Monthly Listener Extract app publicly available while maintaining security and performance!
