#!/usr/bin/env python3
"""
Deduplication script for Spotify monthly listener data.

This script removes duplicate entries for the same artist on the same date,
keeping the latest entry (by timestamp or position in file).
"""

import json
import os
import shutil
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any

def load_data(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON data from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data: List[Dict[str, Any]], file_path: str) -> None:
    """Save JSON data to file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def analyze_duplicates(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze duplicate entries in the data.
    
    Returns:
        Dictionary with duplicate analysis results
    """
    seen = defaultdict(list)
    duplicates = defaultdict(list)
    
    for i, entry in enumerate(data):
        artist_id = entry.get('artist_id', '')
        date = entry.get('date', '')
        key = f"{artist_id}_{date}"
        
        seen[key].append((i, entry))
        
        if len(seen[key]) > 1:
            duplicates[key] = seen[key]
    
    # Count statistics
    total_entries = len(data)
    duplicate_groups = len(duplicates)
    duplicate_entries = sum(len(group) - 1 for group in duplicates.values())  # Total extras
    
    return {
        'total_entries': total_entries,
        'duplicate_groups': duplicate_groups,
        'duplicate_entries': duplicate_entries,
        'clean_entries': total_entries - duplicate_entries,
        'duplicates': duplicates
    }

def deduplicate_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicates, keeping the latest entry for each artist-date combination.
    
    Strategy: Keep the entry that appears later in the file (higher index)
    as it's likely more recent.
    """
    seen = {}
    clean_data = []
    
    # Process entries in reverse order to keep the latest ones
    for i in reversed(range(len(data))):
        entry = data[i]
        artist_id = entry.get('artist_id', '')
        date = entry.get('date', '')
        key = f"{artist_id}_{date}"
        
        # If we haven't seen this artist-date combo yet, keep it
        if key not in seen:
            seen[key] = True
            clean_data.append(entry)
    
    # Reverse back to original order
    clean_data.reverse()
    return clean_data

def backup_file(file_path: str) -> str:
    """Create a backup of the original file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def main():
    """Main deduplication process."""
    # File paths
    master_file = os.path.join('..', 'data', 'results', 'spotify-monthly-listeners-master.json')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    master_file = os.path.join(script_dir, master_file)
    
    if not os.path.exists(master_file):
        print(f"❌ Error: Master file not found at {master_file}")
        return
    
    print("🔍 Analyzing duplicates in master file...")
    
    # Load data
    try:
        data = load_data(master_file)
        print(f"📊 Loaded {len(data)} entries from master file")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Analyze duplicates
    analysis = analyze_duplicates(data)
    
    print("\n📈 Duplicate Analysis Results:")
    print(f"   Total entries: {analysis['total_entries']:,}")
    print(f"   Duplicate groups: {analysis['duplicate_groups']:,}")
    print(f"   Duplicate entries to remove: {analysis['duplicate_entries']:,}")
    print(f"   Clean entries after dedup: {analysis['clean_entries']:,}")
    
    if analysis['duplicate_entries'] == 0:
        print("✅ No duplicates found! Data is already clean.")
        return
    
    # Show some example duplicates
    print("\n🔍 Example duplicate groups:")
    count = 0
    for key, group in analysis['duplicates'].items():
        if count >= 5:  # Show max 5 examples
            break
        
        first_entry = group[0]
        artist_name = first_entry[1].get('artist_name', 'Unknown')
        date = first_entry[1].get('date', 'Unknown')
        listeners = [item[1].get('monthly_listeners', 0) for item in group]
        
        print(f"   {artist_name} on {date}: {len(group)} entries with listeners: {listeners}")
        count += 1
    
    if analysis['duplicate_groups'] > 5:
        print(f"   ... and {analysis['duplicate_groups'] - 5} more duplicate groups")
    
    # Ask for confirmation
    print(f"\n⚠️  This will remove {analysis['duplicate_entries']} duplicate entries.")
    print("   Strategy: Keep the latest entry for each artist-date combination")
    
    response = input("\n🤔 Proceed with deduplication? (y/n): ").lower().strip()
    if response not in ['y', 'yes']:
        print("❌ Deduplication cancelled.")
        return
    
    # Create backup
    print("\n💾 Creating backup...")
    try:
        backup_path = backup_file(master_file)
        print(f"✅ Backup created: {backup_path}")
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return
    
    # Deduplicate
    print("🧹 Deduplicating data...")
    try:
        clean_data = deduplicate_data(data)
        print(f"✅ Deduplicated: {len(data)} → {len(clean_data)} entries")
    except Exception as e:
        print(f"❌ Error during deduplication: {e}")
        return
    
    # Save clean data
    print("💾 Saving cleaned data...")
    try:
        save_data(clean_data, master_file)
        print(f"✅ Saved cleaned data to {master_file}")
    except Exception as e:
        print(f"❌ Error saving cleaned data: {e}")
        print(f"🔄 Restore from backup: {backup_path}")
        return
    
    # Final verification
    print("\n🔍 Verifying cleanup...")
    verification = analyze_duplicates(clean_data)
    
    if verification['duplicate_entries'] == 0:
        print("✅ Cleanup successful! No duplicates remain.")
        print(f"📊 Final count: {len(clean_data):,} clean entries")
        
        # Show cleanup summary
        removed = len(data) - len(clean_data)
        print(f"\n📈 Cleanup Summary:")
        print(f"   Original entries: {len(data):,}")
        print(f"   Removed duplicates: {removed:,}")
        print(f"   Final entries: {len(clean_data):,}")
        print(f"   Space saved: {(removed / len(data) * 100):.1f}%")
        
    else:
        print("⚠️  Warning: Some duplicates may still remain.")
        print(f"   Remaining duplicates: {verification['duplicate_entries']}")

if __name__ == "__main__":
    main()
