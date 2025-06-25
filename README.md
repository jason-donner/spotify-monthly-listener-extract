# Spotify Monthly Listener Extract

A modern web-based system for tracking Spotify artists' monthly listener counts with automated scraping capabilities.

---

## 🌟 Features

- **🎵 Web-based Artist Management** - Manage followed artists through a modern web interface
- **✨ Artist Suggestion System** - Users can suggest new artists to track
- **👨‍💼 Admin Panel** - Review, approve, and manage artist suggestions
- **🔗 Direct Spotify Integration** - Follow artists directly from the web interface using OAuth
- **🤖 Automated Scraping** - Collect monthly listener data automatically
- **📊 Data Persistence** - JSON storage with master results tracking
- **📝 Comprehensive Logging** - Detailed logs for troubleshooting

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8+
- Google Chrome browser
- ChromeDriver (compatible with your Chrome version)
- Spotify Developer App (create at https://developer.spotify.com/dashboard)

### 2. Setup Environment Variables
Create a `.env` file in the project root:
```env
SPOTIPY_CLIENT_ID=your_spotify_app_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_app_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:5000/admin/callback
FLASK_SECRET_KEY=your-secret-key-for-sessions
CHROMEDRIVER_PATH=C:\Windows\System32\chromedriver.exe
```

### 3. Install Dependencies
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 4. Configure Spotify App
In your Spotify Developer Dashboard:
1. Set redirect URI to: `http://127.0.0.1:5000/admin/callback`
2. Add scopes: `user-follow-read user-follow-modify`

### 5. Start the Web Interface
```bash
cd webapp
python app.py
```

### 6. Access the Application
- **Main App**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin

---

## 🎯 How to Use

### Web Interface
1. **Home/Leaderboard**: View artist performance rankings
2. **Search**: Find and explore artist data
3. **Artist Pages**: Detailed views with historical data
4. **Suggest Artists**: Submit new artists for tracking

### Admin Panel
1. **Login**: Click "Login with Spotify" to authenticate
2. **Review Suggestions**: View pending, approved, and rejected suggestions
3. **Manage Artists**: Approve for tracking or following
4. **Follow on Spotify**: Follow artists directly from the interface

### Data Collection
1. **Manual Collection**: Run scripts individually
   ```bash
   python src/get_artists.py    # Fetch followed artists
   python src/scrape.py         # Scrape listener data
   ```

2. **Automated Collection**: Use the batch file
   ```bash
   run_monthly_listener.bat
   ```

---

## 📁 File Structure

```
Spotify Monthly Listener Extract/
├── 📁 app/
│   └── 📁 spotify-listener-tracker/     # Web application
│       ├── app.py                       # Flask application
│       ├── templates/                   # HTML templates
│       └── static/                      # CSS, images
├── 📁 src/                              # Core scripts
│   ├── get_artists.py                   # Fetch artist URLs
│   ├── scrape.py                        # Scrape listener data
│   ├── process_suggestions.py           # Process suggestions
│   └── results/                         # Data files
├── 📁 tests/                            # Test files
├── run_monthly_listener.bat             # Automation script
├── requirements.txt                     # Dependencies
├── .env                                 # Environment variables
└── 📄 Documentation files
```

---

## 🔧 API Endpoints

### Public Endpoints
- `GET /` - Home page/leaderboard
- `GET /search` - Search artists
- `GET /artist/<slug>/<id>` - Artist detail page
- `POST /suggest_artist` - Submit artist suggestion

### Admin Endpoints
- `GET /admin` - Admin panel
- `GET /admin/suggestions` - Get suggestions (JSON)
- `POST /admin/approve_suggestion` - Approve/reject suggestions
- `POST /admin/follow_artist` - Follow artist on Spotify

### Authentication Endpoints
- `GET /login` - Start Spotify OAuth
- `GET /callback` - OAuth callback handler
- `GET /logout` - Clear authentication
- `GET /auth_status` - Check auth status (JSON)

---

## 🛠️ Data Processing Workflow

### 1. Artist Management
```
User Suggestion → Admin Review → Approval → Follow on Spotify → Add to Tracking
```

### 2. Data Collection
```
Get Followed Artists → Scrape Monthly Listeners → Save to JSON → Update Master File
```

### 3. Web Interface
```
Load Data → Display Charts → Search/Filter → Artist Details
```

---

## 🔍 Troubleshooting

### Authentication Issues
- ✅ Check Spotify app redirect URI
- ✅ Verify client credentials in `.env`
- ✅ Clear browser cache/cookies
- ✅ Check Flask app is running on port 5000

### Scraping Issues
- ✅ Ensure ChromeDriver is compatible with Chrome version
- ✅ Check ChromeDriver path in environment variables
- ✅ Verify Spotify login works manually
- ✅ Review `scrape.log` for errors

### Web Interface Issues
- ✅ Check Flask app logs in terminal
- ✅ Verify all dependencies are installed
- ✅ Check browser developer console for JavaScript errors
- ✅ Ensure data files exist in `src/results/`

---

## 📋 Migration from Dual-Account System

If you were using the old dual-account system, see `MIGRATION_GUIDE.md` for detailed migration instructions.

**Key Changes:**
- ❌ No more main/scrape account separation
- ❌ No more `spotify_follow_sync.py` script
- ✅ Single account for all operations
- ✅ Web-based OAuth authentication
- ✅ Simplified setup and configuration

---

## 📚 Additional Documentation

- `WEB_OAUTH_GUIDE.md` - Web-based OAuth setup guide
- `MIGRATION_GUIDE.md` - Migration from dual-account system
- `WORKFLOW.md` - Detailed workflow documentation

---

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the system.

---

## 📄 License

See `LICENSE.txt` for license information.
