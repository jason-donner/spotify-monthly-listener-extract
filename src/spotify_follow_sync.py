"""
Synchronize followed artists between a main Spotify account and a scraping account.
This script logs into both accounts and ensures the scraping account follows all artists that the main account follows.
"""

import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth


# Load environment variables from a .env file for local development (if present)
load_dotenv()

# --- Main account credentials ---
MAIN_CLIENT_ID = os.getenv("MAIN_CLIENT_ID")
MAIN_CLIENT_SECRET = os.getenv("MAIN_CLIENT_SECRET")
MAIN_REDIRECT_URI = os.getenv("MAIN_REDIRECT_URI")

# --- Scraping account credentials ---
SCRAPE_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SCRAPE_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SCRAPE_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

def get_followed_artist_ids(sp):
    """
    Retrieve all artist IDs followed by the current user.

    Args:
        sp (spotipy.Spotify): An authenticated Spotipy client instance.

    Returns:
        set: A set of artist IDs followed by the user.
    """
    ids = []
    after = None
    while True:
        results = sp.current_user_followed_artists(limit=50, after=after)
        items = results['artists']['items']
        ids.extend([artist['id'] for artist in items])
        if len(items) < 50:
            break
        after = items[-1]['id']
    return set(ids)

def force_fresh_login(cache_path):
    if os.path.exists(cache_path):
        os.remove(cache_path)

def main():
    main_cache = ".cache-main"
    scrape_cache = ".cache-scrape"

    force_fresh_login(main_cache)
    force_fresh_login(scrape_cache)

    # --- Main account authentication ---
    main_auth = SpotifyOAuth(
        client_id=MAIN_CLIENT_ID,
        client_secret=MAIN_CLIENT_SECRET,
        redirect_uri=MAIN_REDIRECT_URI,
        scope="user-follow-read",
        cache_path=main_cache
    )
    main_auth_url = main_auth.get_authorize_url()
    print("\nIMPORTANT: Open this URL in your browser for your MAIN account login:")
    print(main_auth_url)
    input("After authorizing and granting access for the MAIN account, press Enter here to continue...")

    sp_main = spotipy.Spotify(auth_manager=main_auth)
    print("Main account:", sp_main.me()["id"])
    main_artist_ids = get_followed_artist_ids(sp_main)
    print(f"Main account follows {len(main_artist_ids)} artists.")

    # --- Scraping account authentication ---
    scrape_auth = SpotifyOAuth(
        client_id=SCRAPE_CLIENT_ID,
        client_secret=SCRAPE_CLIENT_SECRET,
        redirect_uri=SCRAPE_REDIRECT_URI,
        scope="user-follow-read user-follow-modify",
        cache_path=scrape_cache
    )
    scrape_auth_url = scrape_auth.get_authorize_url()
    print("\nIMPORTANT: Open this URL in your browser (preferably incognito/private mode) for your SCRAPING account login:")
    print(scrape_auth_url)
    input("After authorizing and granting access for the SCRAPING account, press Enter here to continue...")

    sp_scrape = spotipy.Spotify(auth_manager=scrape_auth)
    print("Scraping account:", sp_scrape.me()["id"])
    scrape_artist_ids = get_followed_artist_ids(sp_scrape)
    print(f"Scraping account follows {len(scrape_artist_ids)} artists.")

    to_follow = list(main_artist_ids - scrape_artist_ids)
    print(f"Need to follow {len(to_follow)} new artists on scraping account.")

    for i in range(0, len(to_follow), 50):
        batch = to_follow[i:i+50]
        sp_scrape.user_follow_artists(batch)
        print(f"Followed batch {i//50 + 1}: {len(batch)} artists.")

    print("Sync complete!")

if __name__ == "__main__":
    main()