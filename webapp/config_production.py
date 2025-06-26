"""
Production Configuration for Deployment
Handles environment-specific settings for public deployment
"""
import os
from dotenv import load_dotenv

# Load environment variables (for local development)
# In production, these will be set in the hosting platform
load_dotenv()

class ProductionConfig:
    """Production configuration with security-focused defaults"""
    
    # Flask Core Settings
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'your-production-secret-key-change-me'
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    TESTING = False
    
    # Admin Authentication
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'changeme'
    
    # Spotify API Settings
    SPOTIPY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
    SPOTIPY_REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI', 'http://localhost:5000/admin/callback')
    
    # ChromeDriver Settings (for scraping)
    CHROMEDRIVER_PATH = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob:;"
    }
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'true').lower() == 'true'

# Default production configuration
Config = ProductionConfig
