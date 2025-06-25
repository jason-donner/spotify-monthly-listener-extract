def load_json_data(filepath):
    import json
    with open(filepath, 'r') as file:
        return json.load(file)

def search_artist(data, artist_name):
    results = []
    for record in data:
        if artist_name.lower() in record.get('artist', '').lower():
            results.append(record)
    return results