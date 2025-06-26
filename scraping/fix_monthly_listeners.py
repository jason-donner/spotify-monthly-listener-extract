"""
fix_monthly_listeners.py
------------------------
One-time utility to convert all 'monthly_listeners' values in the master JSON
from strings like '1.2k' to integers (e.g., 1200).
Usage:
    python fix_monthly_listeners.py --file src/results/spotify-monthly-listeners-master.json
"""

import json
import argparse

def parse_listener_count(val):
    if not val:
        return 0
    val = str(val).lower().replace(',', '').strip()
    try:
        if 'k' in val:
            return int(float(val.replace('k', '')) * 1000)
        elif 'm' in val:
            return int(float(val.replace('m', '')) * 1000000)
        else:
            return int(val)
    except Exception:
        return 0

def main():
    parser = argparse.ArgumentParser(description="Fix monthly_listeners values in a JSON file.")
    parser.add_argument('--file', required=True, help="Path to the JSON file to fix.")
    args = parser.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for entry in data:
        if 'monthly_listeners' in entry:
            entry['monthly_listeners'] = parse_listener_count(entry['monthly_listeners'])

    with open(args.file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"All monthly_listeners values in {args.file} have been converted to integers.")

if __name__ == "__main__":
    main()