# Example of how to restructure the Flask app

# app/__init__.py
from flask import Flask
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    from .routes import main_bp, admin_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

# app/models/artist.py
class Artist:
    def __init__(self, artist_id, name, url, monthly_listeners=None):
        self.artist_id = artist_id
        self.name = name
        self.url = url
        self.monthly_listeners = monthly_listeners or []
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            artist_id=data.get('artist_id'),
            name=data.get('artist_name'),
            url=data.get('url'),
            monthly_listeners=data.get('monthly_listeners', [])
        )

# app/services/spotify_service.py
class SpotifyService:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    def get_oauth(self):
        return SpotifyOAuth(...)
    
    def get_authenticated_client(self, token_info):
        return spotipy.Spotify(auth=token_info['access_token'])

# app/services/data_service.py
class DataService:
    @staticmethod
    def load_master_data():
        # Load and cache data
        pass
    
    @staticmethod
    def get_artist_history(artist_id):
        # Get artist's historical data
        pass
