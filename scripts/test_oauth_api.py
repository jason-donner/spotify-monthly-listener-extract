#!/usr/bin/env python3
"""
Test script to verify the web-based OAuth functionality works correctly.
This script tests the API endpoints without requiring browser interaction.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_auth_status():
    """Test the authentication status endpoint"""
    response = requests.get(f"{BASE_URL}/auth_status")
    print(f"Auth Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Authenticated: {data.get('authenticated')}")
        if data.get('authenticated'):
            user = data.get('user', {})
            print(f"User: {user.get('display_name', user.get('id', 'Unknown'))}")
    else:
        print(f"Error: {response.text}")
    return response


def test_admin_suggestions():


def test_follow_artist_without_auth():
    """Test following an artist without authentication (should fail gracefully)"""
    test_data = {
        "artist_id": "test_id_123",
        "artist_name": "Test Artist"
    }
    
    response = requests.post(
        f"{BASE_URL}/admin/follow_artist",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nFollow Artist (No Auth): {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        print(f"Auth Required: {data.get('auth_required', False)}")
    else:
        print(f"Error: {response.text}")
    return response

if __name__ == "__main__":
    print("Testing Web-Based OAuth API Endpoints")
    print("=" * 50)
    
    try:
        # Test authentication status
        test_auth_status()
        

        # Test admin suggestions (OBSOLETE)
        test_admin_suggestions()
        
        # Test follow artist without auth
        test_follow_artist_without_auth()
        
        print("\n" + "=" * 50)
        print("Test completed!")
        print("\nTo test the full OAuth flow:")
        print("1. Open http://127.0.0.1:5000/admin in your browser")
        print("2. Click 'Login with Spotify'")
        print("3. Complete the Spotify authorization")
        print("4. Try following an artist from the admin panel")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Flask app.")
        print("Make sure the Flask app is running on port 5000:")
        print("  cd app/spotify-listener-tracker")
        print("  python app.py")
