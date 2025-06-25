import json
import os
from datetime import datetime

def dedupe_and_merge():
    """Deduplicate data files and merge both date formats properly."""
    
    os.chdir('data/results')
    
    # Files to process
    file1 = 'spotify-monthly-listeners-2025-06-25.json'
    file2 = 'spotify-monthly-listeners-20250625.json'
    master_file = 'spotify-monthly-listeners-master.json'
    
    print("=== LOADING FILES ===")
    
    # Load all data
    all_data = []
    
    # Load master file
    if os.path.exists(master_file):
        with open(master_file, 'r', encoding='utf-8') as f:
            master_data = json.load(f)
        print(f'Master file: {len(master_data)} entries')
        all_data.extend(master_data)
    
    # Load today's files (if they're not already in master)
    for filename in [file1, file2]:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                daily_data = json.load(f)
            print(f'{filename}: {len(daily_data)} entries')
            
            # Normalize date format to YYYY-MM-DD format
            for entry in daily_data:
                date_str = entry.get('date', '')
                if len(date_str) == 8 and date_str.isdigit():  # YYYYMMDD format
                    # Convert YYYYMMDD to YYYY-MM-DD
                    year = date_str[:4]
                    month = date_str[4:6]
                    day = date_str[6:8]
                    entry['date'] = f'{year}-{month}-{day}'
            
            all_data.extend(daily_data)
    
    print(f'Total entries before deduplication: {len(all_data)}')
    
    # Deduplicate by (artist_id, date) - keep the entry with the most complete data
    print("\n=== DEDUPLICATING ===")
    unique_entries = {}
    
    for entry in all_data:
        artist_id = entry.get('artist_id')
        date_str = entry.get('date', '')
        
        if not artist_id or not date_str:
            continue
        
        # Normalize date to just YYYY-MM-DD (remove time if present)
        if 'T' in date_str:
            date_only = date_str.split('T')[0]
        else:
            date_only = date_str
        
        key = (artist_id, date_only)
        
        if key not in unique_entries:
            # First entry for this artist/date combination
            unique_entries[key] = entry
        else:
            # Compare entries and keep the better one
            existing = unique_entries[key]
            
            # Prefer entries with more fields or more recent timestamps
            existing_fields = len([v for v in existing.values() if v])
            new_fields = len([v for v in entry.values() if v])
            
            if new_fields > existing_fields:
                unique_entries[key] = entry
            elif new_fields == existing_fields:
                # If same number of fields, prefer the one with timestamp (more recent)
                if 'T' in entry.get('date', '') and 'T' not in existing.get('date', ''):
                    unique_entries[key] = entry
                elif 'T' in entry.get('date', '') and 'T' in existing.get('date', ''):
                    # Both have timestamps, keep the later one
                    if entry.get('date', '') > existing.get('date', ''):
                        unique_entries[key] = entry
    
    # Convert back to list and sort
    deduplicated_data = list(unique_entries.values())
    deduplicated_data.sort(key=lambda x: (x.get('artist_id', ''), x.get('date', '')))
    
    print(f'Total entries after deduplication: {len(deduplicated_data)}')
    print(f'Removed {len(all_data) - len(deduplicated_data)} duplicates')
    
    # Backup the original master file
    if os.path.exists(master_file):
        backup_name = f'{master_file}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.rename(master_file, backup_name)
        print(f'Backed up original master to: {backup_name}')
    
    # Save the deduplicated data as the new master
    with open(master_file, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_data, f, indent=2)
    
    print(f'Saved deduplicated data to: {master_file}')
    
    # Check the results
    print("\n=== VERIFICATION ===")
    today = '2025-06-25'
    today_entries = [entry for entry in deduplicated_data if entry.get('date', '').startswith(today)]
    print(f'Entries for {today} after deduplication: {len(today_entries)}')
    
    # Check for any remaining duplicates
    artist_counts = {}
    for entry in today_entries:
        artist_id = entry.get('artist_id')
        if artist_id:
            artist_counts[artist_id] = artist_counts.get(artist_id, 0) + 1
    
    duplicates = {k: v for k, v in artist_counts.items() if v > 1}
    print(f'Artists with multiple entries today after dedup: {len(duplicates)}')
    
    if duplicates:
        print('Remaining duplicates:')
        for artist_id, count in list(duplicates.items())[:5]:
            # Find artist name
            for entry in today_entries:
                if entry.get('artist_id') == artist_id:
                    artist_name = entry.get('artist_name', 'Unknown')
                    break
            print(f'  {artist_name} ({artist_id}): {count} entries')

if __name__ == "__main__":
    dedupe_and_merge()
