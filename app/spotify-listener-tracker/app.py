from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import requests
import os
from get_token import get_token
from datetime import datetime, timedelta
import time

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

artist_image_cache = {}

def fetch_spotify_artist_image(artist_id):
    print(f"Fetching image for artist_id: {artist_id}")
    if not artist_id:
        print("No artist_id provided.")
        return None
    if artist_id in artist_image_cache:
        print(f"Cache hit for {artist_id}: {artist_image_cache[artist_id]}")
        return artist_image_cache[artist_id]
    headers = {"Authorization": f"Bearer {get_token()}"}
    resp = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
    print(f"Spotify API status for {artist_id}: {resp.status_code}")
    if resp.status_code == 200:
        artist = resp.json()
        if artist.get("images"):
            image_url = artist["images"][0]["url"]
            print(f"Image found for {artist_id}: {image_url}")
            artist_image_cache[artist_id] = image_url
            return image_url
        else:
            print(f"No images found for {artist_id}")
    else:
        print(f"Spotify API error for {artist_id}: {resp.text}")
    return None  # Only return None if no image found

@app.route("/", methods=["GET"])
def index():
    query = request.args.get("artist", "").strip()
    artists = load_data()
    all_artist_names = sorted({a['artist_name'] for a in artists})

    # Leaderboard logic (last 30 days)
    cutoff = datetime.now() - timedelta(days=30)
    artist_changes = {}
    for entry in artists:
        artist = entry["artist_name"]
        date_str = entry["date"]
        # Handle both 'YYYY-MM-DD' and 'YYYYMMDD'
        try:
            if '-' in date_str:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                date = datetime.strptime(date_str, "%Y%m%d")
        except Exception:
            continue  # skip malformed dates
        listeners = entry["monthly_listeners"]
        if artist not in artist_changes:
            artist_changes[artist] = []
        artist_changes[artist].append({
            "date": date,
            "listeners": listeners,
            "artist_url": entry.get("artist_url", ""),
            "artist_id": entry.get("artist_id")
        })
    leaderboard_data = []
    for artist, records in artist_changes.items():
        recent = [r for r in records if r["date"] >= cutoff]
        if len(recent) < 2:
            continue
        recent.sort(key=lambda x: x["date"])
        change = recent[-1]["listeners"] - recent[0]["listeners"]
        artist_id = None
        artist_url = None
        for r in reversed(recent):
            if r and r.get("artist_id"):
                artist_id = r["artist_id"]
                artist_url = r.get("artist_url")
                break
        print(f"DEBUG: {artist} | artist_id: {artist_id}")
        image_url = fetch_spotify_artist_image(artist_id) if artist_id else None
        print(f"DEBUG: {artist} | image_url: {image_url}")
        leaderboard_data.append({
            "artist": artist,
            "artist_id": artist_id,
            "image_url": image_url,
            "change": change,
            "start": recent[0]["listeners"],
            "end": recent[-1]["listeners"],
            "artist_url": artist_url
        })
    leaderboard_data.sort(key=lambda x: abs(x["change"]), reverse=True)
    leaderboard_data = leaderboard_data[:10]  # Show top 10

    results = []
    artist_info = None
    artist_image_url = None
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

        # Fetch artist info and image for the card
        artist_url = results[0].get("artist_url") or results[0].get("url") if results else None
        if artist_url:
            artist_id = get_artist_id_from_url(artist_url)
            try:
                # Fetch directly from Spotify API for consistency
                artist_image_url = fetch_spotify_artist_image(artist_id)
                # Also get artist info
                headers = {"Authorization": f"Bearer {get_token()}"}
                resp = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
                if resp.status_code == 200:
                    artist = resp.json()
                    artist_info = {
                        "name": artist["name"],
                        "image": artist["images"][0]["url"] if artist.get("images") else "",
                        "genres": artist.get("genres", []),
                        "followers": artist.get("followers", {}).get("total", 0),
                        "url": artist["external_urls"]["spotify"]
                    }
            except Exception:
                artist_info = None
                artist_image_url = None
        else:
            # fallback: try to get image by name
            try:
                resp = requests.get(f"http://localhost:5000/artist_image?name={query}")
                if resp.status_code == 200:
                    artist_image_url = resp.json().get("image")
            except Exception:
                artist_image_url = None
    else:
        results_for_chart = []

    # Debug print to check for rounding
    for r in results:
        print("DEBUG:", r['artist_name'], r['monthly_listeners'])

    if results:
        total_change = results[-1]['monthly_listeners'] - results[0]['monthly_listeners']
    else:
        total_change = None
    return render_template(
        "index.html",
        results=results,
        results_for_chart=results_for_chart,
        query=query,
        total_change=total_change,
        all_artist_names=all_artist_names,
        leaderboard=leaderboard_data,
        artist_info=artist_info,
        artist_image_url=artist_image_url,
    )

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

@app.route('/artist_image/<artist_id>')
def artist_image_redirect(artist_id):
    # Fetch the image URL for the artist
    image_url = get_artist_image_url(artist_id)  # Implement this function
    if image_url:
        return redirect(image_url)
    else:
        # Return a placeholder image or 404
        return redirect(url_for('static', filename='placeholder.png'))

def get_artist_image_url(artist_id):
    headers = {"Authorization": f"Bearer {get_token()}"}
    resp = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
    if resp.status_code == 200:
        artist = resp.json()
        if artist.get("images"):
            return artist["images"][0]["url"]
    return url_for('static', filename='placeholder.png')

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