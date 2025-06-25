from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import requests
import os
from get_token import get_token
from datetime import datetime, timedelta
import time
import sys
from werkzeug.utils import redirect
import re
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import subprocess
import threading
import uuid

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# Load environment variables from .env file
load_dotenv()

# Configure session
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-in-production')

def get_spotify_credentials():
    """Get fresh Spotify credentials from environment"""
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:5000/callback")
    
    if not client_id or not client_secret:
        raise ValueError("Spotify credentials not found in environment variables")
    
    print(f"DEBUG: Using Client ID: {client_id}")  # Debug log
    return client_id, client_secret, redirect_uri

SPOTIFY_SCOPE = "user-follow-modify user-follow-read"

def get_spotify_oauth():
    """Create a SpotifyOAuth instance"""
    client_id, client_secret, redirect_uri = get_spotify_credentials()
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SPOTIFY_SCOPE,
        cache_path=None,  # We'll use session storage instead
        show_dialog=True  # Force account selection dialog
    )

def get_token_from_session():
    """Get Spotify token from Flask session"""
    return session.get('spotify_token')

def save_token_to_session(token_info):
    """Save Spotify token to Flask session"""
    session['spotify_token'] = token_info

def get_authenticated_spotify():
    """Get an authenticated Spotify client or None if not authenticated"""
    token_info = get_token_from_session()
    
    if not token_info:
        return None
    
    sp_oauth = get_spotify_oauth()
    
    # Check if token is expired and refresh if needed
    if sp_oauth.is_token_expired(token_info):
        try:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            save_token_to_session(token_info)
        except Exception as e:
            session.pop('spotify_token', None)
            return None
    
    return spotipy.Spotify(auth=token_info['access_token'])

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
        
        # Initialize artist_info and artist_image_url
        artist_info = None
        artist_image_url = None
        
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
    start_date = None
    end_date = None
    
    for artist, records in artist_changes.items():
        recent = [r for r in records if r["date"] >= cutoff]
        if len(recent) < 2:
            continue
        recent.sort(key=lambda x: x["date"])
        
        # Track the overall date range for the leaderboard
        if start_date is None or recent[0]["date"] < start_date:
            start_date = recent[0]["date"]
        if end_date is None or recent[-1]["date"] > end_date:
            end_date = recent[-1]["date"]
        
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
        start_date=start_date,
        end_date=end_date,
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
    results.sort(key=lambda x: x.get("date", ""), reverse=False)  # oldest first
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

@app.route("/search_spotify_artists")
def search_spotify_artists():
    """Search for artists on Spotify API for autocomplete suggestions"""
    query = request.args.get("q", "").strip()
    
    print(f"Artist search query: '{query}'")  # Debug log
    
    if not query or len(query) < 2:
        return jsonify({"artists": []})
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        params = {
            "q": query,
            "type": "artist",
            "limit": 10
        }
        
        resp = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
        
        if resp.status_code == 200:
            data = resp.json()
            artists = []
            
            for artist in data.get("artists", {}).get("items", []):
                artists.append({
                    "id": artist["id"],
                    "name": artist["name"],
                    "url": artist["external_urls"]["spotify"],
                    "image": artist["images"][0]["url"] if artist.get("images") else "",
                    "followers": artist.get("followers", {}).get("total", 0)
                })
            
            print(f"Found {len(artists)} artists")  # Debug log
            return jsonify({"artists": artists})
        else:
            print(f"Spotify API search error: {resp.status_code} - {resp.text}")
            return jsonify({"artists": []})
            
    except Exception as e:
        print(f"Error searching Spotify artists: {e}")
        return jsonify({"artists": []})

@app.route("/suggest_artist", methods=["POST"])
def suggest_artist():
    import json
    import os
    from datetime import datetime
    
    try:
        data = request.get_json()
        artist_name = data.get("artist_name", "").strip()
        spotify_url = data.get("spotify_url", "").strip()
        spotify_id = data.get("spotify_id", "").strip()
        
        if not artist_name:
            return jsonify({"success": False, "message": "Artist name is required"})
        
        # Check blacklist
        blacklist_file = os.path.join(os.path.dirname(__file__), "artist_blacklist.json")
        blacklisted_artists = []
        blacklisted_ids = []
        if os.path.exists(blacklist_file):
            try:
                with open(blacklist_file, "r", encoding="utf-8") as f:
                    blacklist_data = json.load(f)
                    for item in blacklist_data:
                        if isinstance(item, str):
                            # Old format - just artist name
                            blacklisted_artists.append(item.lower())
                        elif isinstance(item, dict):
                            # New format - object with name, spotify_id, etc.
                            if item.get("name"):
                                blacklisted_artists.append(item["name"].lower())
                            if item.get("spotify_id"):
                                blacklisted_ids.append(item["spotify_id"])
            except:
                blacklisted_artists = []
                blacklisted_ids = []
        
        # Check if artist is blacklisted (by name or Spotify ID)
        if (artist_name.lower() in blacklisted_artists or 
            (spotify_id and spotify_id in blacklisted_ids)):
            return jsonify({"success": False, "message": "We do not support predators"})
        
        # Create suggestions file if it doesn't exist
        suggestions_file = os.path.join(os.path.dirname(__file__), "artist_suggestions.json")
        
        # Load existing suggestions and check first (more specific than followed)
        suggestions = []
        if os.path.exists(suggestions_file):
            try:
                with open(suggestions_file, "r", encoding="utf-8") as f:
                    suggestions = json.load(f)
            except:
                suggestions = []
        
        # Check if artist already suggested (by name or Spotify ID)
        for suggestion in suggestions:
            if (suggestion.get("artist_name", "").lower() == artist_name.lower() or 
                (spotify_id and suggestion.get("spotify_id") == spotify_id)):
                return jsonify({"success": False, "message": f"{artist_name} has already been suggested and is waiting to be added!"})
        
        # Check if artist is already followed (in the master followed list)
        followed_artists_file = os.path.join(os.path.dirname(__file__), "..", "..", "src", "results", "spotify-followed-artists-master.json")
        if os.path.exists(followed_artists_file):
            try:
                with open(followed_artists_file, "r", encoding="utf-8") as f:
                    followed_artists = json.load(f)
                    
                # Check if artist is already followed (by name or Spotify ID)
                for followed in followed_artists:
                    followed_name = followed.get("artist_name", "").lower()
                    followed_id = followed.get("artist_id", "")
                    followed_url = followed.get("url", "")
                    
                    # Extract ID from URL if not directly available
                    if not followed_id and followed_url:
                        followed_id = get_artist_id_from_url(followed_url)
                    
                    if (artist_name.lower() == followed_name or 
                        (spotify_id and followed_id and spotify_id == followed_id)):
                        return jsonify({"success": False, "message": f"You're already following {artist_name} on Spotify!"})
            except Exception as e:
                print(f"Error checking followed artists: {e}")
        
        # Add new suggestion - auto-approved unless blacklisted
        new_suggestion = {
            "artist_name": artist_name,
            "spotify_url": spotify_url if spotify_url else None,
            "spotify_id": spotify_id if spotify_id else None,
            "timestamp": datetime.now().isoformat(),
            "status": "approved"  # Auto-approve everything not blacklisted
        }
        
        suggestions.append(new_suggestion)
        
        # Save suggestions
        with open(suggestions_file, "w", encoding="utf-8") as f:
            json.dump(suggestions, f, indent=2, ensure_ascii=False)
        
        return jsonify({"success": True, "message": "Artist suggestion approved and added to the queue!"})
        
    except Exception as e:
        print(f"Error handling artist suggestion: {e}")
        return jsonify({"success": False, "message": "Server error occurred"})

@app.route("/admin")
def admin():
    """Admin page to review and manage artist suggestions."""
    return render_template("admin.html")

@app.route("/admin/suggestions")
def admin_suggestions():
    """API endpoint to get all suggestions for admin review."""
    suggestions_file = os.path.join(os.path.dirname(__file__), "artist_suggestions.json")
    
    if not os.path.exists(suggestions_file):
        return jsonify({"suggestions": []})
    
    try:
        with open(suggestions_file, "r", encoding="utf-8") as f:
            suggestions = json.load(f)
        
        # Add additional info for each suggestion
        for suggestion in suggestions:
            # Check if already followed
            followed_file = os.path.join(os.path.dirname(__file__), "..", "..", "src", "results", "spotify-followed-artists-master.json")
            if os.path.exists(followed_file):
                try:
                    with open(followed_file, "r", encoding="utf-8") as f:
                        followed_artists = json.load(f)
                    
                    suggestion["already_followed"] = any(
                        (suggestion.get("artist_name", "").lower() == followed.get("artist_name", "").lower() or
                         suggestion.get("spotify_id") == followed.get("artist_id"))
                        for followed in followed_artists
                    )
                except:
                    suggestion["already_followed"] = False
            else:
                suggestion["already_followed"] = False
        
        return jsonify({"suggestions": suggestions})
    except Exception as e:
        return jsonify({"error": str(e), "suggestions": []})

@app.route("/admin/approve_suggestion", methods=["POST"])
def admin_approve_suggestion():
    """Admin endpoint to approve a suggestion for auto-following."""
    try:
        data = request.get_json()
        suggestion_id = data.get("suggestion_id")  # Using timestamp as ID
        action = data.get("action")  # "approve_follow", "approve_track", "reject"
        
        suggestions_file = os.path.join(os.path.dirname(__file__), "artist_suggestions.json")
        
        if not os.path.exists(suggestions_file):
            return jsonify({"success": False, "message": "No suggestions file found"})
        
        # Load suggestions
        with open(suggestions_file, "r", encoding="utf-8") as f:
            suggestions = json.load(f)
        
        # Find the suggestion to update
        suggestion_found = False
        for suggestion in suggestions:
            if suggestion.get("timestamp") == suggestion_id:
                suggestion_found = True
                
                if action == "approve_follow":
                    suggestion["status"] = "approved_for_follow"
                    suggestion["admin_approved"] = True
                    suggestion["admin_action_date"] = datetime.now().isoformat()
                elif action == "approve_track":
                    suggestion["status"] = "approved_for_tracking"
                    suggestion["admin_approved"] = True
                    suggestion["admin_action_date"] = datetime.now().isoformat()
                elif action == "reject":
                    suggestion["status"] = "rejected"
                    suggestion["admin_approved"] = False
                    suggestion["admin_action_date"] = datetime.now().isoformat()
                
                break
        
        if not suggestion_found:
            return jsonify({"success": False, "message": "Suggestion not found"})
        
        # Save updated suggestions
        with open(suggestions_file, "w", encoding="utf-8") as f:
            json.dump(suggestions, f, indent=2, ensure_ascii=False)
        
        return jsonify({"success": True, "message": f"Suggestion {action.replace('_', ' ')}d successfully"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route("/admin/follow_artist", methods=["POST"])
def admin_follow_artist():
    """Admin endpoint to immediately follow an artist on Spotify."""
    try:
        data = request.get_json()
        artist_id = data.get("artist_id")
        artist_name = data.get("artist_name", "Unknown Artist")
        
        if not artist_id:
            return jsonify({"success": False, "message": "Artist ID is required"})
        
        # Get authenticated Spotify client
        sp = get_authenticated_spotify()
        
        if not sp:
            return jsonify({
                "success": False, 
                "message": "Spotify authentication required. Please log in with Spotify to follow artists.",
                "auth_required": True
            })
        
        try:
            # Test authentication and get user info
            user = sp.current_user()
            print(f"DEBUG: Following artist as user ID: {user.get('id')}")
            print(f"DEBUG: Following artist as user display name: {user.get('display_name', user.get('id'))}")
            print(f"DEBUG: User email: {user.get('email', 'Not available')}")
            
            # Follow the artist
            sp.user_follow_artists([artist_id])
            print(f"Successfully followed artist {artist_id} ({artist_name})")
            
        except spotipy.SpotifyException as e:
            if e.http_status == 401:
                # Clear invalid token
                session.pop('spotify_token', None)
                return jsonify({
                    "success": False,
                    "message": "Authentication expired. Please log in again.",
                    "auth_required": True
                })
            else:
                return jsonify({"success": False, "message": f"Spotify API error: {str(e)}"})
        
        # Also add to followed artists file
        followed_file = os.path.join(os.path.dirname(__file__), "..", "..", "src", "results", "spotify-followed-artists-master.json")
        try:
            if os.path.exists(followed_file):
                with open(followed_file, "r", encoding="utf-8") as f:
                    followed_artists = json.load(f)
            else:
                followed_artists = []
            
            # Check if already in list
            already_exists = any(
                followed.get("artist_id") == artist_id 
                for followed in followed_artists
            )
            
            if not already_exists:
                new_artist = {
                    "artist_name": artist_name,
                    "artist_id": artist_id,
                    "url": f"https://open.spotify.com/artist/{artist_id}",
                    "source": "admin_follow",
                    "date_added": datetime.now().strftime("%Y-%m-%d"),
                    "removed": False
                }
                followed_artists.append(new_artist)
                
                with open(followed_file, "w", encoding="utf-8") as f:
                    json.dump(followed_artists, f, indent=2, ensure_ascii=False)
                    
                print(f"Added {artist_name} to followed artists file")
        except Exception as e:
            print(f"Error updating followed artists file: {e}")
        
        return jsonify({"success": True, "message": f"Successfully followed {artist_name} on Spotify and added to tracking list!"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route("/login")
def login():
    """Initiate Spotify OAuth login"""
    # Check if force login is requested
    force = request.args.get('force', 'false').lower() == 'true'
    
    sp_oauth = get_spotify_oauth()
    if force:
        # Clear any existing session data
        session.pop('spotify_token', None)
        # Create OAuth with show_dialog=True to force account selection
        client_id, client_secret, redirect_uri = get_spotify_credentials()
        sp_oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=SPOTIFY_SCOPE,
            cache_path=None,
            show_dialog=True
        )
    
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    """Handle Spotify OAuth callback"""
    sp_oauth = get_spotify_oauth()
    
    # Clear any existing token
    session.pop('spotify_token', None)
    
    code = request.args.get('code')
    if not code:
        return redirect('/admin?error=auth_cancelled')
    
    try:
        token_info = sp_oauth.get_access_token(code)
        save_token_to_session(token_info)
        return redirect('/admin?success=logged_in')
    except Exception as e:
        print(f"OAuth callback error: {e}")
        return redirect('/admin?error=auth_failed')

@app.route("/logout")
def logout():
    """Clear Spotify authentication"""
    session.pop('spotify_token', None)
    return redirect('/admin?success=logged_out')

@app.route("/auth_status")
def auth_status():
    """Check if user is authenticated with Spotify"""
    token_info = get_token_from_session()
    
    if not token_info:
        return jsonify({"authenticated": False})
    
    sp_oauth = get_spotify_oauth()
    
    # Check if token is expired and refresh if needed
    if sp_oauth.is_token_expired(token_info):
        try:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            save_token_to_session(token_info)
        except Exception as e:
            session.pop('spotify_token', None)
            return jsonify({"authenticated": False})
    
    # Test the token by making a simple API call
    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user = sp.current_user()
        
        # Debug logging to see which account we're actually authenticated as
        print(f"DEBUG: Authenticated user ID: {user.get('id')}")
        print(f"DEBUG: Authenticated user display name: {user.get('display_name')}")
        print(f"DEBUG: User email: {user.get('email', 'Not available')}")
        
        return jsonify({
            "authenticated": True,
            "user": {
                "id": user.get('id'),
                "display_name": user.get('display_name'),
                "images": user.get('images', [])
            }
        })
    except Exception as e:
        print(f"DEBUG: Auth status error: {e}")
        session.pop('spotify_token', None)
        return jsonify({"authenticated": False})

@app.route("/admin/run_scraping", methods=["POST"])
def admin_run_scraping():
    """Admin endpoint to run the scraping script."""
    import subprocess
    import threading
    import uuid
    from datetime import datetime
    import tempfile
    
    try:
        data = request.get_json()
        headless = data.get("headless", True)  # Default to headless mode
        today_only = data.get("today_only", False)  # New option for today-only scraping
        
        # Generate a unique job ID for this scraping run
        job_id = str(uuid.uuid4())
        
        # Create job status file in temp directory
        job_file = os.path.join(tempfile.gettempdir(), f"scraping_job_{job_id}.json")
        
        initial_job_data = {
            'job_id': job_id,
            'status': 'starting',
            'started_at': datetime.now().isoformat(),
            'output': '',
            'error': '',
            'completed': False,
            'today_only': today_only
        }
        
        # Save initial job status to file
        try:
            with open(job_file, 'w', encoding='utf-8') as f:
                json.dump(initial_job_data, f)
        except Exception as e:
            print(f"Error creating job file: {e}")
        
        def run_scraping():
            def update_job_status(updates):
                """Helper function to update job status file"""
                try:
                    if os.path.exists(job_file):
                        with open(job_file, 'r', encoding='utf-8') as f:
                            job_data = json.load(f)
                    else:
                        job_data = initial_job_data.copy()
                    
                    job_data.update(updates)
                    
                    with open(job_file, 'w', encoding='utf-8') as f:
                        json.dump(job_data, f)
                except Exception as e:
                    print(f"Error updating job status: {e}")
            
            try:
                # Set environment variables from our .env file for the subprocess
                env = os.environ.copy()
                env['CHROMEDRIVER_PATH'] = os.getenv('CHROMEDRIVER_PATH', 'chromedriver')
                
                # Choose the appropriate scraping script based on today_only option
                if today_only:
                    scrape_script = os.path.join(os.path.dirname(__file__), "..", "..", "src", "scrape_filtered.py")
                else:
                    scrape_script = os.path.join(os.path.dirname(__file__), "..", "..", "src", "scrape.py")
                
                # Build the command
                cmd = [sys.executable, scrape_script]
                
                # Add --no-prompt to skip the login prompt
                cmd.append("--no-prompt")
                
                # Add headless mode flag if supported
                if headless:
                    cmd.append("--headless")
                
                # For filtered scraping, add today-only flag
                if today_only:
                    # Use today's date in YYYY-MM-DD format
                    today_date = datetime.now().strftime('%Y-%m-%d')
                    cmd.extend(["--date", today_date])
                
                print(f"DEBUG: Running scraping command: {' '.join(cmd)}")
                print(f"DEBUG: Using CHROMEDRIVER_PATH: {env.get('CHROMEDRIVER_PATH')}")
                
                # Update status to running
                update_job_status({'status': 'running'})
                
                # Run the script with updated environment
                result = subprocess.run(
                    cmd,
                    cwd=os.path.dirname(scrape_script),
                    capture_output=True,
                    text=True,
                    timeout=1800,  # 30 minute timeout
                    env=env  # Pass the updated environment
                )
                
                # Update job status with results
                final_status = {
                    'status': 'completed' if result.returncode == 0 else 'failed',
                    'output': result.stdout,
                    'error': result.stderr,
                    'completed': True,
                    'return_code': result.returncode,
                    'completed_at': datetime.now().isoformat()
                }
                update_job_status(final_status)
                
                print(f"DEBUG: Scraping completed with return code: {result.returncode}")
                
            except subprocess.TimeoutExpired:
                update_job_status({
                    'status': 'timeout',
                    'error': 'Scraping script timed out after 30 minutes',
                    'completed': True,
                    'completed_at': datetime.now().isoformat()
                })
                print("DEBUG: Scraping timed out")
                
            except Exception as e:
                update_job_status({
                    'status': 'error',
                    'error': str(e),
                    'completed': True,
                    'completed_at': datetime.now().isoformat()
                })
                print(f"DEBUG: Scraping error: {e}")
        
        # Start scraping in background thread
        thread = threading.Thread(target=run_scraping)
        thread.daemon = True
        thread.start()
        
        scraping_type = "filtered (today's artists only)" if today_only else "full"
        return jsonify({
            "success": True, 
            "message": f"Scraping started successfully ({scraping_type})", 
            "job_id": job_id
        })
        
    except Exception as e:
        print(f"Error starting scraping: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route("/admin/scraping_status/<job_id>")
def admin_scraping_status(job_id):
    """Get the status of a scraping job."""
    import tempfile
    
    try:
        job_file = os.path.join(tempfile.gettempdir(), f"scraping_job_{job_id}.json")
        
        if not os.path.exists(job_file):
            return jsonify({"success": False, "message": "Job not found"})
        
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                job_data = json.load(f)
            
            return jsonify({
                "success": True,
                "job": job_data
            })
        except Exception as e:
            return jsonify({"success": False, "message": f"Error reading job file: {str(e)}"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route("/admin/scraping_jobs")
def admin_scraping_jobs():
    """Get all scraping jobs."""
    import tempfile
    import glob
    
    try:
        job_pattern = os.path.join(tempfile.gettempdir(), "scraping_job_*.json")
        job_files = glob.glob(job_pattern)
        
        jobs = {}
        for job_file in job_files:
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                    job_id = job_data.get('job_id')
                    if job_id:
                        jobs[job_id] = job_data
            except Exception as e:
                print(f"Error reading job file {job_file}: {e}")
                continue
        
        return jsonify({
            "success": True,
            "jobs": jobs
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route("/admin/process_suggestions", methods=["POST"])
def admin_process_suggestions():
    """Admin endpoint to process approved suggestions and add them to the followed artists list."""
    import subprocess
    from datetime import datetime
    
    try:
        # Path to the suggestion processing script
        process_script = os.path.join(os.path.dirname(__file__), "..", "..", "src", "process_suggestions.py")
        
        # Set environment variables for the subprocess
        env = os.environ.copy()
        # Make sure Spotify credentials are available to the subprocess
        env['SPOTIPY_CLIENT_ID'] = os.getenv('SPOTIPY_CLIENT_ID', '')
        env['SPOTIPY_CLIENT_SECRET'] = os.getenv('SPOTIPY_CLIENT_SECRET', '')
        env['SPOTIPY_REDIRECT_URI'] = os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:5000/callback')
        
        print(f"DEBUG: Running process suggestions script: {process_script}")
        
        # Run the processing script
        result = subprocess.run(
            [sys.executable, process_script],
            cwd=os.path.dirname(process_script),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=env
        )
        
        print(f"DEBUG: Process suggestions completed with return code: {result.returncode}")
        print(f"DEBUG: Output: {result.stdout}")
        if result.stderr:
            print(f"DEBUG: Error: {result.stderr}")
        
        if result.returncode == 0:
            return jsonify({
                "success": True,
                "message": "Successfully processed approved suggestions!",
                "output": result.stdout
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Processing failed with return code {result.returncode}",
                "error": result.stderr,
                "output": result.stdout
            })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "message": "Processing timed out after 5 minutes"
        })
    except Exception as e:
        print(f"Error processing suggestions: {e}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        })

def cleanup_old_job_files():
    """Clean up job files older than 24 hours"""
    import tempfile
    import glob
    import time
    
    try:
        job_pattern = os.path.join(tempfile.gettempdir(), "scraping_job_*.json")
        job_files = glob.glob(job_pattern)
        
        current_time = time.time()
        
        for job_file in job_files:
            try:
                # Check if file is older than 24 hours (86400 seconds)
                if current_time - os.path.getmtime(job_file) > 86400:
                    os.remove(job_file)
                    print(f"Cleaned up old job file: {job_file}")
            except Exception as e:
                print(f"Error cleaning up job file {job_file}: {e}")
    except Exception as e:
        print(f"Error during job file cleanup: {e}")

# Clean up old job files on startup
cleanup_old_job_files()

if __name__ == "__main__":
    print("Starting Spotify Monthly Listener Tracker...")
    app.run(debug=True, host="127.0.0.1", port=5000)
