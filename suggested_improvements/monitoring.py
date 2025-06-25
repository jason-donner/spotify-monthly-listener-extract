# monitoring.py - Health checks and metrics

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import os
import json
import psutil
from collections import defaultdict
import time

monitoring_bp = Blueprint('monitoring', __name__)

class MetricsCollector:
    def __init__(self):
        self.metrics = defaultdict(int)
        self.timings = defaultdict(list)
        self.errors = defaultdict(int)
    
    def increment(self, metric_name):
        """Increment a counter metric"""
        self.metrics[metric_name] += 1
    
    def timing(self, metric_name, duration):
        """Record a timing metric"""
        self.timings[metric_name].append(duration)
        # Keep only last 1000 measurements
        if len(self.timings[metric_name]) > 1000:
            self.timings[metric_name] = self.timings[metric_name][-1000:]
    
    def error(self, error_type):
        """Record an error"""
        self.errors[error_type] += 1
    
    def get_stats(self):
        """Get current statistics"""
        return {
            'counters': dict(self.metrics),
            'timings': {
                k: {
                    'count': len(v),
                    'avg': sum(v) / len(v) if v else 0,
                    'min': min(v) if v else 0,
                    'max': max(v) if v else 0
                } for k, v in self.timings.items()
            },
            'errors': dict(self.errors)
        }

# Global metrics collector
metrics = MetricsCollector()

@monitoring_bp.route('/health')
def health_check():
    """Basic health check endpoint"""
    try:
        # Check database connectivity
        # db_healthy = check_database_health()
        
        # Check file system access
        data_dir = 'src/results'
        fs_healthy = os.path.exists(data_dir) and os.access(data_dir, os.R_OK | os.W_OK)
        
        # Check if essential files exist
        master_file = os.path.join(data_dir, 'spotify-monthly-listeners-master.json')
        master_file_exists = os.path.exists(master_file)
        
        # Overall health
        healthy = fs_healthy and master_file_exists
        
        return jsonify({
            'status': 'healthy' if healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'filesystem': fs_healthy,
                'master_file': master_file_exists
            }
        }), 200 if healthy else 503
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@monitoring_bp.route('/metrics')
def app_metrics():
    """Application metrics endpoint"""
    return jsonify({
        'timestamp': datetime.utcnow().isoformat(),
        'system': {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
        },
        'application': metrics.get_stats()
    })

@monitoring_bp.route('/status')
def detailed_status():
    """Detailed application status"""
    try:
        # Count total artists and data points
        master_file = 'src/results/spotify-monthly-listeners-master.json'
        if os.path.exists(master_file):
            with open(master_file, 'r') as f:
                data = json.load(f)
                total_records = len(data)
                unique_artists = len(set(item.get('artist_id', item.get('artist_name', '')) for item in data))
                
                # Get date range
                dates = [item.get('date', '') for item in data if item.get('date')]
                date_range = {
                    'earliest': min(dates) if dates else None,
                    'latest': max(dates) if dates else None
                }
        else:
            total_records = 0
            unique_artists = 0
            date_range = {'earliest': None, 'latest': None}
        
        # Check for recent scraping activity
        recent_files = []
        results_dir = 'src/results'
        if os.path.exists(results_dir):
            for filename in os.listdir(results_dir):
                if filename.startswith('spotify-monthly-listeners-') and filename.endswith('.json'):
                    if filename != 'spotify-monthly-listeners-master.json':
                        file_path = os.path.join(results_dir, filename)
                        mtime = os.path.getmtime(file_path)
                        if datetime.fromtimestamp(mtime) > datetime.now() - timedelta(days=7):
                            recent_files.append({
                                'filename': filename,
                                'modified': datetime.fromtimestamp(mtime).isoformat()
                            })
        
        return jsonify({
            'status': 'operational',
            'timestamp': datetime.utcnow().isoformat(),
            'data_stats': {
                'total_records': total_records,
                'unique_artists': unique_artists,
                'date_range': date_range
            },
            'recent_activity': {
                'files_modified_7_days': len(recent_files),
                'recent_files': recent_files[:5]  # Show last 5
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

# Request timing middleware
def setup_request_timing(app):
    @app.before_request
    def before_request():
        request.start_time = time.time()
        metrics.increment('requests_total')
    
    @app.after_request
    def after_request(response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            metrics.timing('request_duration', duration)
            
            # Track response codes
            metrics.increment(f'responses_{response.status_code}')
        
        return response
