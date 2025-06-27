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
import json
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables
load_dotenv()

# Import AWS SDK for Secrets Manager (only if running in production)
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

def load_secrets_from_aws():
    """Load secrets from AWS Secrets Manager if available and configured"""
    if not AWS_AVAILABLE:
        return {}
    
    secret_name = os.environ.get('AWS_SECRET_NAME')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    if not secret_name:
        return {}
    
    try:
        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region
        )
        
        # Retrieve the secret
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response['SecretString']
        secrets = json.loads(secret_string)
        
        print(f"Successfully loaded {len(secrets)} secrets from AWS Secrets Manager")
        return secrets
    
    except ClientError as e:
        print(f"Error retrieving secrets from AWS Secrets Manager: {e}")
        return {}
    except NoCredentialsError:
        print("AWS credentials not found. Using environment variables.")
        return {}
    except Exception as e:
        print(f"Unexpected error loading secrets: {e}")
        return {}

def configure_environment():
    """Configure environment variables from AWS Secrets Manager or local .env"""
    # Load secrets from AWS if available
    aws_secrets = load_secrets_from_aws()
    
    # Set environment variables from AWS secrets (they take precedence)
    for key, value in aws_secrets.items():
        os.environ[key] = value
    
    # Validate required environment variables
    required_vars = [
        'FLASK_SECRET_KEY',
        'ADMIN_PASSWORD',
        'SPOTIPY_CLIENT_ID',
        'SPOTIPY_CLIENT_SECRET',
        'SPOTIPY_REDIRECT_URI'
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"WARNING: Missing required environment variables: {', '.join(missing_vars)}")
        print("The application may not function properly without these variables.")
        # Set default values for missing variables to allow startup
        for var in missing_vars:
            if var == 'FLASK_SECRET_KEY':
                os.environ[var] = 'dev-secret-key-change-in-production'
            elif var == 'ADMIN_PASSWORD':
                os.environ[var] = 'admin123'
            elif var == 'SPOTIPY_CLIENT_ID':
                os.environ[var] = 'missing-client-id'
            elif var == 'SPOTIPY_CLIENT_SECRET':
                os.environ[var] = 'missing-client-secret'
            elif var == 'SPOTIPY_REDIRECT_URI':
                os.environ[var] = 'http://localhost:8080/callback'

# Configure environment before importing other modules
configure_environment()

# Import our modular components
from app.config import Config
from app.services import SpotifyService, DataService, JobService
from app.services.scheduler_service import SchedulerService
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
    Config.init_app(app)  # Initialize app-specific config
    
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
        suggestions_file=Config.SUGGESTIONS_FILE,
        blacklist_file=Config.BLACKLIST_FILE
    )
    job_service = JobService(
        chromedriver_path=Config.CHROMEDRIVER_PATH,
        scraping_timeout=Config.SCRAPING_TIMEOUT
    )
    
    # Initialize scheduler service
    scheduler_service = SchedulerService(job_service)
    
    # Store services in app context for access in routes
    app.spotify_service = spotify_service
    app.data_service = data_service
    app.job_service = job_service
    app.scheduler_service = scheduler_service
    
    # Register blueprints
    main_bp = create_main_routes(spotify_service, data_service)
    admin_bp = create_admin_routes(spotify_service, data_service, job_service, scheduler_service)
    
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
    
    # Start the scheduler service
    scheduler_service.start_scheduler()
    
    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    print("Starting Spotify Monthly Listener Tracker...")
    # Only enable debug mode in development
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    # Use environment-specific host and port
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    app.run(debug=debug_mode, host=host, port=port)