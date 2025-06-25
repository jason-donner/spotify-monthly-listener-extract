# config.py - Centralized configuration management

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    # Flask settings
    SECRET_KEY: str
    DEBUG: bool = False
    
    # Spotify API
    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    SPOTIFY_REDIRECT_URI: str
    
    # Database
    DATABASE_URL: str = "sqlite:///app.db"
    
    # Scraping
    CHROMEDRIVER_PATH: str = "chromedriver"
    SCRAPING_TIMEOUT: int = 1800  # 30 minutes
    
    # Caching
    CACHE_TTL: int = 300  # 5 minutes
    REDIS_URL: Optional[str] = None
    
    # Rate limiting
    RATELIMIT_STORAGE_URL: str = "memory://"
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production'),
            DEBUG=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            SPOTIFY_CLIENT_ID=cls._require_env('SPOTIPY_CLIENT_ID'),
            SPOTIFY_CLIENT_SECRET=cls._require_env('SPOTIPY_CLIENT_SECRET'),
            SPOTIFY_REDIRECT_URI=os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:5000/callback'),
            DATABASE_URL=os.getenv('DATABASE_URL', 'sqlite:///app.db'),
            CHROMEDRIVER_PATH=os.getenv('CHROMEDRIVER_PATH', 'chromedriver'),
            SCRAPING_TIMEOUT=int(os.getenv('SCRAPING_TIMEOUT', '1800')),
            CACHE_TTL=int(os.getenv('CACHE_TTL', '300')),
            REDIS_URL=os.getenv('REDIS_URL'),
            RATELIMIT_STORAGE_URL=os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
        )
    
    @staticmethod
    def _require_env(key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} not set")
        return value

# Validation
def validate_config(config: Config):
    """Validate configuration settings"""
    errors = []
    
    if not config.SECRET_KEY or config.SECRET_KEY == 'dev-key-change-in-production':
        if not config.DEBUG:
            errors.append("SECRET_KEY must be set for production")
    
    if not config.SPOTIFY_CLIENT_ID:
        errors.append("SPOTIFY_CLIENT_ID is required")
    
    if not config.SPOTIFY_CLIENT_SECRET:
        errors.append("SPOTIFY_CLIENT_SECRET is required")
    
    if errors:
        raise ValueError("Configuration errors: " + "; ".join(errors))

# Usage in app.py:
# from .config import Config, validate_config
# 
# config = Config.from_env()
# validate_config(config)
# app.config.from_object(config)
