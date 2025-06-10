"""
Spotify Artist Scraper
----------------------
This script uses Selenium to scrape artist names and monthly listeners from Spotify artist pages.
It handles retries for failed fetches, saves results to a JSON file, and provides a summary report.
"""

import json
import os
import glob
import time
import re
from datetime import datetime
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from colorama import Fore, Style, init
import logging
import sys
import argparse

# Initialize colorama for colored console output
init(autoreset=True)


def setup_driver(headless=False, chromedriver_path=None, user_data_dir=None):
    """
    Set up and return a Selenium Chrome WebDriver with custom options.
    """
    if not chromedriver_path:
        raise ValueError("Path to chromedriver must be specified via --chromedriver or CHROMEDRIVER_PATH env var.")
    service = Service(chromedriver_path)
    chrome_options = Options()
    if user_data_dir:
        chrome_options.add_argument(f"user-data-dir={user_data_dir}")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    if headless:
        chrome_options.add_argument("--headless=new")  # Run Chrome in headless mode if requested
    return webdriver.Chrome(service=service, options=chrome_options)


def load_urls(input_path=None):
    """
    Load the list of artist URLs from the specified JSON file or the latest scraped file.
    """
    if input_path:
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Always use absolute path based on script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "results")
    list_files = glob.glob(os.path.join(results_dir, 'spotify-artist-urls-*.json'))
    if not list_files:
        raise FileNotFoundError("No spotify-artist-urls-*.json files found in results/.")
    latest_file = max(list_files, key=os.path.getctime)  # Get the most recently created file
    tqdm.write(f"Using URL list: {latest_file}")
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def scrape_artist(driver, url, wait_time=7):
    """
    Scrape the artist name and monthly listeners from a Spotify artist page.
    Returns (name, monthly_listeners) or (None, None) on failure.
    """
    driver.get(url['url'] if isinstance(url, dict) else url)  # Open the artist page
    try:
        # Wait for the meta tag containing the artist name
        meta_title = WebDriverWait(driver, wait_time).until(
            lambda d: d.find_element(By.XPATH, "//meta[@property='og:title']")
        )
        name = meta_title.get_attribute("content")
    except Exception as e:
        logging.warning(f"Failed to get artist name for URL: {url} | Error: {e}")
        return None, None
    try:
        # Extract monthly listeners from the meta description
        meta = driver.find_element(By.XPATH, "//meta[@property='og:description']")
        monthly = meta.get_attribute("content")
        match = re.search(r"([\d.,]+[KMB]?) monthly listeners", monthly)
        monthly = match.group(1) if match else None
    except Exception:
        monthly = None  # If not found, set to None
    return name, monthly


def scrape_all(driver, urls, today, bar_format, wait_time=0.2):
    """
    Scrape all artist URLs, returning a list of results and a list of failed URLs.
    """
    import sys
    results = []
    failed_urls = []
    is_tty = sys.stdout.isatty()
    # Set up the progress bar for scraping
    with tqdm(
        total=len(urls),
        bar_format=bar_format if is_tty else None,
        colour="#1DB954" if is_tty else None,
        disable=not is_tty,
        dynamic_ncols=is_tty,
        file=sys.stdout
    ) as pbar:
        for idx, url in enumerate(urls, 1):
            # Show current URL and failure count in the progress bar
            pbar.set_postfix({'failures': len(failed_urls)})
            pbar.set_postfix_str(f"Now: {url['url'] if isinstance(url, dict) else url}")
            name, monthly = scrape_artist(driver, url)
            if name:
                # Add successful scrape to results
                results.append({
                    'url': url['url'] if isinstance(url, dict) else url,
                    'artist_name': name,
                    'monthly_listeners': monthly,
                    'date': today
                })
            else:
                # Track failed URLs for retry
                failed_urls.append(url)
            pbar.update(1)
            time.sleep(wait_time)  # Short delay to avoid rate limiting
    return results, failed_urls


def retry_failed(driver, failed_urls, today):
    """
    Retry scraping for URLs that failed in the first pass, using a longer wait time.
    """
    results = []
    if failed_urls:
        tqdm.write(Fore.YELLOW + f"Retrying {len(failed_urls)} failed URLs with longer wait...")
        for url in failed_urls:
            name, monthly = scrape_artist(driver, url, wait_time=15)  # Longer wait on retry
            if name:
                results.append({
                    'url': url['url'] if isinstance(url, dict) else url,
                    'artist_name': name,
                    'monthly_listeners': monthly,
                    'date': today
                })
            time.sleep(0.5)  # Slightly longer delay on retry
    return results


def save_results(results, today, output_path=None):
    """
    Save the scraping results to a JSON file in the results directory.
    """
    today_fmt = datetime.now().strftime('%Y%m%d')  # No dashes
    if output_path:
        output_file = output_path
    else:
        results_dir = 'results'
        os.makedirs(results_dir, exist_ok=True)  # Ensure results directory exists
        output_file = os.path.join(results_dir, f'scraped_monthly_listeners_{today_fmt}.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    tqdm.write(Fore.GREEN + f"Saved {len(results)} results to {output_file}")
    return output_file


def report(results, failed_urls):
    """
    Print a summary report of the scraping session, including failed URLs.
    """
    success_count = len(results)
    fail_count = len(failed_urls)
    tqdm.write(Style.BRIGHT + f"\nSummary:")
    tqdm.write(Fore.GREEN + f"  Successful: {success_count}")
    tqdm.write(Fore.RED + f"  Failed:     {fail_count}")
    if failed_urls:
        tqdm.write(Fore.RED + "Failed URLs:")
        for url in failed_urls:
            tqdm.write(Fore.RED + f"  {url['url'] if isinstance(url, dict) else url}")


def now():
    """
    Return the current time as a string (HH:MM:SS).
    """
    return datetime.now().strftime("%H:%M:%S")


def parse_args():
    today = datetime.now().strftime('%Y%m%d')
    parser = argparse.ArgumentParser(description="Spotify Artist Scraper")
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of artists to scrape (default: all)'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Path to input JSON file (default: most recent spotify-artist-urls-YYYYMMDD.json in results/)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=f'results/spotify-scraped-listeners-{today}.json',
        help="Path to output JSON file (default: results/spotify-scraped-listeners-YYYYMMDD.json)"
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run Chrome in headless mode'
    )
    parser.add_argument(
        '--wait',
        type=float,
        default=0.2,
        help='Delay between requests (seconds)'
    )
    parser.add_argument(
        '--log',
        type=str,
        default='scrape.log',
        help='Log file location'
    )
    parser.add_argument(
        '--no-prompt',
        action='store_true',
        default=False,
        help='Do not prompt for user input (for automation)'
    )
    parser.add_argument(
        '--chromedriver',
        type=str,
        default=os.environ.get('CHROMEDRIVER_PATH', ''),
        help='Path to chromedriver executable (can also set CHROMEDRIVER_PATH env var)'
    )
    parser.add_argument(
        '--user-data-dir',
        type=str,
        default=os.environ.get('SELENIUM_PROFILE', ''),
        help='Path to Chrome user data directory (can also set SELENIUM_PROFILE env var)'
    )
    return parser.parse_args()


def main():
    """
    Main entry point for the script.
    Loads URLs, scrapes data, retries failures, saves results, and prints a report.
    """
    # Parse command-line arguments
    args = parse_args()

    # --- BEGIN FIX: Always write to results folder ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    if not os.path.isabs(args.output):
        output_path = os.path.join(results_dir, os.path.basename(args.output))
    else:
        output_path = args.output
    # --- END FIX ---

    # --- BEGIN FIX: Always write logs to script directory ---
    if not os.path.isabs(args.log):
        log_path = os.path.join(script_dir, os.path.basename(args.log))
    else:
        log_path = args.log
    # --- END FIX ---

    # Configure logging with dynamic log file
    logging.basicConfig(
        filename=log_path,
        filemode='a',
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO
    )
    today = datetime.now().strftime('%Y-%m-%d')
    # Set up progress bar format
    bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} artists scraped | Elapsed: {elapsed} | ETA: {remaining}"
    tqdm.write(f"[{now()}] Starting scrape...")

    # Set up Selenium driver
    driver = None
    try:
        driver = setup_driver(
            headless=args.headless,
            chromedriver_path=args.chromedriver,
            user_data_dir=args.user_data_dir
        )
        # Load artist URLs
        urls = load_urls(args.input)
        if not urls:
            tqdm.write(Fore.YELLOW + "No URLs loaded. Exiting.")
            logging.warning("No URLs loaded. Exiting.")
            return
        logging.info(f"Loaded {len(urls)} URLs for scraping.")
        # Optionally limit number of artists
        if args.limit:
            urls = urls[:args.limit]
        # Scrape all artists
        results, failed_urls = scrape_all(driver, urls, today, bar_format, wait_time=args.wait)
        # Retry failed URLs
        retry_results = retry_failed(driver, failed_urls, today)
        results.extend(retry_results)
        # Print failed URLs after retry
        still_failed = [url for url in failed_urls if url not in [r['url'] for r in retry_results]]
        if still_failed:
            tqdm.write(Fore.RED + f"{len(still_failed)} URLs still failed after retry:")
            for url in still_failed:
                tqdm.write(Fore.RED + f"  {url['url'] if isinstance(url, dict) else url}")
        # Save results to file
        if os.path.exists(output_path) and not getattr(args, 'no_prompt', False):
            confirm = input(f"File {output_path} exists. Overwrite? (y/N): ")
            if confirm.lower() != 'y':
                print("Aborted by user.")
                sys.exit(1)
        save_results(results, today, output_path=output_path)
        # Print summary report
        report(results, failed_urls)
        logging.info(f"Scraping completed successfully. {len(results)} results saved.")
        # Warn if high failure rate
        if len(failed_urls) > 0.5 * len(urls):
            tqdm.write(Fore.RED + "Warning: More than 50% of URLs failed. Check your network or login status.")
    except KeyboardInterrupt:
        tqdm.write(Fore.YELLOW + "\nOperation cancelled by user.")
        logging.warning("Operation cancelled by user.")
        sys.exit(1)
    except FileNotFoundError as fnf:
        tqdm.write(Fore.RED + f"File error: {fnf}")
        logging.error(f"File error: {fnf}")
        sys.exit(1)
    except Exception as e:
        # Handle any fatal errors
        logging.error(f"Script crashed: {e}", exc_info=True)
        tqdm.write(Fore.RED + "A fatal error occurred. See scrape.log for details.")
        sys.exit(1)
    finally:
        # Always close the Selenium driver
        if driver:
            driver.quit()
        tqdm.write(Fore.CYAN + "Scraping session finished. Goodbye!")


if __name__ == "__main__":
    main()

