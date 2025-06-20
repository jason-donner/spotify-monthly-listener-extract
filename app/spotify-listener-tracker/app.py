from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import requests
import os
from get_token import get_token
from datetime import datetime, timedelta
import time
import sys
from werkzeug.utils import redirect
import re

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
    # Only print critical errors
    if not artist_id:
        print("No artist_id provided.")
        return None
    if artist_id in artist_image_cache:
        return artist_image_cache[artist_id]
    headers = {"Authorization": f"Bearer {get_token()}"}
    resp = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
    if resp.status_code == 200:
        artist = resp.json()
        if artist.get("images"):
            image_url = artist["images"][0]["url"]
            artist_image_cache[artist_id] = image_url
            return image_url
        else:
            print(f"No images found for {artist_id}")
    else:
        print(f"Spotify API error for {artist_id}: {resp.text}")
    return None  # Only return None if no image found

@app.route("/")
def home():
    # Show leaderboard as home page
    return leaderboard()

@app.route("/home")
def home_page():
    # Redirect /home to the leaderboard (which is also thehomepage)
    return redirect(url_for("leaderboard"))

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("artist", "").strip()
    artists = load_data()
    if query:
        query_lower = query.lower()
        # Find the best match (first match by name, case-insensitive)
        for a in artists:
            if query_lower == a.get("artist_name", "").lower():
                artist_id = a.get("artist_id")
                if not artist_id and a.get("artist_url"):
                    artist_id = get_artist_id_from_url(a["artist_url"])
                if artist_id:
                    slug = slugify(a.get("artist_name", "artist"))
                    return redirect(url_for("artist_detail", artist_name_slug=slug, artist_id=artist_id))
        # Group results by artist_id, keep only the most recent entry for each
        filtered = [a.copy() for a in artists if query_lower in a.get("artist_name", "").lower()]
        grouped = {}
        for entry in filtered:
            artist_id = entry.get("artist_id")
            if not artist_id and entry.get("artist_url"):
                artist_id = get_artist_id_from_url(entry["artist_url"])
                entry["artist_id"] = artist_id
            entry["slug"] = slugify(entry.get("artist_name", "artist"))
            # Only keep the most recent entry for each artist_id
            if artist_id not in grouped or entry.get("date","") > grouped[artist_id].get("date",""):
                grouped[artist_id] = entry
        results = list(grouped.values())
        results.sort(key=lambda x: x.get("artist_name", "").lower())
        for i, r in enumerate(results):
            if i + 1 < len(results):
                prev = results[i + 1]
                r['listener_diff'] = r['monthly_listeners'] - prev['monthly_listeners']
            else:
                r['listener_diff'] = None
        # Add image_url for each result (fix for search page images)
        for r in results:
            if r.get("artist_id"):
                r["image_url"] = fetch_spotify_artist_image(r["artist_id"])
            else:
                r["image_url"] = None
        results_for_chart = list(reversed(results))
        artist_url = results[0].get("artist_url") or results[0].get("url") if results else None
        if artist_url:
            artist_id = get_artist_id_from_url(artist_url)
            try:
                artist_image_url = fetch_spotify_artist_image(artist_id)
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
            try:
                resp = requests.get(f"http://localhost:5000/artist_image?name={query}")
                if resp.status_code == 200:
                    artist_image_url = resp.json().get("image")
            except Exception:
                artist_image_url = None
    else:
        results = []
        results_for_chart = []
        artist_info = None
        artist_image_url = None
    if results:
        total_change = results[-1]['monthly_listeners'] - results[0]['monthly_listeners']
    else:
        total_change = None
    return render_template(
        "search.html",
        results=results,
        results_for_chart=results_for_chart,
        query=query,
        total_change=total_change,
        artist_info=artist_info,
        artist_image_url=artist_image_url,
        grow_results=True if results else False,  # Add grow_results flag
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
        if isinstance(value, str) and len(value) in (10, 8):  # YYYY-MM-DD or YYYYMMDD
            return dt.strftime('%b %d')
        elif isinstance(value, str) and len(value) == 7:      # YYYY-MM
            return dt.strftime('%b %Y')
    # Use the provided format string for all other cases
    return dt.strftime(format)

@app.route("/leaderboard")
def leaderboard():
    from datetime import datetime, timedelta
    artists = load_data()
    # Group data by artist
    artist_changes = {}
    cutoff = datetime.now() - timedelta(days=30)
    for entry in artists:
        artist = entry["artist_name"]
        date_str = entry["date"]
        try:
            if '-' in date_str:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                date = datetime.strptime(date_str, "%Y%m%d")
        except Exception:
            continue
        listeners = entry["monthly_listeners"]
        if artist not in artist_changes:
            artist_changes[artist] = []
        artist_changes[artist].append({
            "date": date,
            "listeners": listeners,
            "artist_url": entry.get("artist_url", ""),
            "artist_id": entry.get("artist_id"),
            "slug": slugify(artist)
        })
    leaderboard_data = []
    for artist, records in artist_changes.items():
        recent = [r for r in records if r["date"] >= cutoff]
        if len(recent) < 2:
            continue
        recent.sort(key=lambda x: x["date"])
        start = recent[0]["listeners"]
        end = recent[-1]["listeners"]
        if start == 0:
            continue
        if start < 50 and end < 50:
            continue
        change = end - start
        percent_change = ((end - start) / start) * 100
        artist_id = None
        artist_url = None
        slug = None
        for r in reversed(recent):
            if r and r.get("artist_id"):
                artist_id = r["artist_id"]
                artist_url = r.get("artist_url")
                slug = r.get("slug")
                break
        leaderboard_data.append({
            "artist": artist,
            "artist_id": artist_id,
            "slug": slug,
            "change": change,
            "percent_change": percent_change,
            "start": start,
            "end": end,
            "artist_url": artist_url
        })
    mode = request.args.get('mode', 'growth')
    tier = request.args.get('tier', 'all')
    def in_tier(start, end, tier):
        if tier == 'micro':
            return start <= 1000 and end <= 1000
        elif tier == 'small':
            return 1001 <= start <= 3000 and 1001 <= end <= 3000
        elif tier == 'medium':
            return 3001 <= start <= 15000 and 3001 <= end <= 15000
        elif tier == 'large':
            return 15001 <= start <= 50000 and 15001 <= end <= 50000
        elif tier == 'major':
            return start > 50000 and end > 50000
        return True
    leaderboard_data = [row for row in leaderboard_data if in_tier(row['start'], row['end'], tier)]
    if mode == 'loss':
        leaderboard_data.sort(key=lambda x: x['percent_change'])
    else:
        leaderboard_data.sort(key=lambda x: x['percent_change'], reverse=True)
    leaderboard_data = leaderboard_data[:10]
    for entry in leaderboard_data:
        entry["image_url"] = fetch_spotify_artist_image(entry["artist_id"]) if entry["artist_id"] else None
    return render_template(
        "leaderboard.html",
        leaderboard=leaderboard_data,
        leaderboard_mode=mode,
        leaderboard_tier=tier,
    )

# Helper to slugify artist names for URLs
def slugify(value):
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)

@app.route("/artist/<artist_id>")
def artist_detail_redirect(artist_id):
    # Find artist name for slug
    artists = load_data()
    for a in artists:
        if a.get("artist_id") == artist_id:
            artist_name = a.get("artist_name", "artist")
            slug = slugify(artist_name)
            return redirect(url_for('artist_detail', artist_name_slug=slug, artist_id=artist_id))
    return redirect(url_for('home'))

@app.route("/artist/<artist_name_slug>/<artist_id>")
def artist_detail(artist_name_slug, artist_id):
    artists = load_data()
    results = [a for a in artists if a.get("artist_id") == artist_id]
    results.sort(key=lambda x: x.get("date", ""), reverse=True)
    # Convert date strings to datetime objects for template formatting
    def parse_date(val):
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(val, fmt)
                except Exception:
                    continue
        return val
    for row in results:
        row["date"] = parse_date(row.get("date"))
    artist_info = None
    artist_image_url = None
    all_time_high = None
    if results:
        # Find all-time high monthly listeners and its date
        max_entry = max(results, key=lambda x: x.get("monthly_listeners", 0))
        all_time_high = {
            "value": max_entry.get("monthly_listeners", 0),
            "date": parse_date(max_entry.get("date", ""))
        }
        artist_url = results[0].get("artist_url") or results[0].get("url")
        try:
            artist_image_url = fetch_spotify_artist_image(artist_id)
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
    return render_template(
        "artist.html",
        results=results,
        artist_info=artist_info,
        artist_image_url=artist_image_url,
        all_time_high=all_time_high,
        artist_id=artist_id,
    )

if __name__ == "__main__":
    app.run(debug=True)