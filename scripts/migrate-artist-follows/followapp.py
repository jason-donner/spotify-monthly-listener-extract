import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils import load_artist_ids  # Import your utility function

# Load artist IDs from your JSON file
artist_ids = load_artist_ids('migrate-artist-follows/artists.json')
if not artist_ids:
    print("No artist IDs loaded. Check your JSON file and loader function.")
    exit(1)

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="user-follow-modify user-follow-read",
    client_id="5e36297fe74744de9fd4a7cf6c3a9941",
    client_secret="703744d10ba54d779b199134a85333bc",
    redirect_uri="http://127.0.0.1:5000/callback"
))

# Follow artists in batches of 50 (API limit)
successful = 0
failed = 0
for i in range(0, len(artist_ids), 50):
    batch = artist_ids[i:i+50]
    try:
        sp.user_follow_artists(batch)
        successful += len(batch)
        print(f"Successfully followed {len(batch)} artists in this batch.")
    except spotipy.SpotifyException as e:
        failed += len(batch)
        print(f"Error following batch {batch}: {e}")

# Check how many artists you now follow
def get_total_followed_artists(sp):
    total_followed = 0
    after = None
    while True:
        results = sp.current_user_followed_artists(limit=50, after=after)
        artists = results['artists']['items']
        total_followed += len(artists)
        if len(artists) < 50:
            break
        after = artists[-1]['id']
    return total_followed

total = get_total_followed_artists(sp)
print("\nSummary:")
print(f"Attempted to follow {len(artist_ids)} artists.")
print(f"Successfully followed: {successful}")
if failed:
    print(f"Failed to follow: {failed}")
print(f"You now follow {total} artists.")