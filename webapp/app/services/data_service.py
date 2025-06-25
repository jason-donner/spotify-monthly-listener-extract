"""
Data service module for handling data operations.
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DataService:
    """Service class for data operations."""
    
    def __init__(self, data_path: str, followed_artists_path: str, suggestions_file: str, blacklist_file: str):
        self.data_path = data_path
        self.followed_artists_path = followed_artists_path
        self.suggestions_file = suggestions_file
        self.blacklist_file = blacklist_file
        self._data_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 60  # 1 minute - more responsive to changes
    
    def load_data(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Load the master data file with optional caching.
        
        Args:
            use_cache: Whether to use cached data if available
        
        Returns:
            List of artist data dictionaries
        """
        current_time = datetime.now()
        
        # Check if file exists
        if not os.path.exists(self.data_path):
            logger.error(f"Data file not found: {self.data_path}")
            return []
        
        # Get file modification time
        try:
            file_mtime = datetime.fromtimestamp(os.path.getmtime(self.data_path))
        except OSError as e:
            logger.error(f"Error getting file modification time: {e}")
            file_mtime = current_time
        
        # Check cache validity - invalidate if file is newer than cache
        cache_valid = (
            use_cache and 
            self._data_cache is not None and 
            self._cache_timestamp is not None and
            (current_time - self._cache_timestamp).seconds < self._cache_ttl and
            (self._cache_timestamp >= file_mtime)  # Cache is newer than file
        )
        
        if cache_valid:
            return self._data_cache
        
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Update cache
            self._data_cache = data
            self._cache_timestamp = current_time
            
            logger.info(f"Loaded {len(data)} records from data file (cache {'refreshed' if not cache_valid else 'used'})")
            return data
        
        except FileNotFoundError:
            logger.error(f"Data file not found: {self.data_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in data file: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return []
    
    def clear_cache(self):
        """Clear the data cache."""
        self._data_cache = None
        self._cache_timestamp = None
    
    def get_artist_id_from_url(self, url: str) -> str:
        """
        Extract artist ID from Spotify URL.
        
        Args:
            url: Spotify artist URL
        
        Returns:
            Artist ID string
        """
        if not url:
            return ""
        return url.rstrip('/').split('/')[-1]
    
    def slugify(self, value: str) -> str:
        """
        Convert a string to a URL-friendly slug.
        
        Args:
            value: String to slugify
        
        Returns:
            Slugified string
        """
        if not value:
            return ""
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()
        return re.sub(r'[-\s]+', '-', value)
    
    def get_artist_history(self, artist_id: str) -> List[Dict[str, Any]]:
        """
        Get historical data for a specific artist.
        
        Args:
            artist_id: Spotify artist ID
        
        Returns:
            List of historical data points
        """
        data = self.load_data()
        return [entry for entry in data if entry.get("artist_id") == artist_id]
    
    def search_artists(self, query: str) -> List[Dict[str, Any]]:
        """
        Search artists in the data.
        
        Args:
            query: Search query
        
        Returns:
            List of matching artists with most recent data
        """
        if not query:
            return []
        
        data = self.load_data()
        query_lower = query.lower()
        
        # Find artists matching the query
        filtered = [a.copy() for a in data if query_lower in a.get("artist_name", "").lower()]
        
        # Group by artist_id, keep only the most recent entry for each
        grouped = {}
        for entry in filtered:
            artist_id = entry.get("artist_id")
            if not artist_id and entry.get("artist_url"):
                artist_id = self.get_artist_id_from_url(entry["artist_url"])
                entry["artist_id"] = artist_id
            
            entry["slug"] = self.slugify(entry.get("artist_name", "artist"))
            
            # Keep the most recent entry for each artist_id
            if artist_id not in grouped or entry.get("date", "") > grouped[artist_id].get("date", ""):
                grouped[artist_id] = entry
        
        results = list(grouped.values())
        results.sort(key=lambda x: x.get("artist_name", "").lower())
        
        # Calculate listener differences (simplified)
        for i, r in enumerate(results):
            if i + 1 < len(results):
                prev = results[i + 1]
                r['listener_diff'] = r['monthly_listeners'] - prev['monthly_listeners']
            else:
                r['listener_diff'] = None
        
        return results
    
    def get_leaderboard_data(self, mode: str = 'growth', tier: str = 'all', current_month: bool = True) -> Dict[str, Any]:
        """
        Generate leaderboard data.
        
        Args:
            mode: 'growth' or 'loss'
            tier: Artist tier filter
            current_month: If True, only show current month data; if False, use last 30 days
        
        Returns:
            Dictionary with leaderboard data and metadata
        """
        data = self.load_data()
        artist_changes = {}
        
        # Set date range based on current_month parameter
        if current_month:
            # Get start and end of current month
            now = datetime.now()
            start_of_month = datetime(now.year, now.month, 1)
            cutoff = start_of_month
        else:
            # Use traditional 30-day lookback
            cutoff = datetime.now() - timedelta(days=30)
        
        # Group data by artist
        for entry in data:
            artist = entry["artist_name"]
            date_str = entry["date"]
            
            try:
                if '-' in date_str:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    date = datetime.strptime(date_str, "%Y%m%d")
            except Exception:
                continue
            
            listeners = entry["monthly_listeners"]
            if artist not in artist_changes:
                artist_changes[artist] = []
            
            artist_changes[artist].append({
                "date": date,
                "listeners": listeners,
                "artist_url": entry.get("artist_url", ""),
                "artist_id": entry.get("artist_id"),
                "slug": self.slugify(artist)
            })
        
        leaderboard_data = []
        
        # Set the display dates based on current_month parameter
        if current_month:
            # For current month display, show the month name
            now = datetime.now()
            start_date = datetime(now.year, now.month, 1)
            # End date is current date or last day of month if we're past it
            if now.month == 12:
                next_month = datetime(now.year + 1, 1, 1)
            else:
                next_month = datetime(now.year, now.month + 1, 1)
            end_date = min(now, next_month - timedelta(days=1))
        else:
            start_date = None
            end_date = None
        
        for artist, records in artist_changes.items():
            recent = [r for r in records if r["date"] >= cutoff]
            if len(recent) < 2:
                continue
            
            recent.sort(key=lambda x: x["date"])
            
            start = recent[0]["listeners"]
            end = recent[-1]["listeners"]
            
            if start == 0 or (start < 50 and end < 50):
                continue
            
            change = end - start
            percent_change = ((end - start) / start) * 100
            
            # Get artist metadata
            artist_id = None
            artist_url = None
            slug = None
            for r in reversed(recent):
                if r and r.get("artist_id"):
                    artist_id = r["artist_id"]
                    artist_url = r.get("artist_url")
                    slug = r.get("slug")
                    break
            
            leaderboard_data.append({
                "artist": artist,
                "artist_id": artist_id,
                "slug": slug,
                "change": change,
                "percent_change": percent_change,
                "start": start,
                "end": end,
                "artist_url": artist_url
            })
        
        # Filter by tier
        def in_tier(start, end, tier):
            if tier == 'micro':
                return start <= 1000 and end <= 1000
            elif tier == 'small':
                return 1001 <= start <= 3000 and 1001 <= end <= 3000
            elif tier == 'medium':
                return 3001 <= start <= 15000 and 3001 <= end <= 15000
            elif tier == 'large':
                return 15001 <= start <= 50000 and 15001 <= end <= 50000
            elif tier == 'major':
                return start > 50000 and end > 50000
            return True
        
        leaderboard_data = [row for row in leaderboard_data if in_tier(row['start'], row['end'], tier)]
        
        # Sort by mode
        if mode == 'loss':
            leaderboard_data.sort(key=lambda x: x['percent_change'])
        else:
            leaderboard_data.sort(key=lambda x: x['percent_change'], reverse=True)
        
        # Take top 10
        leaderboard_data = leaderboard_data[:10]
        
        return {
            'leaderboard': leaderboard_data,
            'start_date': start_date,
            'end_date': end_date,
            'mode': mode,
            'tier': tier
        }
    
    def load_suggestions(self) -> List[Dict[str, Any]]:
        """Load artist suggestions from file."""
        if not os.path.exists(self.suggestions_file):
            return []
        
        try:
            with open(self.suggestions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading suggestions: {e}")
            return []
    
    def save_suggestions(self, suggestions: List[Dict[str, Any]]) -> bool:
        """
        Save suggestions to file.
        
        Args:
            suggestions: List of suggestion dictionaries
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.suggestions_file, "w", encoding="utf-8") as f:
                json.dump(suggestions, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving suggestions: {e}")
            return False
    
    def load_blacklist(self) -> tuple[List[str], List[str]]:
        """
        Load blacklisted artists and IDs.
        
        Returns:
            Tuple of (blacklisted_names, blacklisted_ids)
        """
        blacklisted_artists = []
        blacklisted_ids = []
        
        if not os.path.exists(self.blacklist_file):
            return blacklisted_artists, blacklisted_ids
        
        try:
            with open(self.blacklist_file, "r", encoding="utf-8") as f:
                blacklist_data = json.load(f)
                
                for item in blacklist_data:
                    if isinstance(item, str):
                        # Old format - just artist name
                        blacklisted_artists.append(item.lower())
                    elif isinstance(item, dict):
                        # New format - object with name, spotify_id, etc.
                        if item.get("name"):
                            blacklisted_artists.append(item["name"].lower())
                        if item.get("spotify_id"):
                            blacklisted_ids.append(item["spotify_id"])
        
        except Exception as e:
            logger.error(f"Error loading blacklist: {e}")
        
        return blacklisted_artists, blacklisted_ids
    
    def load_followed_artists(self) -> List[Dict[str, Any]]:
        """Load followed artists from file."""
        if not os.path.exists(self.followed_artists_path):
            return []
        
        try:
            with open(self.followed_artists_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading followed artists: {e}")
            return []
    
    def save_followed_artists(self, artists: List[Dict[str, Any]]) -> bool:
        """
        Save followed artists to file.
        
        Args:
            artists: List of artist dictionaries
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.followed_artists_path, "w", encoding="utf-8") as f:
                json.dump(artists, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving followed artists: {e}")
            return False
    
    def is_artist_followed(self, artist_name: str, spotify_id: str = None) -> bool:
        """
        Check if an artist is already being followed.
        
        Args:
            artist_name: Artist name
            spotify_id: Spotify artist ID (optional)
        
        Returns:
            True if artist is followed, False otherwise
        """
        followed_artists = self.load_followed_artists()
        
        for followed in followed_artists:
            followed_name = followed.get("artist_name", "").lower()
            followed_id = followed.get("artist_id", "")
            followed_url = followed.get("url", "")
            
            # Extract ID from URL if not directly available
            if not followed_id and followed_url:
                followed_id = self.get_artist_id_from_url(followed_url)
            
            if (artist_name.lower() == followed_name or 
                (spotify_id and followed_id and spotify_id == followed_id)):
                return True
        
        return False
    
    def is_artist_suggested(self, artist_name: str, spotify_id: str = None) -> bool:
        """
        Check if an artist has already been suggested.
        
        Args:
            artist_name: Artist name
            spotify_id: Spotify artist ID (optional)
        
        Returns:
            True if artist is already suggested, False otherwise
        """
        suggestions = self.load_suggestions()
        
        for suggestion in suggestions:
            if (suggestion.get("artist_name", "").lower() == artist_name.lower() or 
                (spotify_id and suggestion.get("spotify_id") == spotify_id)):
                return True
        
        return False
