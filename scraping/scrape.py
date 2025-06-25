"""
Spotify Artist Scraper
----------------------
This script uses Selenium to scrape artist names and monthly listeners from Spotify artist pages.
It handles retries for failed fetches, saves results to a JSON file, and provides a summary report.
"""

import os
import sys
import json
from datetime import datetime
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
from colorama import Fore, Style, init
from dotenv import load_dotenv
import time
import re

# Initialize colorama for colored console output
init(autoreset=True)
load_dotenv()


def parse_listener_count(val):
    """
    Convert a string like '1.2k' or '3.5m' to an integer.
    """
    if not val:
        return 0
    val = val.lower().replace(',', '').strip()
    try:
        if 'k' in val:
            return int(float(val.replace('k', '')) * 1000)
        elif 'm' in val:
            return int(float(val.replace('m', '')) * 1000000)
        else:
            return int(val)
    except Exception:
        return 0


def setup_driver(chromedriver_path=None):
    """
    Set up and return a Selenium Chrome WebDriver with custom options.
    """
    if not chromedriver_path:
        chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "chromedriver")

    service = Service(chromedriver_path)
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # Headless mode removed
    return webdriver.Chrome(service=service, options=chrome_options)



def load_urls(input_path=None):
    """
    Load the list of artist URLs from the specified JSON file or the master artist file.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "..", "data", "results")
    master_artist_file = os.path.join(results_dir, 'spotify-followed-artists-master.json')

    if input_path:
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif os.path.exists(master_artist_file):
        with open(master_artist_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(Fore.RED + "No input file or master artist file found.")
        sys.exit(1)


def scrape_artist(driver, url, wait_time=7):
    """
    Scrape the artist name and monthly listeners from a Spotify artist page.
    Returns (name, monthly_listeners) or (None, None) on failure.
    """
    driver.get(url['url'] if isinstance(url, dict) else url)  # Open the artist page
    try:
        # Wait for the artist name to be present
        meta_title = WebDriverWait(driver, wait_time).until(
            lambda d: d.find_element(By.XPATH, "//meta[@property='og:title']")
        )
        name = meta_title.get_attribute("content")
    except Exception as e:
        print(Fore.RED + f"Failed to get artist name for {url}: {e}")
        return None, None
    try:
        # Wait for the monthly listeners element
        listeners_elem = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'monthly listeners')]"))
        )
        monthly = listeners_elem.text.strip().split(' ')[0]
    except Exception:
        print(Fore.YELLOW + f"Could not find monthly listeners for {url}")
        monthly = None
    return name, monthly


def extract_artist_id(url):
    """
    Extract the artist ID from a Spotify artist URL.
    """
    match = re.search(r"artist/([a-zA-Z0-9]+)", url)
    return match.group(1) if match else None


def scrape_all(driver, urls, today, bar_format, wait_time=0.2):
    """
    Scrape all artist URLs, returning a list of results and a list of failed URLs.
    """
    results = []
    failed_urls = []
    is_tty = sys.stdout.isatty()
    with tqdm(total=len(urls), desc="Scraping artists", bar_format=bar_format if is_tty else None,
              colour="#1DB954" if is_tty else None, disable=not is_tty, dynamic_ncols=is_tty, file=sys.stdout) as pbar:
        for url in urls:
            name, monthly = scrape_artist(driver, url)
            artist_url = url['url'] if isinstance(url, dict) else url
            artist_id = url.get('artist_id') if isinstance(url, dict) and url.get('artist_id') else extract_artist_id(artist_url)
            monthly_listeners = parse_listener_count(monthly)
            if name and monthly_listeners != 0:
                results.append({
                    'url': artist_url,
                    'artist_name': name,
                    'monthly_listeners': monthly_listeners,
                    'date': today,
                    'artist_id': artist_id
                })
            else:
                failed_urls.append(url)
            pbar.update(1)
            time.sleep(wait_time)
    return results, failed_urls


def retry_failed(driver, failed_urls, today):
    """
    Retry scraping for failed URLs.
    """
    results = []
    still_failed = []
    for url in failed_urls:
        name, monthly = scrape_artist(driver, url, wait_time=15)
        artist_url = url['url'] if isinstance(url, dict) else url
        artist_id = url.get('artist_id') if isinstance(url, dict) and url.get('artist_id') else extract_artist_id(artist_url)
        monthly_listeners = parse_listener_count(monthly)
        if name and monthly_listeners != 0:
            results.append({
                'url': artist_url,
                'artist_name': name,
                'monthly_listeners': monthly_listeners,
                'date': today,
                'artist_id': artist_id
            })
        else:
            still_failed.append(url)
    return results, still_failed


def save_results(results, today, output_path=None):
    """
    Save the scraped results to a JSON file in src/results.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "..", "data", "results")
    if not output_path:
        output_path = os.path.join(results_dir, f"spotify-monthly-listeners-{today}.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(Fore.GREEN + f"Saved {len(results)} results to {output_path}")


def append_to_master(results, master_path=None):
    """
    Append new results to the master JSON file in src/results.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "..", "data", "results")
    if not master_path:
        master_path = os.path.join(results_dir, 'spotify-monthly-listeners-master.json')
    if os.path.exists(master_path):
        with open(master_path, 'r', encoding='utf-8') as f:
            master = json.load(f)
    else:
        master = []
    master.extend(results)
    with open(master_path, 'w', encoding='utf-8') as f:
        json.dump(master, f, ensure_ascii=False, indent=2)
    print(Fore.GREEN + f"Appended {len(results)} results to {master_path}")


def report(results, failed_urls):
    """
    Print a summary report.
    """
    print(Style.BRIGHT + f"\nScraping complete. {len(results)} artists scraped successfully.")
    if failed_urls:
        print(Fore.RED + f"{len(failed_urls)} artists failed to scrape:")
        for url in failed_urls:
            print(Fore.RED + f"  {url['url'] if isinstance(url, dict) else url}")


def now():
    return datetime.now().strftime('%Y%m%d')


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape Spotify artist monthly listeners.")
    parser.add_argument('--input', help="Input JSON file with artist URLs")
    parser.add_argument('--chromedriver', help="Path to chromedriver")
    # parser.add_argument('--headless', action='store_true', help="Run Chrome in headless mode")  # REMOVE THIS LINE
    parser.add_argument('--output', help="Output JSON file for results")
    parser.add_argument('--no-prompt', action='store_true', help="Skip login confirmation prompt")
    return parser.parse_args()


def main():
    args = parse_args()
    today = now()
    urls = load_urls(args.input)
    driver = setup_driver(chromedriver_path=args.chromedriver)  # Remove headless param
    driver.get("https://open.spotify.com")
    time.sleep(3)  # Wait for session/cookies to initialize

    # Only prompt if --no-prompt is NOT set
    if not args.no_prompt:
        input("Please sign in to Spotify in the opened browser window, then press Enter here to continue...")

    bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} artists | Elapsed: {elapsed} | ETA: {remaining}"
    try:
        results, failed_urls = scrape_all(driver, urls, today, bar_format)
        if failed_urls:
            print(Fore.YELLOW + f"\nRetrying {len(failed_urls)} failed URLs...")
            retry_results, still_failed = retry_failed(driver, failed_urls, today)
            results.extend(retry_results)
            failed_urls = still_failed
        save_results(results, today, args.output)
        append_to_master(results)
        report(results, failed_urls)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

