"""
Spotify Monthly Listener Tracker - Main Application Entry Point

This is the main Flask application that ties together all the modular components:
- Configuration management
- Service layer (Spotify, Data, Job services)
- Route blueprints (Main and Admin)
"""

from flask import Flask
import os
import logging
import logging.handlers
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables
load_dotenv()

# Import our modular components
from app.config import Config
from app.services import SpotifyService, DataService, JobService
from app.routes.main import create_main_routes
from app.routes.admin import create_admin_routes

def setup_logging():
    """Configure centralized logging for the application"""
    log_level = logging.DEBUG if os.environ.get('FLASK_DEBUG', 'false').lower() == 'true' else logging.INFO
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    ))
    
    # Create admin-specific log file for security monitoring
    admin_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'admin.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    admin_handler.setLevel(logging.INFO)
    admin_handler.setFormatter(logging.Formatter(
        '%(asctime)s - ADMIN - %(levelname)s - %(message)s'
    ))
    
    # Add handlers to root logger
    logging.getLogger().addHandler(file_handler)
    
    # Create admin logger for security events
    admin_logger = logging.getLogger('admin_security')
    admin_logger.addHandler(admin_handler)
    admin_logger.setLevel(logging.INFO)
    
    logging.info("Logging system initialized")

def create_app():
    """Application factory function"""
    # Setup logging first
    setup_logging()
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    Config.validate()  # Validate required settings
    
    # Configure sessions for admin authentication
    app.secret_key = os.getenv('SECRET_KEY', 'new-secret-key-2025-reset')  # Changed to invalidate old sessions
    app.permanent_session_lifetime = timedelta(hours=24)  # Admin session lasts 24 hours
    
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
        suggestions_file=None,  # Legacy suggestions removed
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
            # Always return Month Day, Year for 'short'
            return dt.strftime('%b %d, %Y')
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

    # Register blueprints
    main_bp = create_main_routes(spotify_service, data_service)
    admin_bp = create_admin_routes(spotify_service, data_service, job_service)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    # (Debug route printout removed for production cleanliness)
    # Clean up old job files on startup
    job_service.cleanup_old_jobs()
    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    print("Starting Spotify Monthly Listener Tracker...")
    # Only enable debug mode in development
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host="127.0.0.1", port=5000)