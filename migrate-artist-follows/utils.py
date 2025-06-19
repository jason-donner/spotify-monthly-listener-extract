import json
import re

def load_artist_ids(json_path):
    """
    Loads a list of artist IDs from a JSON file.
    Expects the JSON to be a list of dicts with a 'url' key.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Extract artist ID from the URL
    ids = []
    for entry in data:
        if isinstance(entry, dict) and "url" in entry:
            # Extract the ID from the URL
            match = re.search(r"artist/([a-zA-Z0-9]+)", entry["url"])
            if match:
                ids.append(match.group(1))
    return ids