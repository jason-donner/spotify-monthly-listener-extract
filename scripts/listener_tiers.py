import json
import os
import numpy as np

# Path to the master file
MASTER_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'results', 'spotify-monthly-listeners-master.json')

def main():
    with open(MASTER_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Use only the latest entry per artist for a fair tiering
    latest = {}
    for entry in data:
        artist = entry['artist_id']
        date = entry['date']
        if artist not in latest or date > latest[artist]['date']:
            latest[artist] = entry
    listeners = [a['monthly_listeners'] for a in latest.values() if a['monthly_listeners'] > 0]
    listeners = np.array(listeners)
    percentiles = np.percentile(listeners, [0, 20, 40, 60, 80, 100])
    print("Data-driven tier breakpoints (by monthly listeners):")
    for i in range(5):
        print(f"Tier {i+1}: {int(percentiles[i])} - {int(percentiles[i+1])}")
    print("Suggested labels:")
    print("1: Micro, 2: Small, 3: Medium, 4: Large, 5: Major")

if __name__ == "__main__":
    main()
