import json
import glob
import os

# Path to your results files (adjust as needed)
files = glob.glob('src/results/spotify-monthly-listeners-*.json')

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Group by (artist_id, date), keep the entry with the latest timestamp
    latest_per_day = {}
    for entry in data:
        artist_id = entry.get('artist_id')
        date_str = entry.get('date')
        if not artist_id or not date_str:
            continue
        # Split date and time
        if 'T' in date_str:
            date_only = date_str.split('T', 1)[0]
        else:
            date_only = date_str
        key = (artist_id, date_only)
        # Compare timestamps, keep the latest
        if key not in latest_per_day:
            latest_per_day[key] = entry
        else:
            prev_time = latest_per_day[key]['date']
            if prev_time < date_str:
                latest_per_day[key] = entry

    # Convert back to list and sort
    cleaned_list = list(latest_per_day.values())
    cleaned_list.sort(key=lambda x: (x['artist_id'], x['date']))

    # Overwrite the original file
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_list, f, indent=2)

    print(f"Cleaned and overwrote {file}")
