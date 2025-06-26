#!/usr/bin/env python3
"""
Check for and fix duplicates in the master listeners file
"""

import json
import os
from collections import defaultdict

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    master_file = os.path.join(base_dir, "data", "results", "spotify-monthly-listeners-master.json")
    
    print("🔍 Checking for duplicates in master listeners file...")
    
    if not os.path.exists(master_file):
        print("❌ Master file not found!")
        return
    
    with open(master_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 Total entries: {len(data)}")
    
    # Group by artist_id and date to find duplicates
    duplicates = defaultdict(list)
    for i, entry in enumerate(data):
        key = (entry.get('artist_id'), entry.get('date'))
        duplicates[key].append((i, entry))
    
    # Find actual duplicates
    actual_duplicates = {k: v for k, v in duplicates.items() if len(v) > 1}
    
    if not actual_duplicates:
        print("✅ No duplicates found! Data is clean.")
        return
    
    print(f"🚨 Found {len(actual_duplicates)} sets of duplicates:")
    
    total_duplicate_entries = 0
    for key, entries in actual_duplicates.items():
        artist_id, date = key
        artist_name = entries[0][1].get('artist_name', 'Unknown')
        print(f"  - {artist_name} ({artist_id}) on {date}: {len(entries)} entries")
        total_duplicate_entries += len(entries) - 1  # Count extras only
    
    print(f"📈 Total duplicate entries to remove: {total_duplicate_entries}")
    
    # Ask for confirmation
    response = input("\n🔧 Do you want to remove duplicates, keeping the latest entry for each artist/date? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cancelled.")
        return
    
    # Create backup
    backup_file = master_file + f".backup.before_dedup"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Created backup: {backup_file}")
    
    # Keep only the latest entry for each duplicate set (last in the list)
    cleaned_data = []
    processed_keys = set()
    
    for i, entry in enumerate(data):
        key = (entry.get('artist_id'), entry.get('date'))
        
        if key in actual_duplicates:
            if key not in processed_keys:
                # Keep the last occurrence of this duplicate
                last_entry = actual_duplicates[key][-1][1]
                cleaned_data.append(last_entry)
                processed_keys.add(key)
                print(f"  ✅ Kept latest entry for {last_entry.get('artist_name', 'Unknown')} on {entry.get('date')}")
        else:
            # Not a duplicate, keep as-is
            cleaned_data.append(entry)
    
    # Save cleaned data
    with open(master_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    
    removed_count = len(data) - len(cleaned_data)
    print(f"\n🎉 Deduplication complete!")
    print(f"  - Original entries: {len(data)}")
    print(f"  - Cleaned entries: {len(cleaned_data)}")
    print(f"  - Removed duplicates: {removed_count}")
    print(f"  - Backup saved to: {backup_file}")

if __name__ == "__main__":
    main()
