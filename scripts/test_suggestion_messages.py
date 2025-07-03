raise SystemExit("OBSOLETE: This script is no longer used. All suggestion/approval/processing logic has been removed from the project.")
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
