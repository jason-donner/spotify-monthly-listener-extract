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
- **No hardcoded file paths:** All paths (including ChromeDriver and user data directory) are configurable via command-line arguments or environment variables.
- Easy automation with a batch file and Windows Task Scheduler.
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
- You can also specify a Chrome user data directory with `--user-data-dir` or the `SELENIUM_PROFILE` environment variable (optional, but useful for keeping your Spotify login session).
- Example with both options:
  ```sh
  python src/scrape.py --chromedriver "C:\path\to\chromedriver.exe" --user-data-dir "C:\path\to\SeleniumProfile"
  ```
- For automation (no prompts):
  ```sh
  python src/scrape.py --chromedriver "C:\path\to\chromedriver.exe" --no-prompt
  ```

#### Using Environment Variables

Instead of passing paths every time, you can set environment variables:

On Windows (Command Prompt):
```bat
set CHROMEDRIVER_PATH=C:\path\to\chromedriver.exe
set SELENIUM_PROFILE=C:\path\to\SeleniumProfile
python src\scrape.py
```

On macOS/Linux:
```sh
export CHROMEDRIVER_PATH=/path/to/chromedriver
export SELENIUM_PROFILE=/path/to/SeleniumProfile
python src/scrape.py
```

---

### How Artist Tracking Works

- When you run `get_artists.py`, it exports your currently followed artists to a dated JSON file (e.g., `results/spotify-artist-urls-YYYYMMDD.json`).
- It also updates a **master file**:  
  `results/spotify-followed-artists-master.json`
    - This file keeps a running history of every artist you've ever followed.
    - Each artist entry includes:
      - `artist_name`
      - `url`
      - `date_added`: The date you first followed the artist (or when they were first detected)
      - `removed`: `true` if you have unfollowed the artist, `false` otherwise
      - `date_removed`: The date you unfollowed the artist (if applicable)
    - If you re-follow an artist, their `removed` status is reset.

### Scraping and Master Listener File

- When you run `scrape.py`, it scrapes monthly listener counts for all artists in your master file (or a specific input file).
- Scraped results are saved to a dated file (e.g., `results/spotify-scraped-listeners-YYYYMMDD.json`).
- All scraped data is also appended to a **master listener file**:  
  `results/spotify-monthly-listeners-master.json`
    - This file contains every scrape result, with:
      - `artist_name`
      - `url`
      - `monthly_listeners`
      - `date` (when the data was scraped)
    - Duplicate entries (same artist and date) are avoided.

---

## Output

- **Dated export files**:  
  - `results/spotify-artist-urls-YYYYMMDD.json`: Your followed artists at a point in time.
  - `results/spotify-scraped-listeners-YYYYMMDD.json`: Listener counts scraped on a given date.
- **Master files**:  
  - `results/spotify-followed-artists-master.json`:  
    Tracks all artists you’ve ever followed, with `date_added`, `removed`, and `date_removed` fields.
  - `results/spotify-monthly-listeners-master.json`:  
    Tracks all scraped listener data over time for all artists.

---

## Customization

- Both scripts support command-line arguments for output file, logging, and limits.
- See `python src/get_artists.py --help` and `python src/scrape.py --help` for all options.
- **No file paths are hardcoded:** All paths can be set via arguments or environment variables.
- **Artist history is preserved:**  
  The master artist file allows you to see when you started or stopped following each artist.

---

## Automation

### Batch File: `run_monthly_listener.bat`

You can automate the entire workflow using the provided batch file.  
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
- This batch file runs both scripts with no prompts and logs all output to `automation.log`.
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

### Scheduling with Windows Task Scheduler

To run the workflow automatically (e.g., on the first of every month):

1. **Open Task Scheduler** (search for it in the Start menu).
2. Click **Create Basic Task...** and give it a name (e.g., "Monthly Spotify Listener Export").
3. Set the trigger to **Monthly**, and choose the 1st day of each month.
4. For the action, select **Start a program** and browse to your `run_monthly_listener.bat` file in your project folder.
5. Finish the wizard.

Your workflow will now run automatically on the schedule you set.  
Check `automation.log` for output and errors after each run.

---

## Testing

To run the automated tests:

1. Install the test dependencies (if not already done):
   ```sh
   pip install -r requirements.txt
   ```

2. From the project root, set your `PYTHONPATH` and run pytest:
   - On Windows (PowerShell):
     ```sh
     $env:PYTHONPATH="$PWD"
     pytest
     ```
   - On Windows (Command Prompt):
     ```cmd
     set PYTHONPATH=%CD%
     pytest
     ```
   - On macOS/Linux:
     ```sh
     export PYTHONPATH=$PWD
     pytest
     ```

This will discover and run all tests in the `tests/` folder.

---

## Notes

- Make sure your `.env` and `.cache` files are **not committed** to git (see `.gitignore`).
- The scripts are designed to be robust for both interactive and automated workflows.
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