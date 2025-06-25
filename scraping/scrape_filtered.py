"""
Filtered Spotify Artist Scraper
-------------------------------
This script scrapes only specific artists based on filters like date_added,
and avoids creating duplicate entries for the same date.
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
import argparse

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


def format_listener_count(count):
    """
    Format an integer listener count back to a readable string (e.g., 1200000 -> "1.2M").
    """
    if count >= 1000000:
        return f"{count / 1000000:.1f}M"
    elif count >= 1000:
        return f"{count / 1000:.1f}K"
    else:
        return str(count)


def setup_driver(chromedriver_path=None, headless=False):
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
    
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
    
    return webdriver.Chrome(service=service, options=chrome_options)


def load_artists_by_date(target_date=None):
    """
    Load artists filtered by date_added.
    If target_date is None, loads all artists.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "..", "data", "results")
    master_artist_file = os.path.join(results_dir, 'spotify-followed-artists-master.json')

    if not os.path.exists(master_artist_file):
        print(Fore.RED + "Master artist file not found.")
        return []

    with open(master_artist_file, 'r', encoding='utf-8') as f:
        all_artists = json.load(f)

    if target_date is None:
        return all_artists

    # Filter by target date
    filtered_artists = [
        artist for artist in all_artists 
        if artist.get('date_added') == target_date and not artist.get('removed', False)
    ]
    
    print(f"Found {len(filtered_artists)} artists added on {target_date}")
    return filtered_artists


def load_existing_listeners(target_date):
    """
    Load existing monthly listener entries for the target date to avoid duplicates.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "..", "data", "results")
    master_listeners_file = os.path.join(results_dir, 'spotify-monthly-listeners-master.json')

    existing_artist_ids = set()
    
    if os.path.exists(master_listeners_file):
        with open(master_listeners_file, 'r', encoding='utf-8') as f:
            listeners_data = json.load(f)
        
        # Convert target_date to the format used in the listeners file (YYYYMMDD)
        target_date_formatted = target_date.replace('-', '')
        
        for entry in listeners_data:
            if entry.get('date') == target_date_formatted:
                artist_id = entry.get('artist_id')
                if artist_id:
                    existing_artist_ids.add(artist_id)
    
    print(f"Found {len(existing_artist_ids)} artists already scraped for {target_date}")
    return existing_artist_ids


def scrape_artist(driver, artist_data, wait_time=7):
    """
    Scrape the artist name and monthly listeners from a Spotify artist page.
    Returns (name, monthly_listeners) or (None, None) on failure.
    """
    url = artist_data.get('url') if isinstance(artist_data, dict) else artist_data
    
    driver.get(url)
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


def scrape_filtered_artists(driver, artists, today, existing_artist_ids):
    """
    Scrape only artists that haven't been scraped today.
    """
    results = []
    failed_urls = []
    skipped_count = 0
    
    # Filter out artists that already have data for today
    artists_to_scrape = []
    for artist in artists:
        artist_id = artist.get('artist_id')
        if artist_id in existing_artist_ids:
            skipped_count += 1
            print(f"Skipping {artist.get('artist_name', 'Unknown')} - already scraped today")
        else:
            artists_to_scrape.append(artist)
    
    print(f"Scraping {len(artists_to_scrape)} artists (skipped {skipped_count} duplicates)")
    
    if not artists_to_scrape:
        print(Fore.YELLOW + "No new artists to scrape!")
        return results, failed_urls
    
    is_tty = sys.stdout.isatty()
    bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} artists | Elapsed: {elapsed} | ETA: {remaining}"
    
    with tqdm(total=len(artists_to_scrape), desc="Scraping filtered artists", 
              bar_format=bar_format if is_tty else None,
              colour="#1DB954" if is_tty else None, disable=not is_tty, 
              dynamic_ncols=is_tty, file=sys.stdout) as pbar:
        
        for artist in artists_to_scrape:
            name, monthly = scrape_artist(driver, artist)
            artist_url = artist.get('url')
            artist_id = artist.get('artist_id')
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
                failed_urls.append(artist)
            
            pbar.update(1)
            time.sleep(0.2)  # Small delay between requests
    
    return results, failed_urls


def save_results(results, today, output_path=None):
    """
    Save the scraping results to a dated JSON file.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "..", "data", "results")
    
    if output_path:
        output_file = output_path
    else:
        output_file = os.path.join(results_dir, f'spotify-monthly-listeners-{today}.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(Fore.GREEN + f"Saved {len(results)} results to {output_file}")


def append_to_master(results):
    """
    Append results to the master monthly listeners file.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "..", "data", "results")
    master_path = os.path.join(results_dir, 'spotify-monthly-listeners-master.json')
    
    master = []
    if os.path.exists(master_path):
        with open(master_path, 'r', encoding='utf-8') as f:
            master = json.load(f)
    
    master.extend(results)
    
    with open(master_path, 'w', encoding='utf-8') as f:
        json.dump(master, f, ensure_ascii=False, indent=2)
    
    print(Fore.GREEN + f"Appended {len(results)} results to {master_path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape Spotify artist monthly listeners with filters.")
    parser.add_argument('--date', help="Date to filter artists by (YYYY-MM-DD format). Defaults to today.")
    parser.add_argument('--chromedriver', help="Path to chromedriver")
    parser.add_argument('--headless', action='store_true', help="Run Chrome in headless mode")
    parser.add_argument('--output', help="Output JSON file for results")
    parser.add_argument('--no-prompt', action='store_true', help="Skip login confirmation prompt")
    parser.add_argument('--allow-duplicates', action='store_true', help="Allow scraping artists already scraped today (bypass duplicate protection)")
    
    args = parser.parse_args()
    
    # Use provided date or default to today
    target_date = args.date or datetime.now().strftime('%Y-%m-%d')
    today_formatted = datetime.now().strftime('%Y%m%d')
    
    print(f"Filtering artists added on: {target_date}")
    
    # Load artists filtered by date
    artists = load_artists_by_date(target_date)
    
    if not artists:
        print(Fore.YELLOW + f"No artists found for date: {target_date}")
        return
    
    # Load existing listener data to avoid duplicates (unless bypassed)
    if args.allow_duplicates:
        print("Duplicate protection disabled - will scrape all filtered artists")
        existing_artist_ids = set()
    else:
        existing_artist_ids = load_existing_listeners(target_date)
    
    # Setup driver
    driver = setup_driver(chromedriver_path=args.chromedriver, headless=args.headless)
    
    try:
        # Initialize Spotify session
        driver.get("https://open.spotify.com")
        time.sleep(3)
        
        # Only prompt if --no-prompt is NOT set and not in headless mode
        if not args.no_prompt and not args.headless:
            input("Please sign in to Spotify in the opened browser window, then press Enter here to continue...")
        
        # Scrape the filtered artists
        results, failed_urls = scrape_filtered_artists(driver, artists, today_formatted, existing_artist_ids)
        
        if results:
            save_results(results, today_formatted, args.output)
            append_to_master(results)
            print(Style.BRIGHT + f"\nFiltered scraping complete. {len(results)} new artists scraped successfully.")
            
            # Print detailed list of newly scraped artists
            print(Fore.GREEN + "\n✅ Successfully scraped new artists:")
            for result in results:
                listeners_formatted = format_listener_count(result['monthly_listeners'])
                print(Fore.GREEN + f"  • {result['artist_name']} - {listeners_formatted} monthly listeners")
        else:
            print(Fore.YELLOW + "\nNo new data to save - all artists already scraped today or failed.")
        
        if failed_urls:
            print(Fore.RED + f"\n❌ {len(failed_urls)} artists failed to scrape:")
            for artist in failed_urls:
                print(Fore.RED + f"  • {artist.get('artist_name', 'Unknown')} - {artist.get('url', 'No URL')}")
    
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
