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
                    "url": f"https://open.spotify.com/artist/{artist['id']}"
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
    Main workflow: authenticate, fetch followed artists, and save to file.
    """
    args = parse_args()

    # --- Ensure output is always in the results folder unless absolute path is given ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    if not os.path.isabs(args.output):
        output_path = os.path.join(results_dir, os.path.basename(args.output))
    else:
        output_path = args.output
    # -------------------------------------------------------------------------------

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

    # Check if output file exists and handle according to --no-prompt flag
    if os.path.exists(output_path) and not args.no_prompt:
        while True:
            confirm = input(f"File {output_path} exists. Overwrite? (y/N): ").strip().lower()
            if confirm in ('y', 'n', ''):
                break
            print("Please enter 'y' or 'n'.")
        if confirm != 'y':
            print("Aborted by user.")
            sys.exit(1)

    # Fetch followed artists and save to file
    artist_list = get_followed_artists(sp, limit=args.limit)
    if not artist_list:
        print("No followed artists found for this user.")
    save_artist_list(artist_list, output_path)

    # Print summary report
    report(artist_list, output_path)

    # Inform the user of successful completion and exit with code 0
    print(f"Done! Results saved to {output_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()