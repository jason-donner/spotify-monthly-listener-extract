#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '.')

print("=== Debug Spotify Token Issue ===")

# Check environment variables
print(f"SPOTIPY_CLIENT_ID: {os.getenv('SPOTIPY_CLIENT_ID')}")
print(f"SPOTIPY_CLIENT_SECRET: {os.getenv('SPOTIPY_CLIENT_SECRET')[:10]}..." if os.getenv('SPOTIPY_CLIENT_SECRET') else "None")

# Test dotenv loading
from dotenv import load_dotenv
print(f"\nLoading .env file...")
load_dotenv()
print(f"After load_dotenv - Client ID: {os.getenv('SPOTIPY_CLIENT_ID')}")
print(f"After load_dotenv - Client Secret: {os.getenv('SPOTIPY_CLIENT_SECRET')[:10]}..." if os.getenv('SPOTIPY_CLIENT_SECRET') else "None")

# Test get_token module
print(f"\n=== Testing get_token module ===")
import get_token
print(f"get_token.client_id: {get_token.client_id}")
print(f"get_token.client_secret: {get_token.client_secret[:10]}..." if get_token.client_secret else "None")

# Test token request
print(f"\n=== Testing token request ===")
try:
    token = get_token.request_new_token()
    print(f"SUCCESS: Token obtained (length: {len(token)})")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
