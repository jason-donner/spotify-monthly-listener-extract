import json
import os

os.chdir('data/results')

# Check both files for today - different naming formats!
file1 = 'spotify-monthly-listeners-2025-06-25.json'
file2 = 'spotify-monthly-listeners-20250625.json'

print("=== COMPARING TWO TODAY FILES ===")
for filename in [file1, file2]:
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f'{filename}: {len(data)} entries')
        if data:
            print(f'  First entry date: {data[0].get("date", "Unknown")}')
            print(f'  Last entry date: {data[-1].get("date", "Unknown")}')
    else:
        print(f'{filename}: Not found')

print("\n=== CHECKING MASTER FILE FOR DUPLICATES ===")
# Check master file for duplicates on today's date
master_file = 'spotify-monthly-listeners-master.json'
today = '2025-06-25'

if os.path.exists(master_file):
    with open(master_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f'Total entries in master file: {len(data)}')
    
    # Filter entries for today (both date formats)
    today_entries = [entry for entry in data if entry.get('date', '').startswith(today)]
    print(f'Entries for {today}: {len(today_entries)}')
    
    # Group today's entries by artist_id
    artist_counts = {}
    for entry in today_entries:
        artist_id = entry.get('artist_id')
        artist_name = entry.get('artist_name', 'Unknown')
        if artist_id:
            if artist_id not in artist_counts:
                artist_counts[artist_id] = {'name': artist_name, 'count': 0, 'times': []}
            artist_counts[artist_id]['count'] += 1
            artist_counts[artist_id]['times'].append(entry.get('date'))
    
    # Find artists with multiple entries today
    duplicates = {k: v for k, v in artist_counts.items() if v['count'] > 1}
    
    print(f'Artists with multiple entries today: {len(duplicates)}')
    if duplicates:
        print('First 10 duplicates:')
        count = 0
        for artist_id, info in duplicates.items():
            print(f'  {info["name"]} ({artist_id}): {info["count"]} entries')
            for time in info["times"]:
                print(f'    - {time}')
            count += 1
            if count >= 10:
                break
else:
    print('Master file not found')
