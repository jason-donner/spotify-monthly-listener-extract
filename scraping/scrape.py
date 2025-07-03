"""
Spotify Artist Scraper
----------------------
This script uses Selenium to scrape artist names and monthly listeners from Spotify artist pages.
It handles retries for failed fetches, saves results to a JSON file, and provides a summary report.
"""

import os
import sys
import json
import platform
import subprocess
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


def kill_chrome_processes():
    """
    Kill any existing Chrome/ChromeDriver processes that might be stuck.
    """
    import subprocess
    import platform
    
    try:
        if platform.system() == "Windows":
            # Kill Chrome processes
            subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                         capture_output=True, check=False)
            subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], 
                         capture_output=True, check=False)
        else:
            # Linux/Mac
            subprocess.run(["pkill", "-f", "chrome"], capture_output=True, check=False)
            subprocess.run(["pkill", "-f", "chromedriver"], capture_output=True, check=False)
        time.sleep(2)  # Give processes time to die
    except Exception as e:
        print(Fore.YELLOW + f"Warning: Could not kill existing Chrome processes: {e}")


def check_chrome_version():
    """
    Check Chrome and ChromeDriver version compatibility.
    """
    import subprocess
    
    try:
        # Get Chrome version
        if platform.system() == "Windows":
            chrome_cmd = r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --version'
            result = subprocess.run(chrome_cmd, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
        
        if result.returncode == 0:
            chrome_version = result.stdout.strip()
            print(f"Chrome version: {chrome_version}")
        else:
            print(Fore.YELLOW + "Could not determine Chrome version")
            
    except Exception as e:
        print(Fore.YELLOW + f"Could not check Chrome version: {e}")


def setup_driver(chromedriver_path=None, headless=False, max_retries=3):
    """
    Set up and return a Selenium Chrome WebDriver with custom options.
    Includes network resilience settings and session recovery.
    """
    import platform
    from selenium.webdriver.chrome.service import Service
    
    # Check Chrome version for diagnostics
    check_chrome_version()
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f"Retrying driver setup (attempt {attempt + 1}/{max_retries})...")
                kill_chrome_processes()
                time.sleep(3)
            
            # Set up Chrome options
            chrome_options = Options()
            
            # Essential Chrome arguments for session stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            
            # Session management
            if not headless:
                chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-default-apps")
            
            # Anti-detection settings
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Logging and errors
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--silent")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # User agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            if headless:
                chrome_options.add_argument("--headless=new")  # Use new headless mode
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-plugins")
                chrome_options.add_argument("--disable-web-security")
                chrome_options.add_argument("--disable-features=VizDisplayCompositor")
                chrome_options.add_argument("--disable-popup-blocking")
                chrome_options.add_argument("--disable-notifications")
            
            # Set page load strategy
            chrome_options.page_load_strategy = 'normal'
            
            # Create driver with improved error handling
            print("Creating Chrome WebDriver...")
            
            if chromedriver_path and os.path.exists(chromedriver_path):
                # Use specified ChromeDriver path
                print(f"Using specified ChromeDriver: {chromedriver_path}")
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Try multiple methods to get a working ChromeDriver
                driver = None
                
                # Method 1: Try Selenium's built-in WebDriver manager (most reliable)
                try:
                    print("Trying Selenium's built-in WebDriver management...")
                    driver = webdriver.Chrome(options=chrome_options)
                    print("✓ Successfully created driver with Selenium auto-management")
                except Exception as e:
                    print(f"Selenium auto-management failed: {e}")
                
                # Method 2: Try auto-installer as fallback (if Selenium failed)
                if not driver:
                    try:
                        print("Trying chromedriver-autoinstaller...")
                        import chromedriver_autoinstaller
                        
                        # Set a timeout for the download
                        import socket
                        original_timeout = socket.getdefaulttimeout()
                        socket.setdefaulttimeout(10)  # 10 second timeout
                        
                        try:
                            chromedriver_path_installed = chromedriver_autoinstaller.install()
                            print(f"✓ ChromeDriver installed at: {chromedriver_path_installed}")
                            driver = webdriver.Chrome(options=chrome_options)
                            print("✓ Successfully created driver with auto-installer")
                        finally:
                            socket.setdefaulttimeout(original_timeout)
                            
                    except (ImportError, Exception) as e:
                        print(f"Auto-installer failed: {e}")
                
                # Method 3: Try with explicit service (last resort)
                if not driver:
                    try:
                        print("Trying explicit service creation...")
                        service = Service()
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        print("✓ Successfully created driver with explicit service")
                    except Exception as e:
                        print(f"Explicit service failed: {e}")
                        raise Exception("All ChromeDriver setup methods failed")
            
            # Set timeouts
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            # Test the driver with a simple command
            driver.execute_script("return navigator.userAgent;")
            
            print(Fore.GREEN + "✓ Chrome WebDriver created successfully")
            return driver
            
        except Exception as e:
            error_msg = str(e)
            print(Fore.RED + f"Failed to create driver (attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt == max_retries - 1:
                print(Fore.RED + "All driver creation attempts failed.")
                
                # Provide specific guidance based on the error
                if "WinError 10054" in error_msg or "connection" in error_msg.lower():
                    print(Fore.YELLOW + "\n🌐 Network Connection Issue Detected:")
                    print("1. Check your internet connection and firewall settings")
                    print("2. Try running the script again in a few minutes")
                    print("3. If using corporate network, contact IT about Selenium WebDriver access")
                    print("4. Alternative: Download ChromeDriver manually:")
                    print("   - Go to https://chromedriver.chromium.org/")
                    print("   - Download the version matching your Chrome browser")
                    print("   - Save it to your PATH or specify with --chromedriver argument")
                elif "chrome" in error_msg.lower():
                    print(Fore.YELLOW + "\n🔧 Chrome Browser Issue:")
                    print("1. Make sure Google Chrome is installed and updated")
                    print("2. Close all Chrome windows and try again")
                    print("3. Try running with --headless flag")
                    print("4. Restart your computer to clear stuck processes")
                elif "permission" in error_msg.lower():
                    print(Fore.YELLOW + "\n🔒 Permission Issue:")
                    print("1. Run the script as Administrator")
                    print("2. Check if antivirus is blocking Selenium")
                    print("3. Try running from a different directory")
                else:
                    print(Fore.YELLOW + "\n🛠️ General Troubleshooting:")
                    print("1. Update Chrome to the latest version")
                    print("2. Restart your computer")
                    print("3. Try running with --headless flag")
                    print("4. Check Windows Event Viewer for more details")
                
                print(f"\n📋 For detailed diagnosis, run: python chrome_diagnostic.py")
                raise
            time.sleep(2)
    
    return None



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
        
        for entry in listeners_data:
            if entry.get('date') == target_date:
                artist_id = entry.get('artist_id')
                if artist_id:
                    existing_artist_ids.add(artist_id)
    
    if existing_artist_ids:
        print(f"Found {len(existing_artist_ids)} artists already scraped for {target_date}")
    
    return existing_artist_ids


def scrape_artist(driver, url, wait_time=7, max_retries=3, retry_delay=2):
    """
    Scrape the artist name and monthly listeners from a Spotify artist page.
    Returns (name, monthly_listeners) or (None, None) on failure.
    Includes retry logic for network errors.
    """
    import time
    from selenium.common.exceptions import WebDriverException, TimeoutException
    
    artist_url = url['url'] if isinstance(url, dict) else url
    artist_name = url.get('artist_name', 'Unknown') if isinstance(url, dict) else 'Unknown'
    
    for attempt in range(max_retries):
        try:
            # Navigate to the artist page
            driver.get(artist_url)
            
            # Wait for the artist name to be present
            meta_title = WebDriverWait(driver, wait_time).until(
                lambda d: d.find_element(By.XPATH, "//meta[@property='og:title']")
            )
            name = meta_title.get_attribute("content")
            
            # Wait for the monthly listeners element
            try:
                listeners_elem = WebDriverWait(driver, wait_time).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'monthly listeners')]"))
                )
                monthly = listeners_elem.text.strip().split(' ')[0]
            except TimeoutException:
                print(Fore.YELLOW + f"Could not find monthly listeners for {artist_name}")
                monthly = None
            
            return name, monthly
            
        except WebDriverException as e:
            if "ERR_CONNECTION_RESET" in str(e) or "net::" in str(e):
                if attempt < max_retries - 1:
                    print(Fore.YELLOW + f"Network error for {artist_name}, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    continue
                else:
                    print(Fore.RED + f"Network error for {artist_name} after {max_retries} attempts: {e}")
                    return None, None
            else:
                print(Fore.RED + f"WebDriver error for {artist_name}: {e}")
                return None, None
        except Exception as e:
            print(Fore.RED + f"Unexpected error for {artist_name}: {e}")
            if attempt < max_retries - 1:
                print(Fore.YELLOW + f"Retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 1.5
                continue
            else:
                return None, None
    
    return None, None


def extract_artist_id(url):
    """
    Extract the artist ID from a Spotify artist URL.
    """
    match = re.search(r"artist/([a-zA-Z0-9]+)", url)
    return match.group(1) if match else None


def scrape_all(driver, urls, today, bar_format, existing_artist_ids, wait_time=0.2):
    """
    Scrape all artist URLs, returning a list of results and a list of failed URLs.
    Skips artists that already have data for today to prevent duplicates.
    """
    results = []
    failed_urls = []
    skipped_count = 0
    

    # Debug: Print all input artists and their IDs
    print("[DEBUG] Filtering input artists against today's scraped artist_ids...")
    urls_to_scrape = []
    for url in urls:
        if isinstance(url, dict):
            artist_id = url.get('artist_id') or extract_artist_id(url.get('url', ''))
            artist_name = url.get('artist_name', 'Unknown')
            artist_url = url.get('url', '')
        else:
            artist_id = extract_artist_id(url)
            artist_name = 'Unknown'
            artist_url = url
        print(f"  [DEBUG] Considering: {artist_name} | {artist_id} | {artist_url}")
        if artist_id in existing_artist_ids:
            skipped_count += 1
            print(f"    [DEBUG] Skipping {artist_name} ({artist_id}) - already scraped today")
        else:
            print(f"    [DEBUG] Will scrape {artist_name} ({artist_id})")
            urls_to_scrape.append(url)

    if skipped_count > 0:
        print(f"Scraping {len(urls_to_scrape)} artists (skipped {skipped_count} duplicates)")
    else:
        print(f"Scraping {len(urls_to_scrape)} artists")

    # Output total for progress tracking
    print(f"PROGRESS: Starting scrape of {len(urls_to_scrape)} artists")

    if not urls_to_scrape:
        print(Fore.YELLOW + "No new artists to scrape - all artists already have data for today!")
        return results, failed_urls

    is_tty = sys.stdout.isatty()
    with tqdm(total=len(urls_to_scrape), desc="Scraping artists", bar_format=bar_format if is_tty else None,
              colour="#1DB954" if is_tty else None, disable=not is_tty, dynamic_ncols=is_tty, file=sys.stdout) as pbar:
        for i, url in enumerate(urls_to_scrape):
            try:
                # Output progress for admin dashboard
                artist_name = url.get('artist_name', 'Unknown') if isinstance(url, dict) else 'Unknown'
                print(f"PROGRESS: Processing artist {i+1}/{len(urls_to_scrape)}: {artist_name}", flush=True)
                
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
                
                # Add progressive delay to avoid rate limiting
                if i < len(urls_to_scrape) - 1:  # Don't wait after the last artist
                    base_wait = max(wait_time, 0.5)  # Minimum 0.5 second wait
                    # Add extra delay every 20 requests to be extra cautious
                    if (i + 1) % 20 == 0:
                        extended_wait = base_wait * 3
                        print(f"\nPausing for {extended_wait:.1f}s to avoid rate limiting...")
                        time.sleep(extended_wait)
                    else:
                        time.sleep(base_wait)
                        
            except Exception as e:
                print(Fore.RED + f"Unexpected error processing {url}: {e}")
                failed_urls.append(url)
                pbar.update(1)
                time.sleep(wait_time * 2)  # Longer wait after errors
                
    return results, failed_urls


def retry_failed(driver, failed_urls, today):
    """
    Retry failed URLs with longer delays between requests.
    """
    print(Fore.CYAN + "Retrying failed URLs with increased delays...")
    results = []
    still_failed = []
    for url in failed_urls:
        name, monthly = scrape_artist(driver, url, wait_time=10)  # Longer wait time for retries
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
        time.sleep(1)  # Longer delay between retry attempts
    return results, still_failed


def parse_listener_count(monthly_str):
    """
    Parse the monthly listener count string and convert to integer.
    """
    if not monthly_str:
        return 0
    monthly_str = monthly_str.replace(',', '')
    try:
        count = int(monthly_str)
    except ValueError:
        print(Fore.RED + f"Could not parse listener count: {monthly_str}")
        return 0
    return count


def report(results, failed_urls):
    """
    Print a summary report of the scraping results.
    """
    print("\n" + "="*60)
    print(Fore.GREEN + f"Successfully scraped {len(results)} artists")
    print(f"PROGRESS: Completed scraping {len(results)} artists")
    if failed_urls:
        print(Fore.RED + f"Failed to scrape {len(failed_urls)} artists")
        for url in failed_urls:
            artist_name = url.get('artist_name', 'Unknown') if isinstance(url, dict) else 'Unknown'
            print(f"  - {artist_name}")
    print("="*60)


def save_results(results, today, output_path=None):
    """
    Save the scraping results to the master JSON file only.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, "..", "data", "results")
    os.makedirs(results_dir, exist_ok=True)
    master_path = os.path.join(results_dir, 'spotify-monthly-listeners-master.json')
    with open(master_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(Fore.GREEN + f"Saved {len(results)} results to {master_path}")


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
    print(Fore.GREEN + f"Appended {len(results)} results to master file")


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape Spotify artist monthly listeners.")
    parser.add_argument('--input', help="Input JSON file with artist URLs")
    parser.add_argument('--chromedriver', help="Path to chromedriver")
    parser.add_argument('--headless', action='store_true', help="Run Chrome in headless mode")
    parser.add_argument('--output', help="Output JSON file for results")
    parser.add_argument('--no-prompt', action='store_true', help="Skip login confirmation prompt")
    parser.add_argument('--allow-duplicates', action='store_true', help="Allow scraping artists already scraped today (bypass duplicate protection)")
    parser.add_argument('--skip-network-test', action='store_true', help="Skip the initial network connectivity test (useful if bot-blocking is suspected)")
    return parser.parse_args()


def now():
    """
    Return the current date as a string in the format YYYY-MM-DD.
    """
    return datetime.now().strftime("%Y-%m-%d")


def test_network_connectivity():
    """
    Test basic network connectivity to Spotify.
    """
    import urllib.request
    import urllib.error
    
    # Use sys.stdout with utf-8 encoding to avoid UnicodeEncodeError on Windows
    import sys
    def safe_print(text):
        try:
            print(text)
        except UnicodeEncodeError:
            sys.stdout.buffer.write((str(text) + '\n').encode('utf-8', errors='replace'))

    try:
        safe_print("Testing network connectivity to Spotify...")
        response = urllib.request.urlopen("https://open.spotify.com", timeout=10)
        if response.getcode() == 200:
            safe_print(Fore.GREEN + "✓ Network connectivity to Spotify is working")
            return True
        else:
            safe_print(Fore.YELLOW + f"⚠ Spotify returned status code: {response.getcode()}")
            return False
    except urllib.error.URLError as e:
        safe_print(Fore.RED + f"✗ Network connectivity test failed: {e}")
        safe_print("Check your internet connection and try again.")
        return False
    except Exception as e:
        safe_print(Fore.YELLOW + f"⚠ Network test inconclusive: {e}")
        return True  # Continue anyway


def main():
    args = parse_args()
    today = now()
    driver = None
    
    try:
        # Test network connectivity first, but allow override with --skip-network-test
        if not getattr(args, 'skip_network_test', False):
            if not test_network_connectivity():
                print("Network connectivity issues detected. Proceeding anyway due to possible false positive (e.g., bot blocking).")
        
        urls = load_urls(args.input)
        print("\n[DEBUG] Loaded input artist list:")
        for u in urls:
            if isinstance(u, dict):
                print(f"  - {u.get('artist_name', 'Unknown')} | {u.get('artist_id', extract_artist_id(u.get('url', '')))} | {u.get('url', '')}")
            else:
                print(f"  - [raw url] {u}")

        # Load existing listeners to prevent duplicates (unless bypassed)
        if args.allow_duplicates:
            print("Duplicate protection disabled - will scrape all artists")
            existing_artist_ids = set()
        else:
            existing_artist_ids = load_existing_listeners(today)
        print("[DEBUG] Existing artist_ids for today:")
        for eid in existing_artist_ids:
            print(f"  - {eid}")

        print("\nSetting up Chrome WebDriver...")
        try:
            driver = setup_driver(chromedriver_path=args.chromedriver, headless=args.headless)
        except Exception as e:
            print(Fore.RED + f"Failed to create Chrome WebDriver: {e}")
            print("\nTroubleshooting steps:")
            print("1. Make sure Chrome is installed and updated")
            print("2. Download the correct ChromeDriver version from https://chromedriver.chromium.org/")
            print("3. Try running with --headless flag")
            print("4. Restart your computer to clear stuck processes")
            return
        
        # Initial navigation with retry logic
        max_init_retries = 3
        for attempt in range(max_init_retries):
            try:
                print("Navigating to Spotify login page...")
                driver.get("https://accounts.spotify.com/login")
                time.sleep(3)  # Wait for session/cookies to initialize
                break
            except Exception as e:
                if attempt < max_init_retries - 1:
                    print(Fore.YELLOW + f"Failed to load Spotify login (attempt {attempt + 1}/{max_init_retries}): {e}")
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print(Fore.RED + f"Failed to load Spotify login after {max_init_retries} attempts: {e}")
                    raise

        # Only prompt if --no-prompt is NOT set
        if not args.no_prompt:
            input("Please sign in to Spotify in the opened browser window, then press Enter here to continue...")

        bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} artists | Elapsed: {elapsed} | ETA: {remaining}"
        
        results, failed_urls = scrape_all(driver, urls, today, bar_format, existing_artist_ids)
        
        if failed_urls:
            print(Fore.YELLOW + f"\nRetrying {len(failed_urls)} failed URLs...")
            retry_results, still_failed = retry_failed(driver, failed_urls, today)
            results.extend(retry_results)
            failed_urls = still_failed
            
        save_results(results, today)
        report(results, failed_urls)
        
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\nScraping interrupted by user. Saving partial results...")
        if 'results' in locals():
            save_results(results, today)
            report(results, failed_urls if 'failed_urls' in locals() else [])
        print("Partial results saved.")
    except Exception as e:
        print(Fore.RED + f"\nUnexpected error during scraping: {e}")
        print("This might be due to network issues or Spotify blocking requests.")
        print("Try running the script again later or with fewer concurrent requests.")
        if 'results' in locals() and results:
            print("Saving partial results...")
            save_results(results, today)
            print("Partial results saved.")
        raise
    finally:
        if driver:
            try:
                print("Closing browser...")
                driver.quit()
            except Exception as e:
                print(Fore.YELLOW + f"Warning: Error closing browser: {e}")
                # Force kill if normal quit fails
                kill_chrome_processes()


if __name__ == "__main__":
    main()

