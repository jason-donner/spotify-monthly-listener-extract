#!/usr/bin/env python3
"""
Pre-Public Release Security Validation Script
Checks for sensitive data before making repository public
"""

import os
import json
import re
from pathlib import Path

def check_for_secrets():
    """Check for potential secrets in files"""
    issues = []
    
    # Sensitive patterns to look for
    patterns = {
        'spotify_client_id': r'5e36297fe74744de',
        'spotify_client_secret': r'703744d10ba54d77', 
        'admin_password': r'faith!995',
        'personal_path': r'C:\\Users\\Jason',
        'real_flask_key': r'3xtr3m3ly-s3cur3-fl4sk-s3cr3t'
    }
    
    # Files to check
    for root, dirs, files in os.walk('.'):
        # Skip git directory
        if '.git' in dirs:
            dirs.remove('.git')
        
        for file in files:
            if file.endswith(('.py', '.bat', '.md', '.txt', '.json', '.env')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern_name, pattern in patterns.items():
                        if re.search(pattern, content, re.IGNORECASE):
                            issues.append(f"❌ {pattern_name} found in {filepath}")
                except Exception as e:
                    print(f"⚠️  Could not read {filepath}: {e}")
    
    return issues

def check_env_files():
    """Check .env files for real credentials"""
    issues = []
    
    env_files = [
        'webapp/.env',
        '.env'
    ]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                content = f.read()
                
            # Check for placeholder values
            if 'your_spotify_client_id_here' not in content:
                issues.append(f"❌ {env_file} may contain real Spotify credentials")
            if 'your_secure_admin_password_here' not in content:
                issues.append(f"❌ {env_file} may contain real admin password")
                
    return issues

def check_json_files():
    """Check JSON files for personal data"""
    issues = []
    
    json_files = [
        'webapp/artist_suggestions.json',
        'webapp/artist_blacklist.json'
    ]
    
    for json_file in json_files:
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                if data != []:
                    issues.append(f"❌ {json_file} contains data - should be empty for public release")
            except Exception as e:
                issues.append(f"❌ Could not parse {json_file}: {e}")
                
    return issues

def check_git_tracking():
    """Check what files are tracked by git"""
    issues = []
    
    # Check if sensitive files are tracked
    os.system('git ls-files > git_tracked_files.tmp')
    
    if os.path.exists('git_tracked_files.tmp'):
        with open('git_tracked_files.tmp', 'r') as f:
            tracked_files = f.read()
        
        sensitive_patterns = ['.env', 'token', 'cache', '.log']
        
        for pattern in sensitive_patterns:
            if pattern in tracked_files and pattern != '.env.example':
                issues.append(f"❌ Potentially sensitive files with '{pattern}' are tracked by git")
        
        # Clean up
        os.remove('git_tracked_files.tmp')
    
    return issues

def main():
    print("🔒 Pre-Public Release Security Validation")
    print("=" * 50)
    
    all_issues = []
    
    print("\n🔍 Checking for secrets in files...")
    secret_issues = check_for_secrets()
    all_issues.extend(secret_issues)
    
    print("\n🔍 Checking .env files...")
    env_issues = check_env_files()
    all_issues.extend(env_issues)
    
    print("\n🔍 Checking JSON data files...")
    json_issues = check_json_files()
    all_issues.extend(json_issues)
    
    print("\n🔍 Checking git tracking...")
    git_issues = check_git_tracking()
    all_issues.extend(git_issues)
    
    print("\n" + "=" * 50)
    
    if all_issues:
        print("❌ ISSUES FOUND - DO NOT MAKE PUBLIC YET:")
        for issue in all_issues:
            print(f"   {issue}")
        print(f"\n❌ Total issues: {len(all_issues)}")
        print("❌ Repository is NOT ready for public release")
        return False
    else:
        print("✅ No sensitive data found!")
        print("✅ Repository appears ready for public release")
        print("\n💡 Final manual checks recommended:")
        print("   - Review commit history for any missed secrets")
        print("   - Test fresh installation with placeholder credentials")
        print("   - Verify all documentation is accurate")
        return True

if __name__ == "__main__":
    main()
