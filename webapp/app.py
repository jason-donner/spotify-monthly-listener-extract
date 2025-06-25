"""
Spotify Monthly Listener Tracker - Main Application Entry Point

This is the main Flask application that ties together all the modular components:
- Configuration management
- Service layer (Spotify, Data, Job services)
- Route blueprints (Main and Admin)
"""

from flask import Flask
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modular components
from app.config import Config
from app.services import SpotifyService, DataService, JobService
from app.routes.main import create_main_routes
from app.routes.admin import create_admin_routes

def create_app():
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    Config.validate()  # Validate required settings
    
    # Initialize services
    spotify_service = SpotifyService(
        client_id=Config.SPOTIFY_CLIENT_ID,
        client_secret=Config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=Config.SPOTIFY_REDIRECT_URI,
        scope=Config.SPOTIFY_SCOPE
    )
    
    data_service = DataService(
        data_path=Config.DATA_PATH,
        followed_artists_path=Config.FOLLOWED_ARTISTS_PATH,
        suggestions_file=Config.SUGGESTIONS_FILE,
        blacklist_file=Config.BLACKLIST_FILE
    )
    job_service = JobService(
        chromedriver_path=Config.CHROMEDRIVER_PATH,
        scraping_timeout=Config.SCRAPING_TIMEOUT
    )
    
    # Store services in app context for access in routes
    app.spotify_service = spotify_service
    app.data_service = data_service
    app.job_service = job_service
    
    # Register blueprints
    main_bp = create_main_routes(spotify_service, data_service)
    admin_bp = create_admin_routes(spotify_service, data_service, job_service)
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Register template filters (from original app.py)
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='medium'):
        from datetime import datetime
        if not value:
            return ''
        if isinstance(value, str):
            try:
                # Handle YYYY-MM-DD
                if len(value) == 10 and '-' in value:
                    dt = datetime.strptime(value, "%Y-%m-%d")
                # Handle YYYY-MM
                elif len(value) == 7 and '-' in value:
                    dt = datetime.strptime(value, "%Y-%m")
                # Handle YYYYMMDD
                elif len(value) == 8 and value.isdigit():
                    dt = datetime.strptime(value, "%Y%m%d")
                else:
                    return value
            except Exception:
                return value
        else:
            dt = value
        if format == 'short':
            # "Jun 18" or "Jun 2024"
            if isinstance(value, str) and len(value) in (10, 8):  # YYYY-MM-DD or YYYYMMDD
                return dt.strftime('%b %d')
            elif isinstance(value, str) and len(value) == 7:      # YYYY-MM
                return dt.strftime('%b %Y')
        # Use the provided format string for all other cases
        return dt.strftime(format)
    
    @app.template_filter('format_number')
    def format_number(num):
        """Format large numbers with appropriate suffixes"""
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        else:
            return str(num)

    # Clean up old job files on startup
    job_service.cleanup_old_jobs()
    
    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    print("Starting Spotify Monthly Listener Tracker...")
    app.run(debug=True, host="127.0.0.1", port=5000)