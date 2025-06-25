# security.py - Security enhancements

from flask import request, jsonify, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import hashlib
import time
from datetime import datetime, timedelta
import secrets

class SecurityManager:
    def __init__(self, app=None):
        self.app = app
        self.failed_attempts = {}  # IP -> count
        self.blocked_ips = {}  # IP -> timestamp
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        # Set secure session cookie settings
        app.config.update(
            SESSION_COOKIE_SECURE=True,  # HTTPS only
            SESSION_COOKIE_HTTPONLY=True,  # No JS access
            SESSION_COOKIE_SAMESITE='Lax',
            PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
        )
    
    def is_admin_authenticated(self):
        """Check if user is authenticated as admin"""
        return session.get('spotify_token') is not None
    
    def rate_limit_key(self):
        """Generate rate limit key based on IP or user"""
        if self.is_admin_authenticated():
            # Authenticated users get higher limits
            return f"user:{session.get('user_id', 'anonymous')}"
        return f"ip:{get_remote_address()}"

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('spotify_token'):
            return jsonify({
                'error': 'Authentication required',
                'auth_required': True
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def validate_spotify_url(url):
    """Validate Spotify URL format"""
    if not url:
        return False
    
    # Basic Spotify URL validation
    valid_patterns = [
        'https://open.spotify.com/artist/',
        'https://spotify.com/artist/',
    ]
    
    return any(url.startswith(pattern) for pattern in valid_patterns)

def sanitize_artist_name(name):
    """Sanitize artist name input"""
    if not name or not isinstance(name, str):
        return ""
    
    # Remove potentially dangerous characters
    import re
    # Allow alphanumeric, spaces, common punctuation
    sanitized = re.sub(r'[^\w\s\-\.\'\&\(\)]+', '', name)
    return sanitized.strip()[:255]  # Limit length

def setup_security(app):
    """Configure security settings for the Flask app"""
    
    # Rate limiting
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Security headers middleware
    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # CSRF protection for forms
    @app.before_request
    def csrf_protect():
        if request.method == "POST":
            token = session.pop('_csrf_token', None)
            if not token or token != request.form.get('_csrf_token'):
                # Skip CSRF for JSON API requests with proper headers
                if request.is_json and request.headers.get('Content-Type') == 'application/json':
                    pass
                else:
                    abort(403)
    
    def generate_csrf_token():
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_urlsafe(32)
        return session['_csrf_token']
    
    app.jinja_env.globals['csrf_token'] = generate_csrf_token
    
    return limiter

# Input validation decorators
def validate_json(*required_fields):
    """Decorator to validate JSON input"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid JSON'}), 400
            
            # Check required fields
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Rate limiting for specific endpoints
rate_limits = {
    'suggest_artist': "5 per minute",
    'scraping': "1 per 10 minutes",
    'search': "30 per minute"
}

# Example usage:
# @app.route('/suggest_artist', methods=['POST'])
# @limiter.limit(rate_limits['suggest_artist'])
# @validate_json('artist_name')
# def suggest_artist():
#     pass
