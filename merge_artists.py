"""
merge_artists.py
---------------
Merges followed artists from Spotify with approved artist suggestions from the web app.
Creates a unified master list for scraping with source tracking.
"""

import os
import json
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Set


def setup_logging(log_file: str):
    """Configure logging to file for this script."""
    logging.basicConfig(
        filename=log_file,
        filemode='a',
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO
    )


def load_followed_artists(file_path: str) -> List[Dict]:
    """Load the followed artists from the master file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            artists = json.load(f)
        logging.info(f"Loaded {len(artists)} followed artists from {file_path}")
        return artists
    except FileNotFoundError:
        logging.warning(f"Followed artists file not found: {file_path}")
        return []
    except Exception as e:
        logging.error(f"Error loading followed artists: {e}")
        return []


def load_approved_suggestions(file_path: str) -> List[Dict]:
    """Load approved artist suggestions from the web app."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            suggestions = json.load(f)
        
        # Filter only approved suggestions
        approved = [s for s in suggestions if s.get('status') == 'approved']
        logging.info(f"Loaded {len(approved)} approved suggestions from {file_path}")
        return approved
    except FileNotFoundError:
        logging.warning(f"Suggestions file not found: {file_path}")
        return []
    except Exception as e:
        logging.error(f"Error loading suggestions: {e}")
        return []


def extract_artist_id_from_url(url: str) -> str:
    """Extract artist ID from Spotify URL."""
    if not url:
        return ""
    return url.rstrip('/').split('/')[-1]


def normalize_artist_for_comparison(artist_data: Dict) -> Dict:
    """Normalize artist data for duplicate detection."""
    # Extract artist ID from URL for comparison
    url = artist_data.get('url') or artist_data.get('spotify_url', '')
    artist_id = extract_artist_id_from_url(url)
    name = artist_data.get('artist_name', '').lower().strip()
    
    return {
        'name': name,
        'id': artist_id,
        'original': artist_data
    }


def merge_artists(followed_artists: List[Dict], approved_suggestions: List[Dict]) -> List[Dict]:
    """Merge followed artists with approved suggestions, avoiding duplicates."""
    merged_artists = []
    seen_ids: Set[str] = set()
    seen_names: Set[str] = set()
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # First, add all followed artists
    for artist in followed_artists:
        normalized = normalize_artist_for_comparison(artist)
        
        # Create unified format for followed artists
        unified_artist = {
            "artist_name": artist.get("artist_name", ""),
            "artist_id": extract_artist_id_from_url(artist.get("url", "")),
            "url": artist.get("url", ""),
            "source": "followed",
            "date_added": artist.get("date_added", current_date),
            "removed": artist.get("removed", False)
        }
        
        merged_artists.append(unified_artist)
        
        # Track for duplicate detection
        if normalized['id']:
            seen_ids.add(normalized['id'])
        if normalized['name']:
            seen_names.add(normalized['name'])
    
    # Then, add approved suggestions that aren't duplicates
    suggestions_added = 0
    suggestions_skipped = 0
    
    print(f"🔍 Processing {len(approved_suggestions)} approved suggestions...")
    
    for suggestion in approved_suggestions:
        normalized = normalize_artist_for_comparison(suggestion)
        
        # Check for duplicates
        is_duplicate = False
        duplicate_reason = ""
        
        if normalized['id'] and normalized['id'] in seen_ids:
            is_duplicate = True
            duplicate_reason = f"by ID ({normalized['id']})"
            logging.info(f"Skipping duplicate suggestion (by ID): {suggestion.get('artist_name')}")
        elif normalized['name'] and normalized['name'] in seen_names:
            is_duplicate = True
            duplicate_reason = f"by name ({normalized['name']})"
            logging.info(f"Skipping duplicate suggestion (by name): {suggestion.get('artist_name')}")
        
        if not is_duplicate:
            # Create unified format for suggestions
            unified_artist = {
                "artist_name": suggestion.get("artist_name", ""),
                "artist_id": suggestion.get("spotify_id", ""),
                "url": suggestion.get("spotify_url", ""),
                "source": "suggestion",
                "date_added": current_date,
                "removed": False,
                "suggestion_timestamp": suggestion.get("timestamp"),
                "suggestion_id": suggestion.get("spotify_id")  # Use spotify_id as suggestion identifier
            }
            
            merged_artists.append(unified_artist)
            suggestions_added += 1
            print(f"   ✅ Added: {suggestion.get('artist_name')}")
            
            # Track to prevent future duplicates
            if normalized['id']:
                seen_ids.add(normalized['id'])
            if normalized['name']:
                seen_names.add(normalized['name'])
        else:
            suggestions_skipped += 1
            print(f"   ⚠️  Skipped: {suggestion.get('artist_name')} (duplicate {duplicate_reason})")
    
    print()
    
    logging.info(f"Merge complete: {len(followed_artists)} followed + {suggestions_added} suggestions = {len(merged_artists)} total")
    logging.info(f"Skipped {suggestions_skipped} duplicate suggestions")
    
    return merged_artists


def save_merged_artists(artists: List[Dict], output_path: str, backup: bool = True):
    """Save the merged artist list to file with optional backup."""
    
    # Create backup if requested and file exists
    if backup and os.path.exists(output_path):
        backup_path = f"{output_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            os.rename(output_path, backup_path)
            logging.info(f"Created backup: {backup_path}")
        except Exception as e:
            logging.warning(f"Could not create backup: {e}")
    
    # Save merged data
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(artists, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved {len(artists)} merged artists to {output_path}")
    except Exception as e:
        logging.error(f"Error saving merged artists: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description='Merge followed artists with approved suggestions')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup of existing master file')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be merged without saving')
    args = parser.parse_args()
    
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, 'src', 'results')
    web_app_dir = os.path.join(script_dir, 'app', 'spotify-listener-tracker')
    
    followed_artists_path = os.path.join(results_dir, 'spotify-followed-artists-master.json')
    suggestions_path = os.path.join(web_app_dir, 'artist_suggestions.json')
    output_path = followed_artists_path  # Overwrite the master file
    log_file = os.path.join(script_dir, 'merge_artists.log')
    
    # Setup logging
    setup_logging(log_file)
    logging.info("=" * 50)
    logging.info("Starting artist merge process")
    
    print("🎵 Spotify Artist Merge Tool")
    print("=" * 40)
    print(f"📁 Followed artists: {followed_artists_path}")
    print(f"💡 Suggestions: {suggestions_path}")
    print(f"📝 Output: {output_path}")
    print(f"📋 Log: {log_file}")
    print()
    
    # Load data
    print("Loading data...")
    followed_artists = load_followed_artists(followed_artists_path)
    approved_suggestions = load_approved_suggestions(suggestions_path)
    
    if not followed_artists and not approved_suggestions:
        print("❌ No data found to merge!")
        return
    
    print(f"✅ Found {len(followed_artists)} followed artists")
    print(f"✅ Found {len(approved_suggestions)} approved suggestions")
    print()
    
    # Merge data
    print("Merging artists...")
    merged_artists = merge_artists(followed_artists, approved_suggestions)
    
    # Show summary
    followed_count = len([a for a in merged_artists if a['source'] == 'followed'])
    suggestion_count = len([a for a in merged_artists if a['source'] == 'suggestion'])
    
    print(f"📊 Merge Summary:")
    print(f"   • Followed artists: {followed_count}")
    print(f"   • Suggested artists: {suggestion_count}")
    print(f"   • Total artists: {len(merged_artists)}")
    print()
    
    if suggestion_count > 0:
        print("🆕 New suggested artists:")
        for artist in merged_artists:
            if artist['source'] == 'suggestion':
                print(f"   • {artist['artist_name']}")
        print()
    
    # Save or dry run
    if args.dry_run:
        print("🔍 DRY RUN: Would save merged data (use without --dry-run to actually save)")
    else:
        print("Saving merged artist list...")
        save_merged_artists(merged_artists, output_path, backup=not args.no_backup)
        print("✅ Merge complete!")
    
    logging.info("Artist merge process completed")


if __name__ == "__main__":
    main()
