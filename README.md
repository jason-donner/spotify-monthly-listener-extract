# Monthly Listener Project

This project allows you to export the list of artists you follow on Spotify and then scrape their monthly listener counts. It consists of two main scripts:

- **src/get_artists.py**: Exports your followed artists to a JSON file.
- **src/scrape.py**: Scrapes monthly listener counts for those artists and saves the results.

---

## Features

- Export all followed Spotify artists to a dated JSON file.
- Scrape monthly listener counts for each artist using Selenium.
- Progress bars with Spotify green color and time estimates.
- Robust error handling and logging to dedicated log files.
- Results and logs are always saved in the `results/` folder inside the project.
- Designed for both automation and interactive use.
- Supports command-line arguments for output file, logging, and limits.
- **No hardcoded file paths:** All paths (including ChromeDriver) are configurable via command-line arguments or environment variables.
- Clean project structure with all source code in `src/`.

---

## Folder Structure

```
spotify-monthly-listeners/
│
├── .env                  # Your Spotify API credentials (not committed)
├── .gitignore
├── automation.log        # Main workflow log
├── get_artists.log       # Log for get_artists.py
├── scrape.log            # Log for scrape.py
├── LICENSE.txt
├── README.md
├── requirements.txt
├── run_monthly_listener.bat
├── results/              # All output JSON files
│   ├── spotify-artist-urls-YYYYMMDD.json
│   └── spotify-scraped-listeners-YYYYMMDD.json
└── src/
    ├── get_artists.py
    └── scrape.py
```

---

## Setup

1. **Clone the repository**  
   ```sh
   git clone <your-repo-url>
   cd spotify-monthly-listeners
   ```

2. **Create and activate a virtual environment (recommended)**
   ```sh
   python -m venv .venv
   .venv\Scripts\activate   # On Windows
   # Or
   source .venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

4. **Set up your Spotify API credentials**  
   - Create a `.env` file in the project folder with the following:
     ```
     SPOTIPY_CLIENT_ID=your_client_id
     SPOTIPY_CLIENT_SECRET=your_client_secret
     SPOTIPY_REDIRECT_URI=your_redirect_uri
     ```

---

## Usage

### 1. Export Followed Artists

```sh
python src/get_artists.py
```

- This will create a file like `results/spotify-artist-urls-YYYYMMDD.json`.
- You can customize the output file:
  ```sh
  python src/get_artists.py --output my_artists.json
  ```
- For automation (no prompts):
  ```sh
  python src/get_artists.py --no-prompt
  ```

### 2. Scrape Monthly Listeners

```sh
python src/scrape.py --chromedriver "C:\path\to\chromedriver.exe"
```

- By default, this uses the latest `results/spotify-artist-urls-YYYYMMDD.json` as input.
- You **must** specify the path to your ChromeDriver executable using `--chromedriver` or by setting the `CHROMEDRIVER_PATH` environment variable.
- When running the script, you will be prompted to log in to Spotify in the opened browser window. This is required for scraping and cannot be automated.
- For automation (no prompts except login):
  ```sh
  python src/scrape.py --chromedriver "C:\path\to\chromedriver.exe" --no-prompt
  ```

#### Using Environment Variables

Instead of passing paths every time, you can set environment variables:

On Windows (Command Prompt):
```bat
set CHROMEDRIVER_PATH=C:\path\to\chromedriver.exe
python src\scrape.py
```

On macOS/Linux:
```sh
export CHROMEDRIVER_PATH=/path/to/chromedriver
python src/scrape.py
```

---

## Output

- All results are saved in the `results/` folder by default.
- Log files are saved as `get_artists.log`, `scrape.log`, and `automation.log`.

---

## Customization

- Both scripts support command-line arguments for output file, logging, and limits.
- See `python src/get_artists.py --help` and `python src/scrape.py --help` for all options.
- **No file paths are hardcoded:** All paths can be set via arguments or environment variables.

---

## Manual Workflow

### Batch File: `run_monthly_listener.bat`

You can use the provided batch file to run the workflow.  
**Place this file in your project folder (where your scripts and `.venv` are located):**

```bat
@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
python src\get_artists.py --no-prompt --log get_artists.log
python src\scrape.py --no-prompt --log scrape.log
echo %DATE% %TIME% - Monthly listener workflow completed >> automation.log
```

- `%~dp0` ensures the batch file always runs from the project folder, no matter where it's launched from.
- This batch file runs both scripts with no prompts except for the Spotify login step.
- **You will need to manually log in to Spotify in the browser window when prompted during the scraping step.**
- **Do not hardcode your ChromeDriver path in the batch file. Instead, set it in your `.env` file as described below.**

---

### Setting the ChromeDriver Path

Before running the workflow, you must tell the scripts where to find your `chromedriver.exe`.  
**Create or edit a `.env` file in your project folder and add:**

```
CHROMEDRIVER_PATH=C:\Path\To\chromedriver.exe
```

- Replace `C:\Path\To\chromedriver.exe` with the actual path to your ChromeDriver executable.
- On Windows, backslashes are fine.
- Do **not** commit your `.env` file to version control.

If you do not have ChromeDriver, download it from [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads) and place it somewhere on your system.

---

## Notes

- **Automation via Windows Task Scheduler is no longer supported.**  
  Manual login to Spotify is required each time you run the scraping script or batch file.
- Make sure your `.env` and `.cache` files are **not committed** to git (see `.gitignore`).
- The scripts are designed to be robust for both interactive and manual workflows.
- Progress bars use Spotify green and show elapsed/estimated time.
- All source code is in the `src/` folder for clarity and maintainability.
- **No hardcoded file paths:** All paths are configurable for portability.

---

## License

MIT License

---

## Acknowledgments

- [Spotipy](https://spotipy.readthedocs.io/) for Spotify API access.
- [Selenium](https://www.selenium.dev/) for web scraping.
- [tqdm](https://tqdm.github.io/) for progress bars.
- [colorama](https://pypi.org/project/colorama/) for colored terminal output.