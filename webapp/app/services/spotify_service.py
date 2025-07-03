"""
Spotify service module for handling Spotify API interactions.
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import requests
from flask import session
import logging

logger = logging.getLogger(__name__)

class SpotifyService:
    def get_followed_artists(self, limit=50):
        """
        Get the list of artists followed by the current user.
        Args:
            limit: Maximum number of artists to return per request (max 50 per Spotify API)
        Returns:
            List of artist dicts, or empty list if not authenticated or error.
        """
        sp = self.get_authenticated_client()
        if not sp:
            return []
        artists = []
        after = None
        try:
            while True:
                if after:
                    results = sp.current_user_followed_artists(limit=limit, after=after)
                else:
                    results = sp.current_user_followed_artists(limit=limit)
                items = results.get('artists', {}).get('items', [])
                if not items:
                    break
                artists.extend(items)
                if len(items) < limit:
                    break
                after = items[-1]['id']
            return artists
        except Exception as e:
            logger.error(f"Error fetching followed artists: {e}")
            return []
    """Service class for Spotify API interactions."""
    
    def __init__(self, client_id, client_secret, redirect_uri, scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self._image_cache = {}
        self._public_client = None
    
    def get_public_client(self):
        """Get a public Spotify client using client credentials flow."""
        if not self._public_client:
            try:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                self._public_client = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            except Exception as e:
                logger.error(f"Failed to create public Spotify client: {e}")
                return None
        
        return self._public_client
    
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
        
        # Debug: Log the redirect URI being used
        logger.info(f"Using redirect URI: {self.redirect_uri}")
        
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
            str: Image URL or default image path if not found
        """
        if not artist_id:
            logger.warning("No artist_id provided for image fetch")
            return "/static/default-artist.png"
        
        # Check cache first
        if artist_id in self._image_cache:
            return self._image_cache[artist_id]
        
        try:
            artist_data = None
            
            # Try using provided token first
            if bearer_token:
                headers = {"Authorization": f"Bearer {bearer_token}"}
                resp = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
                if resp.status_code == 200:
                    artist_data = resp.json()
            
            # Try public client credentials first (works without session)
            if not artist_data:
                sp_public = self.get_public_client()
                if sp_public:
                    try:
                        artist_data = sp_public.artist(artist_id)
                    except Exception as e:
                        logger.debug(f"Public client failed for {artist_id}: {e}")
            
            # Fallback to authenticated client
            if not artist_data:
                try:
                    sp = self.get_authenticated_client()
                    if sp:
                        try:
                            artist_data = sp.artist(artist_id)
                        except Exception as e:
                            logger.debug(f"Authenticated client failed for {artist_id}: {e}")
                except RuntimeError:
                    # No session context, skip authenticated client
                    pass
            
            # Extract image URL if we have artist data
            if artist_data and artist_data.get("images"):
                image_url = artist_data["images"][0]["url"]
                # Cache the result
                self._image_cache[artist_id] = image_url
                return image_url
            else:
                logger.debug(f"No images found for artist {artist_id}")
                # Cache the default result to avoid repeated API calls
                self._image_cache[artist_id] = "/static/default-artist.png"
                return "/static/default-artist.png"
        
        except Exception as e:
            logger.error(f"Error fetching artist image for {artist_id}: {e}")
            # Cache the default result to avoid repeated API calls  
            self._image_cache[artist_id] = "/static/default-artist.png"
            return "/static/default-artist.png"
    
    def search_artists(self, query, limit=10):
        """
        Search for artists on Spotify.
        
        Args:
            query: Search query string
            limit: Maximum number of results
        
        Returns:
            list: List of artist dictionaries
        """
        results = None
        
        # Try public client first (works without session context)
        sp_public = self.get_public_client()
        if sp_public:
            try:
                results = sp_public.search(q=query, type='artist', limit=limit)
            except Exception as e:
                logger.debug(f"Public client failed for artist search '{query}': {e}")
        
        # Fallback to authenticated client if public client fails
        if not results:
            try:
                sp = self.get_authenticated_client()
                if sp:
                    try:
                        results = sp.search(q=query, type='artist', limit=limit)
                    except Exception as e:
                        logger.debug(f"Authenticated client failed for artist search '{query}': {e}")
            except RuntimeError:
                # No session context, skip authenticated client
                pass
        
        if not results:
            logger.error(f"Could not search artists for query: {query}")
            return []
        
        try:
            artists = []
            for artist in results.get('artists', {}).get('items', []):
                image = artist["images"][0]["url"] if artist.get("images") else ""
                # Defensive: never return template placeholders
                if isinstance(image, str) and image.startswith("${"):
                    image = ""
                artists.append({
                    "id": artist["id"],
                    "name": artist["name"],
                    "url": artist["external_urls"]["spotify"],
                    "image": image,
                    "followers": artist.get("followers", {}).get("total", 0)
                })
            return artists
        except Exception as e:
            logger.error(f"Error processing artist search results for '{query}': {e}")
            return []
    
    def get_artist_info(self, artist_id):
        """
        Get detailed artist information.
        
        Args:
            artist_id: Spotify artist ID
        
        Returns:
            dict: Artist information or empty dict
        """
        artist_data = None
        
        # Try public client first (works without session context)
        sp_public = self.get_public_client()
        if sp_public:
            try:
                artist_data = sp_public.artist(artist_id)
            except Exception as e:
                logger.debug(f"Public client failed for artist info {artist_id}: {e}")
        
        # Fallback to authenticated client if public client fails
        if not artist_data:
            try:
                sp = self.get_authenticated_client()
                if sp:
                    try:
                        artist_data = sp.artist(artist_id)
                    except Exception as e:
                        logger.debug(f"Authenticated client failed for artist info {artist_id}: {e}")
            except RuntimeError:
                # No session context, skip authenticated client
                pass
        
        if not artist_data:
            logger.error(f"Could not get artist info for {artist_id}")
            return {}
        
        try:
            return {
                "name": artist_data["name"],
                "image": artist_data["images"][0]["url"] if artist_data.get("images") else "",
                "genres": artist_data.get("genres", []),
                "popularity": artist_data.get("popularity", 0),
                "followers": artist_data.get("followers", {}).get("total", 0),
                "url": artist_data["external_urls"]["spotify"]
            }
        
        except Exception as e:
            logger.error(f"Error processing artist info for {artist_id}: {e}")
            return {}
    
    def get_artist_top_tracks(self, artist_id, market="US"):
        """
        Get top tracks for an artist.
        
        Args:
            artist_id: Spotify artist ID
            market: Market code (e.g., "US")
        
        Returns:
            list: List of track dictionaries
        """
        results = None
        
        # Try public client first (works without session context)
        sp_public = self.get_public_client()
        if sp_public:
            try:
                results = sp_public.artist_top_tracks(artist_id, country=market)
            except Exception as e:
                logger.debug(f"Public client failed for top tracks {artist_id}: {e}")
        
        # Fallback to authenticated client if public client fails
        if not results:
            try:
                sp = self.get_authenticated_client()
                if sp:
                    try:
                        results = sp.artist_top_tracks(artist_id, country=market)
                    except Exception as e:
                        logger.debug(f"Authenticated client failed for top tracks {artist_id}: {e}")
            except RuntimeError:
                # No session context, skip authenticated client
                pass
        
        if not results:
            logger.error(f"Could not get top tracks for {artist_id}")
            return []
        
        try:
            tracks = []
            import re
            def is_invalid_url(url):
                if not url or url is None:
                    return True
                if isinstance(url, str):
                    # Check for template placeholders or encoded templates
                    if url.strip() == '' or url.startswith('${') or re.match(r'^\$\{.*\}$', url):
                        return True
                    if url.lower().startswith('%24%7b') or re.match(r'^%24%7b.*%7d$', url, re.IGNORECASE):
                        return True
                return False

            for track in results.get("tracks", []):
                album_image = ""
                if track.get("album") and track["album"].get("images") and len(track["album"]["images"]) > 0:
                    album_image = track["album"]["images"][0]["url"]
                preview_url = track.get("preview_url")
                # Robustly sanitize URLs
                if is_invalid_url(album_image):
                    album_image = ""
                if is_invalid_url(preview_url):
                    preview_url = None
                tracks.append({
                    "name": track["name"],
                    "url": track["external_urls"]["spotify"],
                    "album_image": album_image,
                    "preview_url": preview_url,
                    "album": track["album"].get("name", "") if track.get("album") else "",
                    "artists": [a["name"] for a in track.get("artists", [])],
                })
            return tracks
        except Exception as e:
            logger.error(f"Error processing top tracks for {artist_id}: {e}")
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
