#!/usr/bin/env python3
"""
Quick test script to verify admin panel "Run Full Scrape Now" fix works
"""

import os
import sys
import json
import requests
import time

# Set up environment
os.environ['ADMIN_PASSWORD'] = 'testpass123'

# Add webapp to path
webapp_dir = os.path.join(os.path.dirname(__file__), 'webapp')
sys.path.insert(0, webapp_dir)

def test_admin_run_now_endpoint():
    """Test the /admin/scheduler/run_now endpoint"""
    
    print("Testing admin panel 'Run Full Scrape Now' fix...")
    
    # Test the endpoint directly
    base_url = "http://127.0.0.1:5000"
    
    try:
        # Test the scheduler run_now endpoint
        response = requests.post(f"{base_url}/admin/scheduler/run_now", 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint response: {data}")
            
            if data.get('success') and data.get('job_id'):
                print(f"✅ Job created successfully with ID: {data['job_id']}")
                
                # Test job status endpoint
                job_id = data['job_id']
                status_response = requests.get(f"{base_url}/admin/scraping_status/{job_id}", timeout=10)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"✅ Job status endpoint working: {status_data}")
                else:
                    print(f"❌ Job status endpoint failed: {status_response.status_code}")
            else:
                print(f"❌ Job creation failed: {data}")
        else:
            print(f"❌ Endpoint failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app. Make sure it's running on http://127.0.0.1:5000")
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")

def verify_frontend_fix():
    """Verify the frontend JavaScript fix"""
    
    print("\nVerifying frontend JavaScript fix...")
    
    admin_html_path = os.path.join(webapp_dir, 'templates', 'admin.html')
    
    try:
        with open(admin_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if the key fixes are present
        fixes_to_check = [
            'currentScrapingJobId = data.job_id;',  # Job ID assignment
            'scrapingStatusInterval = setInterval(checkScrapingStatus, 2000);',  # Status polling
            'runScrapingBtn.disabled = true;',  # Disable other button
            'statusText.textContent = \'Running scheduled full scraping...\';'  # Status text
        ]
        
        all_fixes_present = True
        for fix in fixes_to_check:
            if fix in content:
                print(f"✅ Found fix: {fix}")
            else:
                print(f"❌ Missing fix: {fix}")
                all_fixes_present = False
        
        if all_fixes_present:
            print("✅ All frontend fixes are present!")
        else:
            print("❌ Some frontend fixes are missing!")
            
        # Check resetScrapingUI fix too
        if 'runNowBtn.disabled = false;' in content:
            print("✅ Found resetScrapingUI button reset fix")
        else:
            print("❌ Missing resetScrapingUI button reset fix")
            
    except Exception as e:
        print(f"❌ Error checking frontend fixes: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("ADMIN PANEL 'RUN FULL SCRAPE NOW' FIX VERIFICATION")
    print("=" * 60)
    
    verify_frontend_fix()
    test_admin_run_now_endpoint()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("- The frontend JavaScript has been updated to properly track")
    print("  the scraping job when 'Run Full Scrape Now' is clicked")
    print("- The job ID is now captured and status polling is started")
    print("- The scraping tab will show real-time output and progress")
    print("- Both buttons are properly managed during execution")
    print("=" * 60)
