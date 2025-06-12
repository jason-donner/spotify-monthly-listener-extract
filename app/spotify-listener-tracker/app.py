from flask import Flask, render_template, request, jsonify
import json
import requests
import os
from get_token import get_token

app = Flask(__name__)

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
    return render_template("index.html", results=results, query=query)

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

if __name__ == "__main__":
    app.run(debug=True)