import requests
import base64
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
token_url = os.getenv('SPOTIFY_TOKEN_URL', 'https://accounts.spotify.com/api/token')

# Ensure the cache file is always in the app\spotify-listener-tracker directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cache_file = os.path.join(BASE_DIR, "spotify_token_cache.json")

def request_new_token():
    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    resp = requests.post(token_url, headers=headers, data=data)
    resp.raise_for_status()
    token_info = resp.json()
    token_info['expires_at'] = int(time.time()) + token_info['expires_in'] - 60  # 60s buffer
    with open(cache_file, "w") as f:
        json.dump(token_info, f)
    return token_info['access_token']

def get_token():
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            token_info = json.load(f)
        if token_info.get('expires_at', 0) > int(time.time()):
            return token_info['access_token']
    return request_new_token()

# Usage example:
if __name__ == "__main__":
    print(get_token())