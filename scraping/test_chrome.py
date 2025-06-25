#!/usr/bin/env python3
"""
Quick Chrome session test
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from scrape import setup_driver, kill_chrome_processes
from colorama import Fore, init

init(autoreset=True)

def test_chrome_setup():
    print("Testing Chrome WebDriver setup...")
    
    try:
        # Clean up any existing processes first
        print("Cleaning up existing Chrome processes...")
        kill_chrome_processes()
        
        # Test headless mode first (more reliable)
        print("Attempting to create headless Chrome driver...")
        driver = setup_driver(headless=True)
        
        if driver:
            print(Fore.GREEN + "✓ Headless Chrome driver created successfully!")
            
            # Test basic functionality
            driver.get("https://www.google.com")
            title = driver.title
            print(f"✓ Successfully navigated to Google. Title: {title}")
            
            driver.quit()
            print("✓ Driver closed successfully")
            return True
        else:
            print(Fore.RED + "✗ Failed to create driver")
            return False
            
    except Exception as e:
        print(Fore.RED + f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_chrome_setup()
    if success:
        print(Fore.GREEN + "\n🎉 Chrome setup is working! The scraping script should work now.")
    else:
        print(Fore.RED + "\n❌ Chrome setup failed. Check the error messages above.")
