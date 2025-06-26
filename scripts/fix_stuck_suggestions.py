#!/usr/bin/env python3
"""
Fix Stuck Suggestions Migration Script
-------------------------------------
This script fixes suggestions that are stuck in limbo - approved but not marked as followed.
It handles suggestions that were approved before the auto-follow functionality was implemented.
"""

import json
import os
import sys
from datetime import datetime

def load_json_file(file_path):
    """Load JSON file or return empty list if file doesn't exist."""
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def save_json_file(file_path, data):
    """Save data to JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    # File paths
    suggestions_file = os.path.join(base_dir, "webapp", "artist_suggestions.json")
    followed_artists_file = os.path.join(base_dir, "data", "results", "spotify-followed-artists-master.json")
    
    print("🔧 Fixing stuck suggestions...")
    print(f"Suggestions file: {suggestions_file}")
    print(f"Followed artists file: {followed_artists_file}")
    
    # Load data
    suggestions = load_json_file(suggestions_file)
    followed_artists = load_json_file(followed_artists_file)
    
    if not suggestions:
        print("No suggestions found or unable to load suggestions file")
        return
    
    # Find stuck suggestions (approved but not marked as followed)
    stuck_suggestions = []
    for suggestion in suggestions:
        if (suggestion.get("status") == "approved" and 
            not suggestion.get("already_followed") and 
            not suggestion.get("admin_action_date")):
            stuck_suggestions.append(suggestion)
    
    if not stuck_suggestions:
        print("✅ No stuck suggestions found - all approved suggestions are properly processed!")
        return
    
    print(f"\n🔍 Found {len(stuck_suggestions)} stuck suggestion(s):")
    for suggestion in stuck_suggestions:
        print(f"  - {suggestion.get('artist_name', 'Unknown')} (ID: {suggestion.get('spotify_id', 'N/A')})")
    
    # Get existing followed artist IDs for duplicate checking
    existing_artist_ids = {artist.get("artist_id") for artist in followed_artists if artist.get("artist_id")}
    
    # Process each stuck suggestion
    fixed_count = 0
    added_to_followed = 0
    
    for suggestion in stuck_suggestions:
        artist_name = suggestion.get("artist_name", "Unknown")
        spotify_id = suggestion.get("spotify_id")
        spotify_url = suggestion.get("spotify_url")
        
        print(f"\n🔧 Processing: {artist_name}")
        
        # Mark suggestion as properly processed
        suggestion["already_followed"] = True
        suggestion["admin_action_date"] = datetime.now().isoformat()
        fixed_count += 1
        
        # Add to followed artists if not already there
        if spotify_id and spotify_id not in existing_artist_ids:
            new_artist = {
                "artist_name": artist_name,
                "artist_id": spotify_id,
                "url": spotify_url if spotify_url else f"https://open.spotify.com/artist/{spotify_id}",
                "source": "migration_fix",
                "date_added": datetime.now().strftime("%Y-%m-%d"),
                "removed": False
            }
            followed_artists.append(new_artist)
            existing_artist_ids.add(spotify_id)
            added_to_followed += 1
            print(f"  ✅ Added to followed artists")
        elif spotify_id:
            print(f"  ℹ️ Already in followed artists list")
        else:
            print(f"  ⚠️ No Spotify ID - only marked as processed")
    
    # Save updated files
    print(f"\n💾 Saving changes...")
    
    if save_json_file(suggestions_file, suggestions):
        print(f"  ✅ Updated suggestions file")
    else:
        print(f"  ❌ Failed to update suggestions file")
        return
    
    if save_json_file(followed_artists_file, followed_artists):
        print(f"  ✅ Updated followed artists file")
    else:
        print(f"  ❌ Failed to update followed artists file")
        return
    
    # Summary
    print(f"\n🎉 Migration complete!")
    print(f"  - Fixed {fixed_count} stuck suggestion(s)")
    print(f"  - Added {added_to_followed} artist(s) to followed list")
    print(f"  - All approved suggestions are now properly processed")

if __name__ == "__main__":
    main()
