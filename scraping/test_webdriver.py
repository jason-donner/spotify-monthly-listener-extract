#!/usr/bin/env python3
"""Quick test of the improved WebDriver setup"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from scrape import setup_driver

print("Testing improved WebDriver setup...")
try:
    driver = setup_driver(headless=True)
    if driver:
        print("✅ SUCCESS: WebDriver created successfully!")
        print("Testing navigation...")
        driver.get("https://www.google.com")
        print("✅ Navigation test passed!")
        driver.quit()
        print("✅ WebDriver cleanup completed!")
    else:
        print("❌ Failed to create WebDriver")
except Exception as e:
    print(f"❌ Test failed: {e}")
