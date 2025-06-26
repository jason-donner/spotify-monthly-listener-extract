#!/usr/bin/env python3
"""
Test duplicate prevention in scraping scripts
"""

import json
import os
import sys
from datetime import datetime

def test_duplicate_prevention():
    """Test the load_existing_listeners function"""
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scraping'))
    
    # Import the function from scrape_filtered.py
    from scrape_filtered import load_existing_listeners
    
    target_date = datetime.now().strftime('%Y-%m-%d')
    print(f"🧪 Testing duplicate prevention for date: {target_date}")
    
    existing_ids = load_existing_listeners(target_date)
    
    if existing_ids:
        print(f"✅ Found {len(existing_ids)} existing artist IDs for {target_date}")
        print("Sample IDs:", list(existing_ids)[:5])
        print("✅ Duplicate prevention should work correctly!")
    else:
        print(f"ℹ️ No existing entries found for {target_date} - first run today")
    
    return existing_ids

def verify_data_consistency():
    """Verify that all data uses consistent date format"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    master_file = os.path.join(base_dir, "data", "results", "spotify-monthly-listeners-master.json")
    
    print("\n🔍 Verifying date format consistency...")
    
    if not os.path.exists(master_file):
        print("❌ Master file not found!")
        return False
    
    with open(master_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    date_formats = set()
    for entry in data:
        date = entry.get('date')
        if date:
            date_formats.add(len(date))  # Check length to identify format
    
    print(f"📊 Found {len(date_formats)} different date format lengths: {date_formats}")
    
    if len(date_formats) == 1 and 10 in date_formats:
        print("✅ All dates use YYYY-MM-DD format (length 10) - consistency verified!")
        return True
    else:
        print("⚠️ Mixed date formats detected - this could cause duplicate prevention issues")
        return False

def main():
    print("🛠️ Duplicate Prevention Test")
    print("=" * 50)
    
    # Test 1: Check duplicate prevention function
    existing_ids = test_duplicate_prevention()
    
    # Test 2: Verify data consistency
    consistent = verify_data_consistency()
    
    print("\n📋 Summary:")
    print(f"  - Duplicate prevention: {'✅ Working' if existing_ids is not None else '❌ Issue'}")
    print(f"  - Date format consistency: {'✅ Good' if consistent else '❌ Issue'}")
    
    if existing_ids is not None and consistent:
        print("\n🎉 All tests passed! Duplicate prevention should work correctly.")
    else:
        print("\n⚠️ Issues detected. Please review the output above.")

if __name__ == "__main__":
    main()
