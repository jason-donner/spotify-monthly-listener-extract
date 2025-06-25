"""
Spotify service module for handling Spotify API interactions.
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from flask import session
import logging

logger = logging.getLogger(__name__)

class SpotifyService:
    """Service class for Spotify API interactions."""
    
    def __init__(self, client_id, client_secret, redirect_uri, scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self._image_cache = {}
    
    def get_oauth(self, show_dialog=True):
        """Create a SpotifyOAuth instance."""
        return SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            cache_path=None,  # Use session storage instead
            show_dialog=show_dialog
        )
    
    def get_token_from_session(self):
        """Get Spotify token from Flask session."""
        return session.get('spotify_token')
    
    def save_token_to_session(self, token_info):
        """Save Spotify token to Flask session."""
        session['spotify_token'] = token_info
    
    def get_authenticated_client(self):
        """Get an authenticated Spotify client or None if not authenticated."""
        token_info = self.get_token_from_session()
        
        if not token_info:
            return None
        
        sp_oauth = self.get_oauth()
        
        # Check if token is expired and refresh if needed
        if sp_oauth.is_token_expired(token_info):
            try:
                token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                self.save_token_to_session(token_info)
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                session.pop('spotify_token', None)
                return None
        
        return spotipy.Spotify(auth=token_info['access_token'])
    
    def get_auth_url(self, force_login=False):
        """Get Spotify OAuth authorization URL."""
        if force_login:
            # Clear any existing session data
            session.pop('spotify_token', None)
            # Create OAuth with show_dialog=True to force account selection
            sp_oauth = self.get_oauth(show_dialog=True)
        else:
            sp_oauth = self.get_oauth()
        
        return sp_oauth.get_authorize_url()
    
    def handle_oauth_callback(self, code):
        """Handle OAuth callback and save token to session."""
        try:
            sp_oauth = self.get_oauth()
            token_info = sp_oauth.get_access_token(code)
            self.save_token_to_session(token_info)
            return True
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return False
    
    def logout(self):
        """Clear Spotify authentication."""
        session.pop('spotify_token', None)
    
    def get_auth_status(self):
        """Check if user is authenticated with Spotify and return status."""
        token_info = self.get_token_from_session()
        
        if not token_info:
            return {"authenticated": False}
        
        sp_oauth = self.get_oauth()
        
        # Check if token is expired and refresh if needed
        if sp_oauth.is_token_expired(token_info):
            try:
                token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                self.save_token_to_session(token_info)
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
                session.pop('spotify_token', None)
                return {"authenticated": False}
        
        # Test the token by making a simple API call
        try:
            sp = spotipy.Spotify(auth=token_info['access_token'])
            user = sp.current_user()
            
            # Debug logging to see which account we're actually authenticated as
            logger.info(f"Authenticated user ID: {user.get('id')}")
            logger.info(f"Authenticated user display name: {user.get('display_name')}")
            logger.info(f"User email: {user.get('email', 'Not available')}")
            
            return {
                "authenticated": True,
                "user": {
                    "id": user.get('id'),
                    "display_name": user.get('display_name'),
                    "images": user.get('images', [])
                }
            }
        except Exception as e:
            logger.error(f"Auth status error: {e}")
            session.pop('spotify_token', None)
            return {"authenticated": False}
    
    def fetch_artist_image(self, artist_id, bearer_token=None):
        """
        Fetch artist image from Spotify API with caching.
        
        Args:
            artist_id: Spotify artist ID
            bearer_token: Bearer token for API requests (optional)
        
        Returns:
            str: Image URL or None if not found
        """
        if not artist_id:
            logger.warning("No artist_id provided for image fetch")
            return None
        
        # Check cache first
        if artist_id in self._image_cache:
            return self._image_cache[artist_id]
        
        try:
            # Use provided token or get from authenticated client
            if bearer_token:
                headers = {"Authorization": f"Bearer {bearer_token}"}
                resp = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
            else:
                sp = self.get_authenticated_client()
                if not sp:
                    return None
                artist = sp.artist(artist_id)
                # Create a mock response object that behaves like requests.Response
                class MockResponse:
                    def __init__(self, data):
                        self.status_code = 200
                        self._data = data
                    
                    def json(self):
                        return self._data
                
                resp = MockResponse(artist)
            
            if resp.status_code == 200:
                artist_data = resp.json() if hasattr(resp, 'json') else resp
                if artist_data.get("images"):
                    image_url = artist_data["images"][0]["url"]
                    # Cache the result
                    self._image_cache[artist_id] = image_url
                    return image_url
                else:
                    logger.debug(f"No images found for artist {artist_id}")
            else:
                logger.error(f"Spotify API error for {artist_id}: {resp.status_code}")
        
        except Exception as e:
            logger.error(f"Error fetching artist image for {artist_id}: {e}")
        
        return None
    
    def search_artists(self, query, limit=10):
        """
        Search for artists on Spotify.
        
        Args:
            query: Search query string
            limit: Maximum number of results
        
        Returns:
            list: List of artist dictionaries
        """
        sp = self.get_authenticated_client()
        if not sp:
            return []
        
        try:
            results = sp.search(q=query, type='artist', limit=limit)
            artists = []
            
            for artist in results.get('artists', {}).get('items', []):
                artists.append({
                    "id": artist["id"],
                    "name": artist["name"],
                    "url": artist["external_urls"]["spotify"],
                    "image": artist["images"][0]["url"] if artist.get("images") else "",
                    "followers": artist.get("followers", {}).get("total", 0)
                })
            
            return artists
        
        except Exception as e:
            logger.error(f"Error searching artists: {e}")
            return []
    
    def get_artist_info(self, artist_id):
        """
        Get detailed artist information.
        
        Args:
            artist_id: Spotify artist ID
        
        Returns:
            dict: Artist information or empty dict
        """
        sp = self.get_authenticated_client()
        if not sp:
            return {}
        
        try:
            artist = sp.artist(artist_id)
            return {
                "name": artist["name"],
                "image": artist["images"][0]["url"] if artist.get("images") else "",
                "genres": artist.get("genres", []),
                "popularity": artist.get("popularity", 0),
                "followers": artist.get("followers", {}).get("total", 0),
                "url": artist["external_urls"]["spotify"]
            }
        
        except Exception as e:
            logger.error(f"Error getting artist info for {artist_id}: {e}")
            return {}
    
    def get_top_tracks(self, artist_id, market="US"):
        """
        Get top tracks for an artist.
        
        Args:
            artist_id: Spotify artist ID
            market: Market code (e.g., "US")
        
        Returns:
            list: List of track dictionaries
        """
        sp = self.get_authenticated_client()
        if not sp:
            return []
        
        try:
            results = sp.artist_top_tracks(artist_id, country=market)
            tracks = []
            
            for track in results.get("tracks", []):
                tracks.append({
                    "name": track["name"],
                    "url": track["external_urls"]["spotify"],
                    "album_image": track["album"]["images"][0]["url"] if track["album"]["images"] else ""
                })
            
            return tracks
        
        except Exception as e:
            logger.error(f"Error getting top tracks for {artist_id}: {e}")
            return []
    
    def follow_artist(self, artist_id):
        """
        Follow an artist on Spotify.
        
        Args:
            artist_id: Spotify artist ID
        
        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        sp = self.get_authenticated_client()
        if not sp:
            return False, "Authentication required"
        
        try:
            sp.user_follow_artists([artist_id])
            logger.info(f"Successfully followed artist {artist_id}")
            return True, None
        
        except spotipy.SpotifyException as e:
            if e.http_status == 401:
                # Clear invalid token
                session.pop('spotify_token', None)
                return False, "Authentication expired"
            else:
                logger.error(f"Spotify API error following artist {artist_id}: {e}")
                return False, f"Spotify API error: {str(e)}"
        
        except Exception as e:
            logger.error(f"Error following artist {artist_id}: {e}")
            return False, str(e)
    
    def get_current_user(self):
        """
        Get current user information.
        
        Returns:
            dict: User information or None
        """
        sp = self.get_authenticated_client()
        if not sp:
            return None
        
        try:
            user = sp.current_user()
            return {
                "id": user.get('id'),
                "display_name": user.get('display_name'),
                "images": user.get('images', []),
                "email": user.get('email', 'Not available')
            }
        
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
