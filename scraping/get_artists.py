"""
get_artists.py
--------------
Retrieves the list of artists followed by the authenticated user on Spotify
and saves their names and URLs to a JSON file with the current date in the filename.
"""

import os
import json
import logging
import argparse
from datetime import datetime
import sys

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from tqdm import tqdm


def setup_logging(log_file):
    """
    Configure logging to file for this script.
    """
    logging.basicConfig(
        filename=log_file,
        filemode='a',
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO
    )


def get_followed_artists(sp, limit=None):
    """
    Fetch all followed artists for the authenticated user.
    Returns a list of dicts with artist name and URL.
    """

    artist_list = []
    after = None
    total_fetched = 0

    # First call to get the total number of followed artists
    try:
        results = sp.current_user_followed_artists(limit=50, after=after)
    except Exception as e:
        logging.error(f"Error fetching artists: {e}")
        return artist_list

    if 'artists' not in results or 'total' not in results['artists']:
        logging.error("Unexpected response structure from Spotify API.")
        return artist_list
    total = results['artists']['total']
    if limit and limit < total:
        total = limit

    # Set up progress bar format (matches scrape.py)
    bar_format = (
        "{l_bar}{bar}| {n_fmt}/{total_fmt} artists | Elapsed: {elapsed} | ETA: {remaining}"
    )

    # Only show progress bar and color if running in a real terminal
    is_tty = sys.stdout.isatty()

    tqdm_kwargs = dict(
        total=total,
        desc="Fetching artists",
        bar_format=bar_format if is_tty else None,
        colour="#1DB954" if is_tty else None,  # Use 'colour' not 'color'
        disable=not is_tty,
        dynamic_ncols=is_tty,
        file=sys.stdout
    )

    with tqdm(**tqdm_kwargs) as pbar:
        while True:
            artists = results['artists']['items']
            if not artists:
                break
            for artist in artists:
                artist_list.append({
                    "artist_name": artist['name'],
                    "url": f"https://open.spotify.com/artist/{artist['id']}",
                    "artist_id": artist['id']
                })
                total_fetched += 1
                pbar.update(1)
                # Break if we have fetched the requested limit
                if limit and total_fetched >= limit:
                    return artist_list
            # Pagination: get the next batch
            if results['artists']['next']:
                after = artists[-1]['id']
                try:
                    results = sp.current_user_followed_artists(limit=50, after=after)
                except Exception as e:
                    logging.error(f"Error fetching artists: {e}")
                    break
            else:
                break
    return artist_list


def save_artist_list(artist_list, output_path):
    """
    Save the artist list to a JSON file.
    """
    try:
        # Ensure the output directory exists, if any
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(artist_list, f, indent=2)
        logging.info(f"Saved {len(artist_list)} artists to {output_path}")
        print(f"Saved {len(artist_list)} artists to {output_path}")
    except Exception as e:
        logging.error(f"Error saving artist list: {e}")
        print(f"Failed to save artist list: {e}")


def load_master_artist_list(master_path):
    if os.path.exists(master_path):
        with open(master_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_master_artist_list(artist_list, master_path):
    output_dir = os.path.dirname(master_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(master_path, 'w', encoding='utf-8') as f:
        json.dump(artist_list, f, indent=2)
    logging.info(f"Saved {len(artist_list)} artists to {master_path}")
    print(f"Saved {len(artist_list)} artists to {master_path}")


def update_master_artist_list(master_list, current_list, today):
    """
    Update the master artist list with current followed artists.
    Marks removed artists and adds new ones.
    """
    current_urls = {a['url'] for a in current_list}
    master_urls = {a['url'] for a in master_list}

    # Mark removed artists
    for artist in master_list:
        if artist['url'] not in current_urls and not artist.get('removed', False):
            artist['removed'] = True
            artist['date_removed'] = today
        # If artist was previously removed but is now back, unmark as removed
        if artist['url'] in current_urls and artist.get('removed', False):
            artist['removed'] = False
            artist.pop('date_removed', None)

    # Add new artists
    for artist in current_list:
        if artist['url'] not in master_urls:
            artist['date_added'] = today
            artist['removed'] = False
            master_list.append(artist)

    return master_list


def parse_args():
    """
    Parse command-line arguments for output file location, logging, and limits.
    """
    today = datetime.now().strftime('%Y%m%d')
    parser = argparse.ArgumentParser(
        description="Spotify Followed Artists Exporter"
    )
    parser.add_argument(
        '--output',
        type=str,
        default=f'results/spotify-artist-urls-{today}.json',
        help='Output JSON file (default: results/spotify-artist-urls-YYYYMMDD.json)'
    )
    parser.add_argument(
        '--no-prompt',
        action='store_true',
        default=False,
        help='Do not prompt for user input (for automation)'
    )
    parser.add_argument(
        '--log',
        type=str,
        default='get_artists.log',
        help='Log file location (default: get_artists.log)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of artists to fetch (default: all)'
    )
    return parser.parse_args()


def report(artist_list, output_path):
    """
    Print a summary report of the export session.
    """
    print("\nSummary:")
    print(f"  Total artists exported: {len(artist_list)}")
    print(f"  Output file: {output_path}")


def main():
    """
    Main workflow: authenticate, fetch followed artists, and update master file.
    """
    args = parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    master_path = os.path.join(results_dir, "spotify-followed-artists-master.json")

    # --- Ensure logs are always in the script directory unless absolute path is given ---
    if not os.path.isabs(args.log):
        log_path = os.path.join(script_dir, os.path.basename(args.log))
    else:
        log_path = args.log
    # -------------------------------------------------------------------------------

    # Set up logging
    setup_logging(log_path)

    load_dotenv()

    # Retrieve credentials from environment variables
    CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
    REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

    # Prompt if credentials are missing
    if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
        print("Spotify credentials not found in environment variables.")
        input("Press Enter after you have set up your .env file...")
        sys.exit(1)

    # Attempt to authenticate with Spotify
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope='user-follow-read'
        ))
    except Exception as e:
        logging.error(f"Spotify authentication failed: {e}")
        print(f"Spotify authentication failed: {e}")
        sys.exit(1)

    print("A browser window will open for Spotify authentication. Please log in and authorize the app.")

    today = datetime.now().strftime('%Y-%m-%d')

    # Fetch followed artists
    artist_list = get_followed_artists(sp, limit=args.limit)
    if not artist_list:
        print("No followed artists found for this user.")

    # Load master, update, and save
    master_list = load_master_artist_list(master_path)
    before_urls = {a['url'] for a in master_list}
    before_removed = {a['url'] for a in master_list if a.get('removed', False)}

    updated_master = update_master_artist_list(master_list, artist_list, today)
    after_urls = {a['url'] for a in updated_master}
    after_removed = {a['url'] for a in updated_master if a.get('removed', False)}

    num_added = len(after_urls - before_urls)
    num_removed = len(after_removed - before_removed)

    save_master_artist_list(updated_master, master_path)

    # Print summary report
    print("\nSummary:")
    print(f"  Total artists in master: {len(updated_master)}")
    print(f"  New artists added: {num_added}")
    print(f"  Artists marked as removed: {num_removed}")
    print(f"  Output file: {master_path}")

    print(f"Done! Master artist list saved to {master_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()