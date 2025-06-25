import json
import re
import os

# Path to the master file
MASTER_PATH = os.path.join(os.path.dirname(__file__), 'results', 'spotify-monthly-listeners-master.json')

def extract_artist_id(url):
    match = re.search(r"artist/([a-zA-Z0-9]+)", url)
    return match.group(1) if match else None

def fix_artist_ids(input_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    updated = 0
    cleaned = []
    for record in data:
        if not record.get('artist_id'):
            artist_url = record.get('url', '')
            artist_id = extract_artist_id(artist_url)
            if artist_id:
                record['artist_id'] = artist_id
                updated += 1
        if record.get('monthly_listeners', 0) != 0:
            cleaned.append(record)
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f"Updated {updated} records and removed {len(data) - len(cleaned)} zero-listener records. Overwrote {input_path}")

if __name__ == "__main__":
    fix_artist_ids(MASTER_PATH)
