# Migration Guide: Single Account Setup

## Overview
The system has been simplified to use only one Spotify account instead of separate "main" and "scrape" accounts. This makes the setup much easier and eliminates the need for account synchronization.

## What Changed

### Before (Dual Account System)
- **Main Account**: Your personal Spotify account
- **Scrape Account**: Separate account for data collection
- **Sync Process**: Script to sync followed artists between accounts
- **Complex Setup**: Multiple sets of credentials needed

### After (Single Account System)
- **Single Account**: One Spotify account for everything
- **Web-Based Management**: Manage followed artists through web interface
- **Simplified Setup**: Only one set of credentials needed
- **No Sync Required**: No more account synchronization

## Migration Steps

### 1. Update Environment Variables
Remove the old main account credentials from your `.env` files:

**Remove these lines:**
```
MAIN_CLIENT_ID=...
MAIN_CLIENT_SECRET=...
MAIN_REDIRECT_URI=...
```

**Keep only:**
```
SPOTIPY_CLIENT_ID=your_spotify_app_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_app_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:5000/callback
FLASK_SECRET_KEY=your-secret-key-for-sessions
```

### 2. Choose Your Primary Account
Decide which Spotify account you want to use:
- Use your **personal account** if you want to follow artists directly
- Use a **dedicated tracking account** if you prefer separation

### 3. Update Spotify App Settings
In your Spotify Developer Dashboard:
1. Use the credentials from the account you chose
2. Ensure the redirect URI is set to: `http://127.0.0.1:5000/callback`
3. Make sure your app has the required scopes: `user-follow-read user-follow-modify`

### 4. Clean Up Old Files
The following files are no longer needed:
- `src/spotify_follow_sync.py` (now deprecated)
- Any `.cache-main` or `.cache-scrape` files (old authentication caches)

### 5. Test the New System
1. Start the Flask app: `python app.py`
2. Go to `http://localhost:5000/admin`
3. Click "Login with Spotify"
4. Authorize with your chosen account
5. Test following an artist from the admin panel

## Benefits of Single Account System

### Simplified Setup
- Only one set of Spotify app credentials needed
- No complex authentication flow for multiple accounts
- Easier to understand and maintain

### Better User Experience
- Direct integration with your chosen Spotify account
- Real-time following through web interface
- No need to run sync scripts

### Reduced Complexity
- Fewer moving parts
- Less potential for authentication issues
- Simpler troubleshooting

## Frequently Asked Questions

### Q: What if I was using separate accounts for privacy?
**A:** You can still use a separate account - just use that account's credentials in the `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET` variables.

### Q: Will my existing followed artists data be affected?
**A:** No, your existing data in `spotify-followed-artists-master.json` remains unchanged. The system will continue to work with your existing data.

### Q: Can I still use the command-line scripts?
**A:** Yes, `process_suggestions.py` still works and will use the same single account. The web interface and command-line scripts are now fully compatible.

### Q: What about my existing suggestions?
**A:** All existing suggestions in `artist_suggestions.json` will continue to work normally. You can process them through either the web interface or the command-line script.

## Troubleshooting

### Authentication Issues
1. Make sure you're using the correct Spotify app credentials
2. Verify the redirect URI is set correctly in your Spotify app
3. Clear browser cache/cookies if having login issues

### Following Issues
1. Ensure your Spotify account has permission to follow artists
2. Check that the artist IDs are valid
3. Verify your app has the `user-follow-modify` scope

### Migration Problems
If you encounter issues after migration:
1. Double-check your `.env` file contains only the single account credentials
2. Remove any old cache files (`.cache-*`)
3. Restart the Flask app
4. Try the authentication flow again

## 🚀 Auto-Follow System Migration (June 2025)

### New Feature Overview
The system now automatically follows suggested artists, eliminating most manual admin work.

### Migration for Existing Installations

#### Step 1: Update to Latest Code
```bash
git pull origin main
```

#### Step 2: Fix Stuck Suggestions
If you have suggestions that were approved before the auto-follow system:

**Option A: Use Admin Panel**
1. Go to Admin Panel → Maintenance section
2. Click "Fix Stuck Suggestions"
3. Confirm the action

**Option B: Use Command Line**
```bash
python scripts/fix_stuck_suggestions.py
```

#### Step 3: Verify Migration
1. Check Admin Panel → Processed tab
2. Ensure all approved suggestions show "Already Followed" badge
3. Verify artists appear in followed artists list

### What the Migration Does
- ✅ Identifies approved suggestions missing follow data
- ✅ Adds `already_followed: true` and `admin_action_date` fields
- ✅ Adds artists to followed artists database
- ✅ Preserves all original suggestion data

### Before Migration
```json
{
  "artist_name": "Example Artist",
  "status": "approved",
  "timestamp": "2025-06-25T10:00:00"
  // Missing follow data
}
```

### After Migration
```json
{
  "artist_name": "Example Artist", 
  "status": "approved",
  "timestamp": "2025-06-25T10:00:00",
  "already_followed": true,
  "admin_action_date": "2025-06-25T22:00:00"
}
```

## Need Help?
If you encounter issues during migration, check:
1. The Flask app logs for error messages
2. Your browser's developer console for JavaScript errors
3. The `process_suggestions.log` file for script errors
