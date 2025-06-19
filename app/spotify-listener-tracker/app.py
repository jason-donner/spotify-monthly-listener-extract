from flask import Flask, render_template, request, jsonify
import json
import requests
import os
from get_token import get_token
from datetime import datetime

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# Path to your master data file
DATA_PATH = r"C:\Users\Jason\Spotify Monthly Listener Extract\src\results\spotify-monthly-listeners-master.json"

def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data

def get_artist_id_from_url(url):
    # Extract the artist ID from the Spotify URL
    return url.rstrip('/').split('/')[-1]

@app.route("/", methods=["GET"])
def index():
    query = request.args.get("artist", "").strip()
    artists = load_data()
    results = []
    if query:
        query_lower = query.lower()
        # Find all records matching the artist name
        results = [a for a in artists if query_lower in a.get("artist_name", "").lower()]
        # Sort results by date (descending)
        results.sort(key=lambda x: x.get("date", ""), reverse=True)
        # Calculate difference
        for i, r in enumerate(results):
            if i + 1 < len(results):
                prev = results[i + 1]
                r['listener_diff'] = r['monthly_listeners'] - prev['monthly_listeners']
            else:
                r['listener_diff'] = None  # No previous data
        # Reverse for chart (oldest to newest)
        results_for_chart = list(reversed(results))
    else:
        results_for_chart = []

    # Debug print to check for rounding
    for r in results:
        print("DEBUG:", r['artist_name'], r['monthly_listeners'])

    return render_template("index.html", results=results, results_for_chart=results_for_chart, query=query)

@app.route("/suggest", methods=["GET"])
def suggest():
    term = request.args.get("term", "").strip().lower()
    artists = load_data()
    suggestions = []
    if term:
        seen = set()
        for a in artists:
            name = a.get("artist_name", "")
            if term in name.lower() and name not in seen:
                suggestions.append(name)
                seen.add(name)
        suggestions.sort()  # Sort alphabetically
    return jsonify(suggestions)

@app.route("/top_tracks/<artist_id>")
def top_tracks(artist_id):
    headers = {"Authorization": f"Bearer {get_token()}"}
    params = {"market": "US"}
    resp = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks", headers=headers, params=params)
    if resp.status_code == 200:
        tracks = resp.json().get("tracks", [])
        return jsonify([
            {
                "name": t["name"],
                "url": t["external_urls"]["spotify"],
                "album_image": t["album"]["images"][0]["url"] if t["album"]["images"] else ""
            }
            for t in tracks
        ])
    return jsonify([])

@app.route("/artist_info/<artist_id>")
def artist_info(artist_id):
    headers = {"Authorization": f"Bearer {get_token()}"}
    resp = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
    if resp.status_code == 200:
        artist = resp.json()
        return jsonify({
            "name": artist["name"],
            "image": artist["images"][0]["url"] if artist.get("images") else "",
            "genres": artist.get("genres", []),
            "popularity": artist.get("popularity", 0),
            "followers": artist.get("followers", {}).get("total", 0),
            "url": artist["external_urls"]["spotify"]
        })
    return jsonify({})

@app.route("/artist_image")
def artist_image():
    name = request.args.get("name")
    # Lookup artist by name using Spotify API
    headers = {"Authorization": f"Bearer {get_token()}"}
    resp = requests.get("https://api.spotify.com/v1/search", params={"q": name, "type": "artist", "limit": 1}, headers=headers)
    if resp.status_code == 200:
        items = resp.json().get("artists", {}).get("items", [])
        if items and items[0].get("images"):
            return jsonify({"image": items[0]["images"][0]["url"]})
    return jsonify({"image": "https://via.placeholder.com/64?text=No+Image"})

@app.template_filter('datetimeformat')
def datetimeformat(value, format='medium'):
    from datetime import datetime
    if not value:
        return ''
    if isinstance(value, str):
        try:
            # Handle YYYY-MM-DD
            if len(value) == 10 and '-' in value:
                dt = datetime.strptime(value, "%Y-%m-%d")
            # Handle YYYY-MM
            elif len(value) == 7 and '-' in value:
                dt = datetime.strptime(value, "%Y-%m")
            # Handle YYYYMMDD
            elif len(value) == 8 and value.isdigit():
                dt = datetime.strptime(value, "%Y%m%d")
            else:
                return value
        except Exception:
            return value
    else:
        dt = value
    if format == 'short':
        # "Jun 18" or "Jun 2024"
        if len(value) in (10, 8):  # YYYY-MM-DD or YYYYMMDD
            return dt.strftime('%b %d')
        elif len(value) == 7:      # YYYY-MM
            return dt.strftime('%b %Y')
    # Default: "2024-06-18" or "2024-06"
    return dt.strftime('%Y-%m-%d') if len(value) in (10, 8) else dt.strftime('%Y-%m')

@app.route("/leaderboard")
def leaderboard():
    import json
    from collections import defaultdict
    from datetime import datetime, timedelta

    artists = load_data()
    # Group data by artist
    artist_history = defaultdict(list)
    for entry in artists:
        artist_history[entry["artist_name"]].append(entry)

    leaderboard = []
    for artist, records in artist_history.items():
        # Sort records by date descending
        records.sort(key=lambda x: x["date"], reverse=True)
        if len(records) < 2:
            continue
        # Get the most recent and the previous month's record
        latest = records[0]
        # Find the record closest to 30 days before latest
        latest_date = datetime.strptime(latest["date"], "%Y-%m-%d")
        prev = None
        for r in records[1:]:
            r_date = datetime.strptime(r["date"], "%Y-%m-%d")
            if (latest_date - r_date).days >= 28:
                prev = r
                break
        if prev:
            change = latest["monthly_listeners"] - prev["monthly_listeners"]
            leaderboard.append({
                "artist_name": artist,
                "latest": latest["monthly_listeners"],
                "prev": prev["monthly_listeners"],
                "change": change,
                "url": latest.get("url", "#")
            })

    # Sort by biggest change (absolute value, descending)
    leaderboard.sort(key=lambda x: abs(x["change"]), reverse=True)
    # Top 20
    leaderboard = leaderboard[:20]

    return render_template("leaderboard.html", leaderboard=leaderboard)

if __name__ == "__main__":
    app.run(debug=True)