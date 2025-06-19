import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="user-follow-read",
    client_id="YOUR_MAIN_CLIENT_ID",
    client_secret="YOUR_MAIN_CLIENT_SECRET",
    redirect_uri="YOUR_REDIRECT_URI"
))

def get_followed_artists():
    artists = []
    after = None
    while True:
        results = sp.current_user_followed_artists(limit=50, after=after)
        items = results['artists']['items']
        for artist in items:
            artists.append({
                "artist_name": artist['name'],
                "url": artist['external_urls']['spotify'],
                "date_added": "",  # You can’t get this from Spotify, leave blank or use today
                "removed": False
            })
        if len(items) < 50:
            break
        after = items[-1]['id']
    return artists

artists = get_followed_artists()
with open('src/results/spotify-followed-artists-master.json', 'w', encoding='utf-8') as f:
    json.dump(artists, f, ensure_ascii=False, indent=2)