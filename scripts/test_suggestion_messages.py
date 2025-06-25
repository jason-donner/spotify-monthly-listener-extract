#!/usr/bin/env python3
"""
Test script to verify the different suggestion messages
"""

import requests
import json

# Test different scenarios for suggestion messages
test_cases = [
    {
        "name": "Test Case 1: Artist already suggested",
        "artist_name": "Youth Novel",  # This is in suggestions
        "spotify_url": "https://open.spotify.com/artist/0YxhqoWVBE2dzg1vAyE7JA",
        "spotify_id": "0YxhqoWVBE2dzg1vAyE7JA",
        "expected_message": "already been suggested"
    },
    {
        "name": "Test Case 2: Artist already followed on Spotify (not in suggestions)",
        "artist_name": "Waving",  # This is in the followed list but not in suggestions
        "spotify_url": "https://open.spotify.com/artist/5fFJtAUKz4FbplhVoxlIA4",
        "spotify_id": "5fFJtAUKz4FbplhVoxlIA4",
        "expected_message": "already following"
    },
    {
        "name": "Test Case 3: Brand new artist suggestion",
        "artist_name": "Another Brand New Test Artist",
        "spotify_url": "https://open.spotify.com/artist/AnotherNewTestArtistID456",
        "spotify_id": "AnotherNewTestArtistID456",
        "expected_message": "approved and added"
    }
]

def test_suggestion_endpoint():
    url = "http://127.0.0.1:5000/suggest_artist"
    
    print("🧪 Testing Artist Suggestion Messages")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Artist: {test_case['artist_name']}")
        
        payload = {
            "artist_name": test_case["artist_name"],
            "spotify_url": test_case["spotify_url"],
            "spotify_id": test_case["spotify_id"]
        }
        
        try:
            response = requests.post(url, json=payload)
            result = response.json()
            
            print(f"   Response: {result.get('message', 'No message')}")
            
            if test_case["expected_message"] in result.get("message", "").lower():
                print("   ✅ PASS - Message matches expected content")
            else:
                print("   ❌ FAIL - Message doesn't match expected content")
                print(f"   Expected to contain: '{test_case['expected_message']}'")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print()

if __name__ == "__main__":
    test_suggestion_endpoint()
