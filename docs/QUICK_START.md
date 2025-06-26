# Quick Start Guide

## 🚀 New User Experience (Auto-Follow System)

### For End Users
1. **Visit the Web App**: Go to http://localhost:5000
2. **Suggest Artists**: Use the suggestion form to add new artists
3. **Instant Results**: Artists are automatically approved and followed
4. **No Waiting**: Start seeing data in the next scraping run

### For Admins
1. **Set Up Admin Access**: Configure password and Spotify authentication
2. **Monitor**: Use admin panel to review processed suggestions
3. **Maintain**: Minimal manual intervention needed

---

## Setting Up Admin Access

### Using a .env File (Recommended)
Create a `.env` file in the `webapp` directory:
```env
ADMIN_PASSWORD=your_secure_password_here
FLASK_DEBUG=false
FLASK_SECRET_KEY=your_secret_key_here

# Spotify API credentials
SPOTIPY_CLIENT_ID=your_spotify_app_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_app_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:5000/admin/callback
```

Then start the app:
```bash
cd webapp
python app.py
```

## First Time Setup

1. **Set Admin Password** (required)
   ```powershell
   $env:ADMIN_PASSWORD = "admin123"
   ```

2. **Start the Web App**
   ```powershell
   cd webapp
   python app.py
   ```

3. **Access Admin Panel**
   - Go to: http://127.0.0.1:5000/admin_login
   - Login with your password
   - Admin panel will be at: http://127.0.0.1:5000/admin/

4. **Test Scraping**
   - Click "Run Scraping" in the admin panel
   - Choose your options (headless recommended)
   - Monitor progress in real-time

5. **View Leaderboard**
   - Go to: http://127.0.0.1:5000/leaderboard
   - Shows top artists for current month (e.g., "June 2025")
   - Automatically updates to new month when calendar changes

## Common Issues

### "Failed to fetch" Error
- ✅ **Fixed**: Ensure `ADMIN_PASSWORD` environment variable is set
- ✅ **Fixed**: Admin routes now have proper authentication

### Admin Login Not Working
- Check that `ADMIN_PASSWORD` environment variable is set
- Restart the Flask app after setting the environment variable
- Check the console for "ADMIN_PASSWORD environment variable not set!" message

### Scraping Issues
- Ensure Chrome browser is installed and updated
- Try running with `--headless` flag first
- Check network connectivity to Spotify

## Security Notes

- **Never commit passwords to version control**
- Use strong passwords in production
- Consider using a `.env` file for easier management
- Rotate passwords regularly in production environments
