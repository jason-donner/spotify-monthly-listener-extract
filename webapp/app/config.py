"""
Configuration module for the Spotify Listener Tracker app.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Spotify API credentials
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:5000/callback")
    SPOTIFY_SCOPE = "user-follow-modify user-follow-read"
    
    # Admin authentication
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'changeme')
    
    # Data file paths - handle both local and production deployments
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    DATA_DIR = os.getenv('DATA_PATH', os.path.join(BASE_DIR, "..", "data", "results"))
    
    DATA_PATH = os.path.join(DATA_DIR, "spotify-monthly-listeners-master.json")
    FOLLOWED_ARTISTS_PATH = os.path.join(DATA_DIR, "spotify-followed-artists-master.json")
    SUGGESTIONS_FILE = os.path.join(BASE_DIR, "artist_suggestions.json")
    BLACKLIST_FILE = os.path.join(BASE_DIR, "artist_blacklist.json")
    
    # Scraping settings
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', 'chromedriver')
    SCRAPING_TIMEOUT = 1800  # 30 minutes
    
    # Template settings
    TEMPLATES_AUTO_RELOAD = DEBUG
    
    # Production settings
    PREFERRED_URL_SCHEME = 'https' if not DEBUG else 'http'
    
    @classmethod
    def init_app(cls, app):
        """Initialize app-specific configuration."""
        # Ensure data directories exist
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        
        # Create empty data files if they don't exist
        for file_path in [cls.DATA_PATH, cls.FOLLOWED_ARTISTS_PATH, cls.SUGGESTIONS_FILE, cls.BLACKLIST_FILE]:
            if not os.path.exists(file_path):
                if file_path.endswith('.json'):
                    with open(file_path, 'w') as f:
                        f.write('[]')
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        errors = []
        
        if not cls.SPOTIFY_CLIENT_ID:
            errors.append("SPOTIFY_CLIENT_ID is required")
        
        if not cls.SPOTIFY_CLIENT_SECRET:
            errors.append("SPOTIFY_CLIENT_SECRET is required")
        
        if errors:
            raise ValueError("Configuration errors: " + "; ".join(errors))


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
