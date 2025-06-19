# Spotify Monthly Listener Extract – Workflow Documentation

## Overview

This workflow automates the extraction of monthly listener counts for Spotify artists using Python scripts and Selenium. It ensures your scraping account follows all artists your main account does, guaranteeing a complete and up-to-date artist list.

---

## Prerequisites

- **Python** installed and available in your system PATH.
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

## Workflow Steps

1. **Navigate to Project Directory**
   - The batch file changes the working directory to the project folder.

2. **Activate Virtual Environment**
   - The batch file activates the `.venv` Python environment to ensure dependencies are available.

3. **Synchronize Followed Artists**
   - Runs `spotify_follow_sync.py` to ensure the scraping account follows all artists that the main account follows.
   - You will be prompted to log in to both accounts via browser.
   - This guarantees the artist list fetched for scraping is complete and up-to-date.
   - **Note:** This account sync step is only necessary if you want to avoid using your main account for scraping, which can help reduce the risk of your main account being flagged or restricted by Spotify. If you are comfortable scraping with your main account, you may skip this step and use your main account credentials throughout.

4. **Run `get_artists.py`**
   - Fetches the list of artist URLs based on the scraping account’s followed artists.
   - Output is logged to `get_artists.log`.

5. **Run `scrape.py`**
   - Opens a browser window for manual Spotify login and scrapes monthly listener data.
   - Results are saved to a JSON file and appended to a master results file.

6. **Logging and Completion**
   - All major steps and errors are logged to `automation.log`.
   - The batch file logs completion and pauses so you can review any messages.

7. **Explore Results with the Web App**
   - Use the included Flask web application to search, visualize, and analyze your collected data.
   - See the [README.md](README.md) for setup and usage instructions.

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
└── automation.log
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