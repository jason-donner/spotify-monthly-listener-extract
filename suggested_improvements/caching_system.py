# Caching improvements

from functools import wraps
import time
import hashlib
import json
from flask import request

# Simple in-memory cache
class SimpleCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key):
        if key in self._cache:
            return self._cache[key]
        return None
    
    def set(self, key, value, ttl=300):  # 5 minutes default
        self._cache[key] = value
        self._timestamps[key] = time.time() + ttl
    
    def is_expired(self, key):
        if key not in self._timestamps:
            return True
        return time.time() > self._timestamps[key]
    
    def cleanup(self):
        expired_keys = [k for k in self._timestamps if self.is_expired(k)]
        for key in expired_keys:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)

# Global cache instance
cache = SimpleCache()

def cached_route(ttl=300):
    """Decorator to cache route responses"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Create cache key from route and query params
            cache_key = f"{request.path}_{hashlib.md5(str(request.args).encode()).hexdigest()}"
            
            # Check if cached and not expired
            if not cache.is_expired(cache_key):
                cached_result = cache.get(cache_key)
                if cached_result:
                    return cached_result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# Usage example:
# @app.route("/leaderboard")
# @cached_route(ttl=600)  # Cache for 10 minutes
# def leaderboard():
#     # Expensive operation
#     return render_template("leaderboard.html", data=data)

# Artist image caching improvement
class ArtistImageCache:
    def __init__(self, max_size=1000):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
    
    def get(self, artist_id):
        if artist_id in self.cache:
            self.access_times[artist_id] = time.time()
            return self.cache[artist_id]
        return None
    
    def set(self, artist_id, image_url):
        if len(self.cache) >= self.max_size:
            # Remove least recently used
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            self.cache.pop(oldest_key)
            self.access_times.pop(oldest_key)
        
        self.cache[artist_id] = image_url
        self.access_times[artist_id] = time.time()
