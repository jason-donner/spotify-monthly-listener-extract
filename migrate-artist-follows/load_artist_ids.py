import json
import os

def load_artist_ids(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Support both list and dict with 'artists' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'artists' in data:
        return data['artists']
    else:
        return []

if __name__ == "__main__":
    ids = load_artist_ids('src/results/spotify-followed-artists-master.json')
    print(ids[:5])
    print(f"Total artists: {len(ids)}")
    # Always save artists.json in the same folder as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, 'artists.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(ids, f, indent=2)  # Save as a simple list