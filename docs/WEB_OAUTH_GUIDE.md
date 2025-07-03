# Web-Based Spotify OAuth Setup Guide

## Overview
The admin panel now supports fully web-based Spotify authentication. You can log in with your Spotify account directly from the browser and follow artists without needing to run command-line scripts.

## Setup Steps

### 1. Make sure your Spotify App has the correct redirect URI
In your Spotify Developer Dashboard (https://developer.spotify.com/dashboard):
- Go to your app settings
- Under "Redirect URIs", make sure you have: `http://127.0.0.1:5000/callback`
- Click "Save"

### 2. Environment Configuration
The `.env` file in the app directory should contain:
```
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:5000/callback
FLASK_SECRET_KEY=your-secret-key-for-sessions
```

**Note:** The app now uses a single Spotify account for all operations. You no longer need separate "main" and "scrape" account credentials.

### 3. Start the Flask App
```bash
cd "app/spotify-listener-tracker"
python app.py
```

The app will start on http://127.0.0.1:5000

## How to Use

### Admin Panel Access
1. Go to http://127.0.0.1:5000/admin
2. You'll see an authentication status at the top:
   - **Red warning**: Not logged in - shows "Login with Spotify" button
   - **Green success**: Logged in - shows your Spotify username and "Logout" button

### Authentication Flow
1. Click "Login with Spotify" in the admin panel
2. You'll be redirected to Spotify's authorization page
3. Grant permissions to your app
4. You'll be redirected back to the admin panel, now logged in
5. The authentication status will update to show you're connected

### Following Artists
With the new web-based system, you can:

1. **Directly Add/Follow Artists**: Admins can add and follow artists for tracking immediately—no suggestions or approvals required.

### Authentication States
- **Not Authenticated**: Follow buttons will show a warning message
- **Authenticated**: Follow buttons will work directly
- **Authentication Expired**: The system will prompt you to log in again

## Features

### Automatic Token Management
- Tokens are stored in the Flask session (browser-based)
- Automatic token refresh when needed
- Clear error messages when authentication is required

### User Feedback
- Success/error messages for all actions
- Visual authentication status indicator
- Confirmation dialogs for important actions

### Seamless Integration
- No need to run command-line scripts for authentication
- All admin actions can be performed from the web interface
- Real-time updates after actions

## API Endpoints

### Authentication Endpoints
- `GET /login` - Start Spotify OAuth flow
- `GET /callback` - Handle OAuth callback
- `GET /logout` - Clear authentication
- `GET /auth_status` - Check authentication status (JSON)

### Admin Endpoints
- `GET /admin` - Admin panel interface
- `POST /admin/follow_artist` - Follow artist on Spotify

## Troubleshooting

### Login Issues
1. Check your Spotify app's redirect URI settings
2. Make sure the Flask app is running on port 5000
3. Clear your browser cache/cookies
4. Check the browser console for JavaScript errors

### Follow Issues
1. Make sure you're logged in (green status indicator)
2. Check that the artist has a valid Spotify ID
3. Verify your Spotify account has permission to follow artists

### Session Issues
1. The authentication is session-based and will expire when you close the browser
2. For persistent authentication across browser sessions, tokens would need to be stored differently

## Migration from Script-Based Authentication

**Note:** The legacy suggestion/approval workflow and related scripts are no longer supported. All artist management is now performed directly in the admin panel.
