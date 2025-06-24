# Spotify Monthly Listener Extract

Automate the extraction of monthly listener counts for Spotify artists using Python and Selenium, with a modern web-based management interface.

---

## Features

- **Web-based artist management** with OAuth authentication
- **Artist suggestion system** where users can suggest new artists to track
- **Admin panel** for reviewing and approving artist suggestions
- **Direct Spotify integration** to follow artists from the web interface
- **Automated scraping** of monthly listener counts from Spotify artist pages
- **Data persistence** with JSON storage and master results tracking
- **Comprehensive logging** for all operations and troubleshooting
- Uses Selenium to scrape monthly listener counts from Spotify artist pages.
- Saves results to JSON files and appends to a master results file.
- Logs all major steps and errors for troubleshooting.

---

## Prerequisites

- **Python** (3.8+) installed and available in your system PATH.
- **Google Chrome** installed.
- **ChromeDriver** compatible with your Chrome version, available in your project directory or PATH.
- **Virtual environment** (`.venv`) created in the project root:
  ```sh
  python -m venv .venv
  ```
- **Dependencies installed** in the virtual environment:
  ```sh
  .venv\Scripts\activate
  pip install -r requirements.txt
  ```
- **Environment variables** for both main and scraping Spotify accounts set in a `.env` file.

---

## Workflow

1. **Navigate to Project Directory**
   - The batch file changes the working directory to the project folder.

2. **Activate Virtual Environment**
   - The batch file activates the `.venv` Python environment to ensure dependencies are available.

3. **Synchronize Followed Artists** (Optional, but recommended)
   - Runs `spotify_follow_sync.py` to ensure the scraping account follows all artists that the main account follows.
   - You will be prompted to log in to both accounts via browser.
   - **Note:** This step is only necessary if you want to avoid using your main account for scraping, which can help reduce the risk of your main account being flagged or restricted by Spotify. If you are comfortable scraping with your main account, you may skip this step and use your main account credentials throughout.

4. **Run `get_artists.py`**
   - Fetches the list of artist URLs based on the scraping account’s followed artists.
   - Output is logged to `get_artists.log`.

5. **Run `scrape.py`**
   - Opens a browser window for manual Spotify login and scrapes monthly listener data.
   - Results are saved to a JSON file and appended to a master results file.

6. **Logging and Completion**
   - All major steps and errors are logged to `automation.log`.
   - The batch file logs completion and pauses so you can review any messages.

---

## Usage

1. Double-click `run_monthly_listener.bat` or run it from the command prompt:
   ```sh
   run_monthly_listener.bat
   ```
2. Follow the prompts:
   - Log in to both Spotify accounts when prompted during the sync step (if using a separate scraping account).
   - When the browser window opens for scraping, log in to Spotify if required.
   - Wait for the script to finish scraping.

---

## File Structure

```
Spotify Monthly Listener Extract/
│
├── .venv/                      # Python virtual environment
├── src/
│   ├── get_artists.py          # Script to gather artist URLs
│   ├── scrape.py               # Script to scrape monthly listeners
│   └── spotify_follow_sync.py  # Script to sync followed artists
├── results/                    # Output and master JSON files
├── run_monthly_listener.bat
├── requirements.txt
├── .env                        # Environment variables for Spotify accounts
├── automation.log
└── WORKFLOW.md                 # Detailed workflow documentation
```

---

## Troubleshooting

- **Browser does not open:**  
  Ensure ChromeDriver is present and compatible with your Chrome version. Check for errors in the command prompt or `automation.log`.

- **Script fails with exit code:**  
  Review the log files for error messages. Make sure all dependencies are installed.

- **Login prompt does not appear:**  
  Make sure you are not running in headless mode and that `scrape.py` is set up to prompt for login.

- **Sync step fails:**  
  Ensure your `.env` file contains valid credentials for both accounts and that you complete the browser authorization steps.

---

## Data Cleanup

- Data cleanup steps are documented in detail in [WORKFLOW.md](WORKFLOW.md).
- Briefly, we have:
  - Ensured all records in the master results file have valid `artist_id` fields (extracted from the URL if missing).
  - Removed any records with `monthly_listeners` equal to 0, as these represent scraping errors.
  - Updated the scraping script to prevent such records from being created in the future.
  - **Deduplicated data:** As of June 2025, we use `dedupe_daily_last.py` to ensure only the latest value per artist per day is kept in all results files. This script overwrites the originals in-place.

### Deduplicate Data by Day

To ensure only one data point per artist per day (the latest scraped value), run:

```sh
& ".venv/Scripts/python.exe" dedupe_daily_last.py
```

This will overwrite all `spotify-monthly-listeners-*.json` files in `src/results/` with deduplicated data.

See the workflow documentation for scripts and commands used.

---

## Web App: Explore Your Results

This project includes a Flask web application for searching, visualizing, and exploring your collected Spotify monthly listener data.

### Features

- Search for artists and view their listener history.
- See listener trends, changes, and top tracks.
- Leaderboard of biggest monthly listener changes.
- Modern, responsive UI.

### How to Use

1. **Install dependencies** for the web app:
   ```sh
   cd app/spotify-listener-tracker
   pip install -r requirements.txt
   ```
2. **Start the Flask app:**
   ```sh
   python app.py
   ```
   The app will run on [http://127.0.0.1:5000](http://127.0.0.1:5000).

3. **Browse your data:**
   - Use the search bar to find artists.
   - Visit `/leaderboard` for the top monthly changes.

### File Structure

```
app/
└── spotify-listener-tracker/
    ├── app.py
    ├── routes.py
    ├── utils.py
    ├── templates/
    ├── static/
    └── requirements.txt
```

**Note:** The web app reads from your master results JSON file. Make sure your scraping workflow has run at least once before using the app.

---

## License

MIT