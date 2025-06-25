#!/usr/bin/env python3
"""
Quick test script to debug the webapp issues.
"""

import sys
import os

# Add the webapp directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'webapp'))

# Test imports
try:
    from app.services.spotify_service import SpotifyService
    from app.services.data_service import DataService  
    from app.config import Config
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test configuration
try:
    Config.validate()
    print("✅ Configuration validation passed")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    sys.exit(1)

# Test data service
try:
    data_service = DataService(
        data_path=Config.DATA_PATH,
        followed_artists_path=Config.FOLLOWED_ARTISTS_PATH,
        suggestions_file=Config.SUGGESTIONS_FILE,
        blacklist_file=Config.BLACKLIST_FILE
    )
    
    data = data_service.load_data()
    print(f"✅ Data loaded successfully: {len(data)} records")
    
    if data:
        first_record = data[0]
        print(f"   Sample record: {first_record}")
        
        # Test artist history
        artist_id = first_record.get('artist_id')
        if artist_id:
            history = data_service.get_artist_history(artist_id)
            print(f"   Artist history for {artist_id}: {len(history)} entries")
        
except Exception as e:
    print(f"❌ Data service error: {e}")
    import traceback
    traceback.print_exc()

# Test Spotify service
try:
    spotify_service = SpotifyService(
        client_id=Config.SPOTIFY_CLIENT_ID,
        client_secret=Config.SPOTIFY_CLIENT_SECRET,
        redirect_uri=Config.SPOTIFY_REDIRECT_URI,
        scope=Config.SPOTIFY_SCOPE
    )
    
    # Test public client
    public_client = spotify_service.get_public_client()
    if public_client:
        print("✅ Spotify public client created successfully")
        
        # Test artist info fetch
        test_artist_id = "00ZAzYrqrlsYdohYbZcSAO"  # ChurchKey
        artist_info = spotify_service.get_artist_info(test_artist_id)
        print(f"   Artist info for {test_artist_id}: {artist_info}")
        
        # Test image fetch
        image_url = spotify_service.fetch_artist_image(test_artist_id)
        print(f"   Artist image URL: {image_url}")
        
        # Test top tracks
        top_tracks = spotify_service.get_top_tracks(test_artist_id)
        print(f"   Top tracks for {test_artist_id}: {len(top_tracks)} tracks")
        if top_tracks:
            print(f"     First track: {top_tracks[0]}")
        
    else:
        print("❌ Failed to create Spotify public client")
        
except Exception as e:
    print(f"❌ Spotify service error: {e}")
    import traceback
    traceback.print_exc()

print("Test complete!")
