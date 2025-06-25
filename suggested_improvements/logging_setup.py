# logging_config.py - Structured logging setup

import logging
import logging.handlers
import json
from datetime import datetime
from flask import request, g
import traceback

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available
        try:
            if request:
                log_data['request'] = {
                    'method': request.method,
                    'path': request.path,
                    'ip': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                }
        except RuntimeError:
            # Outside request context
            pass
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data)

def setup_logging(app):
    """Configure application logging"""
    
    # Create logs directory
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Remove default Flask handlers
    app.logger.handlers.clear()
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if app.debug else logging.WARNING)
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/app.log', maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/error.log', maxBytes=10*1024*1024, backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    
    # Add handlers to app logger
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.INFO)
    
    # Configure other loggers
    logging.getLogger('scraping').addHandler(file_handler)
    logging.getLogger('spotify_api').addHandler(file_handler)

# error_handlers.py - Custom error handlers
from flask import jsonify, render_template
import logging

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    
    @app.errorhandler(400)
    def bad_request(error):
        logger.warning(f"Bad request: {error}")
        if request.is_json:
            return jsonify({'error': 'Bad request'}), 400
        return render_template('error.html', error='Bad request'), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        logger.warning(f"Unauthorized access: {error}")
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        return render_template('error.html', error='Authentication required'), 401
    
    @app.errorhandler(404)
    def not_found(error):
        logger.info(f"Page not found: {request.url}")
        if request.is_json:
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('error.html', error='Page not found'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}", exc_info=True)
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('error.html', error='Internal server error'), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        if request.is_json:
            return jsonify({'error': 'An unexpected error occurred'}), 500
        return render_template('error.html', error='An unexpected error occurred'), 500
