# Spotify Monthly Listener Extract

A modern web-based system for tracking Spotify artists' monthly listener counts with automated scraping capabilities.

---

## 🎉 Recent Updates (June 2025)

### Data Integrity Verification (June 25, 2025)
- **✅ Clean Data Confirmed** - Comprehensive analysis shows 6,392 entries with zero duplicates
- **🛡️ Prevention System Verified** - Automatic duplicate protection working correctly since implementation
- **📋 Documentation Updated** - Enhanced deduplication guide with verification records
- **🔧 Best Practices Documented** - Clear guidelines for maintaining data integrity

### Real-Time Progress Indicator (June 25, 2025)
- **📊 Live Progress Bar** - Beautiful visual progress bar during scraping operations
- **🎯 Artist Counter** - Shows "current / total" artists being processed in real-time
- **👁️ Current Artist Display** - See exactly which artist is being processed
- **⏱️ Phase Tracking** - Clear status updates (Starting, Scraping, Completed)
- **🔄 Real-Time Updates** - Progress updates every 2 seconds with smooth animations

### Leaderboard Enhancement (June 25, 2025)
- **📅 Current Month Focus** - Leaderboard now shows only current month data (e.g., "June 2025")
- **🎯 Improved Date Display** - Clear month/year display instead of confusing date ranges
- **⚡ Automatic Month Updates** - Automatically switches to new month when the calendar changes
- **📊 Better Data Relevance** - Shows more relevant, timely artist performance data

### Critical Authentication Fix (June 25, 2025)
- **🔐 Fixed "Failed to fetch" Error** - Resolved authentication issues in admin scraping endpoints
- **🛡️ Enhanced Route Security** - Added proper `@admin_login_required` decorators to all admin endpoints
- **⚙️ Environment Variable Support** - Fixed `ADMIN_PASSWORD` environment variable handling
- **🚀 Stable Admin Panel** - All admin functionality now works reliably with proper authentication

### Admin Panel Improvements
- **🚀 Streamlined "Follow & Track" Process** - One-click approval that follows artists and marks suggestions as processed
- **🔧 Fixed Suggestion Tab Management** - Properly moves processed suggestions between tabs
- **📊 Enhanced Filtering Logic** - Accurate categorization of pending, approved, and processed suggestions
- **🐛 Bug Fixes** - Resolved issues with stuck suggestions in "Pending Review"
- **📝 Improved Logging** - Added detailed debug logging for suggestion processing
- **🎨 Modern Admin Login** - Beautiful Spotify-themed login page with improved UX
- **🔒 Secure Authentication** - Environment variable-based password management
- **🛡️ Security Logging** - Comprehensive admin activity and authentication logging
- **📋 Enhanced Scraping Feedback** - Detailed messages showing newly added artists when running "today only" scraping

### Search & Discovery Enhancements  
- **🎵 Top Tracks Preview** - Added artist top tracks preview on search page
- **✨ Improved UI/UX** - Better visual feedback and user experience
- **🎯 Refined Artist Selection** - Top tracks appear after artist selection, not on hover

### Backend Improvements
- **🔄 Enhanced Suggestion Lifecycle** - Better handling of suggestion status transitions
- **⚡ Optimized Admin Actions** - Combined follow and processing into single operation
- **🛡️ Error Handling** - More robust error handling and user feedback
- **📋 Data Consistency** - Fixed data structure inconsistencies in suggestion processing

### Code Quality Enhancements
- **🔍 Improved Logging** - Added detailed debug logging for better troubleshooting
- **🧹 Code Cleanup** - Removed redundant buttons and streamlined JavaScript
- **📊 Better State Management** - Enhanced frontend filtering and tab management
- **🎯 Consistent Data Flow** - Unified suggestion processing workflow
- **📝 Centralized Logging** - Structured logging with file rotation and admin security monitoring

---

## 🌟 Features

- **🎵 Web-based Artist Management** - Manage followed artists through a modern web interface
- **📅 Current Month Leaderboard** - Track artist performance for the current calendar month (e.g., "June 2025")
- **📊 Real-Time Progress Tracking** - Live progress bars and artist counters during scraping operations
- **✨ Artist Suggestion System** - Users can suggest new artists to track
- **👨‍💼 Admin Panel** - Review, approve, and manage artist suggestions with real-time feedback
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

The project has separate requirements for different components:

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install main dependencies
pip install -r requirements.txt

# Install webapp dependencies
cd webapp
pip install -r requirements.txt

# Install scraping dependencies
cd ../scraping
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

### 6. Set Admin Password (Required for Admin Access)
Set your admin password as an environment variable:
```powershell
# Windows PowerShell
$env:ADMIN_PASSWORD = "your_secure_password_here"

# Linux/Mac
export ADMIN_PASSWORD="your_secure_password_here"
```

### 7. Access the Application
- **Main App**: http://localhost:5000
- **Admin Login**: http://localhost:5000/admin_login
- **Admin Panel**: http://localhost:5000/admin (requires login)

---

## 🎯 How to Use

### Web Interface
1. **Home/Leaderboard**: View artist performance rankings
2. **Search**: Find and explore artist data
3. **Artist Pages**: Detailed views with historical data
4. **Suggest Artists**: Submit new artists for tracking

### Admin Panel
1. **Login**: Visit `/admin_login` and enter your admin password
2. **OAuth Setup**: After login, click "Login with Spotify" to authenticate API access
3. **Review Suggestions**: View pending, approved, and rejected suggestions
4. **Process Suggestions**: 
   - **🎵 Follow & Track** - Immediately follows artist on Spotify and adds to tracking (direct to processed)
   - **👁️ Track Only** - Adds to tracking without following on Spotify (direct to processed)
   - **✗ Reject** - Rejects the suggestion
5. **Tab Management**: Suggestions automatically move between tabs based on status:
   - **Pending Review** - New suggestions awaiting admin action
   - **Processed** - Completed suggestions (followed/tracked)
   - **Rejected** - Declined suggestions

### Data Collection
1. **Manual Collection**: Run scripts individually
   ```bash
   cd scraping
   python get_artists.py    # Fetch followed artists
   python scrape.py         # Scrape listener data
   ```

2. **Automated Collection**: Use the batch file
   ```bash
   cd scripts
   run_monthly_listener.bat
   ```

---

## 📁 File Structure

```
Spotify Monthly Listener Extract/
├── 📁 webapp/                           # Web application
│   ├── app.py                           # Flask application
│   ├── app/                             # App modules
│   ├── templates/                       # HTML templates
│   ├── static/                          # CSS, images
│   └── requirements.txt                 # Web app dependencies
├── 📁 scraping/                         # Core scraping scripts
│   ├── get_artists.py                   # Fetch artist URLs
│   ├── scrape.py                        # Scrape listener data
│   ├── process_suggestions.py           # Process suggestions
│   └── requirements.txt                 # Scraping dependencies
├── 📁 scripts/                          # Utility scripts
│   ├── run_monthly_listener.bat         # Automation script
│   └── *.py                             # Various utility scripts
├── 📁 data/
│   └── results/                         # JSON data files
├── 📁 docs/                             # Documentation
├── 📁 tests/                            # Test files
├── requirements.txt                     # Main dependencies
└── .env                                 # Environment variables
```

---

## 📂 Project Structure Details

### Core Components
- **`webapp/`** - Flask web application with admin panel and user interface
- **`scraping/`** - Python scripts for data collection and processing
- **`scripts/`** - Utility scripts and automation tools
- **`data/results/`** - JSON data files with artist and listener information
- **`docs/`** - Documentation and guides
- **`tests/`** - Unit tests for the application

### Key Files
- **`webapp/app.py`** - Main Flask application entry point
- **`scraping/get_artists.py`** - Fetches followed artists from Spotify
- **`scraping/scrape.py`** - Scrapes monthly listener data
- **`scripts/run_monthly_listener.bat`** - Automated data collection script

---

## 🔧 API Endpoints

### Public Endpoints
- `GET /` - Home page/leaderboard
- `GET /search` - Search artists with top tracks preview
- `GET /artist/<slug>/<id>` - Artist detail page
- `POST /suggest_artist` - Submit artist suggestion
- `GET /api/artist/<artist_id>/top-tracks` - Get artist's top tracks (JSON)

### Admin Endpoints
- `GET /admin` - Admin panel interface
- `GET /admin/suggestions` - Get all suggestions (JSON)
- `POST /admin/approve_suggestion` - Approve/reject suggestions
- `POST /admin/follow_artist` - Follow artist on Spotify and process suggestion
- `POST /admin/run_scraping` - Start automated scraping job
- `POST /admin/process_suggestions` - Process approved suggestions in batch
- `GET /admin/scraping_status/<job_id>` - Check scraping job status

### Authentication Endpoints
- `GET /login` - Start Spotify OAuth
- `GET /callback` - OAuth callback handler
- `GET /logout` - Clear authentication
- `GET /auth_status` - Check auth status (JSON)

---

## 🛠️ Data Processing Workflow

### 1. Artist Management
```
User Suggestion → Admin Review → Direct Processing (Follow & Track OR Track Only) → Processed
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

### Admin Panel Issues
- ✅ **Suggestions stuck in "Pending Review"**: Check suggestion status in `artist_suggestions.json`
- ✅ **"Follow & Track" not working**: Ensure Spotify authentication is active
- ✅ **Tab counts incorrect**: Refresh the page or check filtering logic in browser console
- ✅ **Processing errors**: Check Flask app logs for detailed error messages

### Scraping Issues
- ✅ Ensure ChromeDriver is compatible with Chrome version
- ✅ Check ChromeDriver path in environment variables
- ✅ Verify Spotify login works manually
- ✅ Review `scrape.log` for errors
- ✅ **Smart detailed feedback**: 
  - "Today only" scraping shows detailed list of newly added artists
  - Full scraping shows appropriate detail level (detailed list for small batches, top performers for medium batches, statistics for large batches)
- ✅ **Completion messages**: Admin panel displays context-aware artist count and performance statistics
- ✅ **Real-time progress**: Live progress bar shows current artist being processed with accurate counters

### Progress Indicator Issues
- ✅ **Progress bar not showing**: Check that scraping script outputs "PROGRESS:" markers
- ✅ **Progress stuck at 0%**: Verify scraping script is outputting progress updates
- ✅ **No artist names showing**: Check progress parsing in job service logs
- ✅ **Progress bar shows but no updates**: Ensure frontend is polling `/admin/scraping_status/` endpoint
- ✅ **Progress percentage incorrect**: Verify total artist count is detected correctly from script output

### Web Interface Issues
- ✅ Check Flask app logs in terminal
- ✅ Verify all dependencies are installed
- ✅ Check browser developer console for JavaScript errors
- ✅ Ensure data files exist in `data/results/`
- ✅ **Top tracks not loading**: Check Spotify API credentials and rate limits

### Logging and Monitoring
- ✅ **Application logs**: Check `webapp/logs/app.log` for general application issues
- ✅ **Admin security logs**: Check `webapp/logs/admin.log` for authentication and admin activity
- ✅ **Failed login attempts**: Monitor admin.log for security violations
- ✅ **Performance issues**: Review app.log with timestamps for slow operations
- ✅ **Log rotation**: Logs automatically rotate at 10MB (app.log) and 5MB (admin.log)

---

## 📋 Migration from Dual-Account System

If you were using the old dual-account system, see `MIGRATION_GUIDE.md` for detailed migration instructions.

**Key Changes:**
- ❌ No more main/scrape account separation
- ❌ `spotify_follow_sync.py` script is deprecated (but still present)
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
