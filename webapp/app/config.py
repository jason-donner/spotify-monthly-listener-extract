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
    
    # Spotify API credentials
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:5000/callback")
    SPOTIFY_SCOPE = "user-follow-modify user-follow-read"
    
    # Data file paths
    DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "results", "spotify-monthly-listeners-master.json")
    FOLLOWED_ARTISTS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "results", "spotify-followed-artists-master.json")
    SUGGESTIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "artist_suggestions.json")
    BLACKLIST_FILE = os.path.join(os.path.dirname(__file__), "..", "artist_blacklist.json")
    
    # Scraping settings
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', 'chromedriver')
    SCRAPING_TIMEOUT = 1800  # 30 minutes
    
    # Template settings
    TEMPLATES_AUTO_RELOAD = True
    
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
