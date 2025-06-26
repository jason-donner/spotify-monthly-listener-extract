#!/usr/bin/env python3
"""
Clean test artists from all result files.
This script removes test artists from:
- Daily results files
- Master results file
- Followed artists file
"""

import json
import os
import shutil
from datetime import datetime

# Test artist identifiers to remove
TEST_ARTISTS = {
    "1234567890ABCDEF",  # Fake test ID
    "4CJ5eNfmJHQ5spEAvaxj8F"  # worlds greatest dad (if this is a test)
}

TEST_ARTIST_NAMES = {
    "Test Artist Unique",
    "worlds greatest dad"
}

def backup_file(filepath):
    """Create a backup of the file before modifying"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup.{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"Created backup: {backup_path}")
    return backup_path

def clean_monthly_listeners_file(filepath):
    """Remove test artists from a monthly listeners file"""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    print(f"Cleaning {filepath}...")
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data)
    cleaned_data = []
    
    for entry in data:
        artist_id = entry.get('artist_id', '')
        artist_name = entry.get('artist_name', '')
        
        if artist_id not in TEST_ARTISTS and artist_name not in TEST_ARTIST_NAMES:
            cleaned_data.append(entry)
        else:
            print(f"  Removed: {artist_name} ({artist_id})")
    
    removed_count = original_count - len(cleaned_data)
    print(f"  Removed {removed_count} entries out of {original_count}")
    
    if removed_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        print(f"  Updated {filepath}")

def clean_followed_artists_file(filepath):
    """Remove test artists from the followed artists file"""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    print(f"Cleaning {filepath}...")
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data)
    cleaned_data = []
    
    for entry in data:
        artist_id = entry.get('artist_id', '')
        artist_name = entry.get('artist_name', '')
        
        if artist_id not in TEST_ARTISTS and artist_name not in TEST_ARTIST_NAMES:
            cleaned_data.append(entry)
        else:
            print(f"  Removed: {artist_name} ({artist_id})")
    
    removed_count = original_count - len(cleaned_data)
    print(f"  Removed {removed_count} entries out of {original_count}")
    
    if removed_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        print(f"  Updated {filepath}")

def main():
    """Main function to clean all files"""
    results_dir = "src/results"
    
    # Clean all daily files
    print("=== Cleaning daily listener files ===")
    for filename in os.listdir(results_dir):
        if filename.startswith("spotify-monthly-listeners-") and filename.endswith(".json") and "master" not in filename:
            filepath = os.path.join(results_dir, filename)
            clean_monthly_listeners_file(filepath)
    
    # Clean master listener file
    print("\n=== Cleaning master listener file ===")
    master_file = os.path.join(results_dir, "spotify-monthly-listeners-master.json")
    clean_monthly_listeners_file(master_file)
    
    # Clean followed artists file
    print("\n=== Cleaning followed artists file ===")
    followed_file = os.path.join(results_dir, "spotify-followed-artists-master.json")
    clean_followed_artists_file(followed_file)
    
    print("\n=== Cleanup completed ===")

if __name__ == "__main__":
    main()
