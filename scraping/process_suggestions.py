"""
Process Artist Suggestions
--------------------------
This script processes approved artist suggestions from the web app and either:
1. Follows them on Spotify (if configured to do so)
2. Adds them to a special tracking list for monitoring without following

This should be run as part of the monthly listener workflow to incorporate
user-suggested artists into the monitoring system.
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables
load_dotenv()

def setup_logging():
    """Configure logging for this script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler('process_suggestions.log'),
            logging.StreamHandler()
        ]
    )

def load_suggestions():
    """Load artist suggestions from the web app."""
    suggestions_file = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "webapp", 
        "artist_suggestions.json"
    )
    
    if not os.path.exists(suggestions_file):
        logging.info("No suggestions file found")
        return []
    
    try:
        with open(suggestions_file, 'r', encoding='utf-8') as f:
            suggestions = json.load(f)
            # Return suggestions that are admin-approved for following or tracking
            return [s for s in suggestions if s.get('admin_approved') == True and s.get('status') in ['approved_for_follow', 'approved_for_tracking']]
    except Exception as e:
        logging.error(f"Error loading suggestions: {e}")
        return []

def load_followed_artists():
    """Load the current followed artists master list."""
    followed_file = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "data", 
        "results", 
        "spotify-followed-artists-master.json"
    )
    
    if not os.path.exists(followed_file):
        logging.warning("No followed artists file found")
        return []
    
    try:
        with open(followed_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading followed artists: {e}")
        return []

def save_followed_artists(artists):
    """Save the updated followed artists list."""
    followed_file = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "data", 
        "results", 
        "spotify-followed-artists-master.json"
    )
    
    try:
        with open(followed_file, 'w', encoding='utf-8') as f:
            json.dump(artists, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved {len(artists)} artists to followed list")
    except Exception as e:
        logging.error(f"Error saving followed artists: {e}")

def follow_artist_on_spotify(sp, artist_id):
    """Follow an artist on Spotify."""
    try:
        sp.user_follow_artists([artist_id])
        logging.info(f"Successfully followed artist {artist_id} on Spotify")
        return True
    except Exception as e:
        logging.error(f"Error following artist {artist_id}: {e}")
        return False

def update_suggestions_status(suggestions_to_update):
    """Mark suggestions as processed."""
    suggestions_file = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "webapp", 
        "artist_suggestions.json"
    )
    
    if not os.path.exists(suggestions_file):
        return
    
    try:
        with open(suggestions_file, 'r', encoding='utf-8') as f:
            all_suggestions = json.load(f)
        
        # Mark processed suggestions
        processed_ids = {s.get('spotify_id') for s in suggestions_to_update}
        processed_names = {s.get('artist_name', '').lower() for s in suggestions_to_update}
        
        for suggestion in all_suggestions:
            if (suggestion.get('spotify_id') in processed_ids or 
                suggestion.get('artist_name', '').lower() in processed_names):
                suggestion['status'] = 'processed'
                suggestion['processed_date'] = datetime.now().isoformat()
        
        with open(suggestions_file, 'w', encoding='utf-8') as f:
            json.dump(all_suggestions, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Marked {len(suggestions_to_update)} suggestions as processed")
        
    except Exception as e:
        logging.error(f"Error updating suggestions status: {e}")

def process_suggestions(auto_follow=False):
    """
    Process admin-approved artist suggestions.
    
    Args:
        auto_follow (bool): If True, automatically follow artists approved for following
    """
    logging.info("Starting to process artist suggestions")
    
    suggestions = load_suggestions()
    if not suggestions:
        logging.info("No admin-approved suggestions to process")
        return
    
    logging.info(f"Found {len(suggestions)} admin-approved suggestions")
    
    followed_artists = load_followed_artists()
    followed_ids = {artist.get('artist_id') for artist in followed_artists}
    followed_names = {artist.get('artist_name', '').lower() for artist in followed_artists}
    
    # Initialize Spotify client for auto-following
    sp = None
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
            scope="user-follow-modify user-follow-read"
        ))
        logging.info("Spotify client initialized")
    except Exception as e:
        logging.error(f"Error initializing Spotify client: {e}")
        sp = None
    
    new_artists_added = 0
    already_followed = 0
    followed_count = 0
    suggestions_to_process = []  # Track all suggestions we process (including already followed ones)
    
    for suggestion in suggestions:
        artist_name = suggestion.get('artist_name', '')
        artist_id = suggestion.get('spotify_id', '')
        artist_url = suggestion.get('spotify_url', '')
        should_follow = suggestion.get('status') == 'approved_for_follow'
        
        # Add to list of suggestions to mark as processed
        suggestions_to_process.append(suggestion)
        
        # Skip if already in followed list
        if (artist_id and artist_id in followed_ids) or (artist_name.lower() in followed_names):
            logging.info(f"Artist '{artist_name}' is already in followed list")
            already_followed += 1
            continue
        
        # Add to followed list
        new_artist = {
            "artist_name": artist_name,
            "artist_id": artist_id,
            "url": artist_url,
            "source": "admin_approved",
            "date_added": datetime.now().strftime("%Y-%m-%d"),
            "auto_followed": False,
            "removed": False
        }
        
        # Try to follow on Spotify if approved for following
        if should_follow and sp and artist_id:
            if follow_artist_on_spotify(sp, artist_id):
                new_artist["auto_followed"] = True
                new_artist["source"] = "admin_followed"
                followed_count += 1
        
        followed_artists.append(new_artist)
        new_artists_added += 1
        logging.info(f"Added '{artist_name}' to tracking list (follow: {should_follow and new_artist['auto_followed']})")
    
    # Save followed artists if we added new ones
    if new_artists_added > 0:
        save_followed_artists(followed_artists)
    
    # Always mark processed suggestions (even if already followed)
    if suggestions_to_process:
        update_suggestions_status(suggestions_to_process)
        logging.info(f"Processing complete: {new_artists_added} new artists added, {followed_count} followed on Spotify, {already_followed} already in list")
    else:
        logging.info("No suggestions to process")

def main():
    """Main function."""
    setup_logging()
    
    # Process admin-approved suggestions (auto_follow parameter is now ignored 
    # since the decision is made in the admin panel)
    process_suggestions()

if __name__ == "__main__":
    main()
