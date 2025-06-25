#!/usr/bin/env python3
"""
Chrome/ChromeDriver Diagnostic Tool
Helps troubleshoot browser session issues for Spotify scraping
"""

import os
import sys
import platform
import subprocess
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def get_chrome_version():
    """Get the installed Chrome version."""
    try:
        if platform.system() == "Windows":
            # Try multiple possible Chrome paths
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    result = subprocess.run([chrome_path, "--version"], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        return result.stdout.strip()
        else:
            # Linux/Mac
            result = subprocess.run(["google-chrome", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
                
    except Exception as e:
        return f"Error getting Chrome version: {e}"
    
    return "Chrome not found or version unavailable"

def get_chromedriver_version():
    """Get the ChromeDriver version."""
    try:
        result = subprocess.run(["chromedriver", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        return f"Error getting ChromeDriver version: {e}"
    
    return "ChromeDriver not found or not in PATH"

def kill_chrome_processes():
    """Kill any existing Chrome processes."""
    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                         capture_output=True, check=False)
            subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], 
                         capture_output=True, check=False)
        else:
            subprocess.run(["pkill", "-f", "chrome"], capture_output=True, check=False)
            subprocess.run(["pkill", "-f", "chromedriver"], capture_output=True, check=False)
        return True
    except Exception as e:
        return f"Error killing Chrome processes: {e}"

def test_basic_chrome_session():
    """Test if we can create a basic Chrome session."""
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222")
        
        service = Service("chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        
        # Test basic functionality
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        return f"Success! Page title: {title}"
        
    except Exception as e:
        return f"Failed: {e}"

def test_spotify_access():
    """Test if we can access Spotify specifically."""
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222")
        
        service = Service("chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get("https://open.spotify.com")
        title = driver.title
        driver.quit()
        
        return f"Success! Spotify page title: {title}"
        
    except Exception as e:
        return f"Failed: {e}"

def main():
    print("=" * 60)
    print("CHROME/CHROMEDRIVER DIAGNOSTIC TOOL")
    print("=" * 60)
    
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Python Version: {sys.version}")
    print()
    
    # Check Chrome version
    print("1. Chrome Version Check:")
    chrome_version = get_chrome_version()
    print(f"   {chrome_version}")
    print()
    
    # Check ChromeDriver version
    print("2. ChromeDriver Version Check:")
    chromedriver_version = get_chromedriver_version()
    print(f"   {chromedriver_version}")
    print()
    
    # Kill existing processes
    print("3. Cleaning Up Existing Chrome Processes:")
    kill_result = kill_chrome_processes()
    if kill_result == True:
        print("   ✓ Chrome processes cleaned up")
    else:
        print(f"   ⚠ {kill_result}")
    print()
    
    # Test basic Chrome session
    print("4. Basic Chrome Session Test:")
    basic_test = test_basic_chrome_session()
    if "Success" in basic_test:
        print(f"   ✓ {basic_test}")
    else:
        print(f"   ✗ {basic_test}")
    print()
    
    # Test Spotify access
    print("5. Spotify Access Test:")
    spotify_test = test_spotify_access()
    if "Success" in spotify_test:
        print(f"   ✓ {spotify_test}")
    else:
        print(f"   ✗ {spotify_test}")
    print()
    
    print("=" * 60)
    print("RECOMMENDATIONS:")
    
    if "not found" in chromedriver_version.lower():
        print("• Download ChromeDriver from https://chromedriver.chromium.org/")
        print("• Make sure ChromeDriver is in your PATH or specify --chromedriver path")
    
    if "not found" in chrome_version.lower():
        print("• Install Google Chrome from https://www.google.com/chrome/")
    
    if "Failed" in basic_test:
        print("• Try updating both Chrome and ChromeDriver to latest versions")
        print("• Make sure versions are compatible")
        print("• Try running as administrator (Windows) or with sudo (Linux)")
    
    if "Failed" in spotify_test and "Success" in basic_test:
        print("• Network connectivity to Spotify may be blocked")
        print("• Try using a VPN or different network")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
