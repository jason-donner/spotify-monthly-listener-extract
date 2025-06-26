# Maintenance & Migration Tools Documentation

## Overview

The Spotify Monthly Listener Extract system includes comprehensive maintenance tools to handle data integrity issues, perform migrations, and fix various edge cases that can occur during normal operation.

---

## 🔧 Available Tools

### 1. Fix Stuck Suggestions

**Purpose**: Repairs suggestions that are approved but stuck in limbo (missing follow data)

**When to Use**:
- After upgrading to auto-follow system
- When suggestions show as "approved" but don't appear in "Processed" tab
- Data integrity issues with suggestion processing

**How it Works**:
- Identifies suggestions with `status: "approved"` but missing `already_followed` field
- Adds missing metadata (`already_followed: true`, `admin_action_date`)
- Adds artists to followed artists database if missing
- Preserves original suggestion data

### 2. Data Deduplication

**Purpose**: Removes duplicate entries from listener data

**When to Use**:
- After importing data from multiple sources
- Before major data migrations
- Monthly maintenance routines

**Available Scripts**:
- `scripts/dedupe_daily_last.py` - Remove duplicates keeping most recent
- Data service built-in deduplication functions

### 3. Date Format Standardization

**Purpose**: Ensures consistent date formats across all data files

**When to Use**:
- After importing legacy data
- When mixing YYYY-MM-DD and YYYYMMDD formats
- Data consistency verification

---

## 🖥️ Admin Panel Tools

### Maintenance Section

Located in Admin Panel → Maintenance & Data Fixes

#### Fix Stuck Suggestions Button
```javascript
// Accessible via admin panel
function fixStuckSuggestions() {
    // Confirms action with user
    // Calls /admin/fix_stuck_suggestions endpoint
    // Provides detailed feedback
    // Reloads suggestions to show changes
}
```

**Features**:
- ✅ Confirmation dialog before executing
- 📊 Shows count of fixed suggestions
- 🔄 Auto-refreshes admin panel after completion
- 📝 Detailed success/error messages

### Scheduler Management

**Purpose**: Manage automated daily scraping

**Features**:
- Set custom scraping times
- View next scheduled run
- Manually trigger full scraping
- Monitor scheduler status

---

## 📝 Command Line Scripts

### Fix Stuck Suggestions Script

**Location**: `scripts/fix_stuck_suggestions.py`

**Usage**:
```bash
cd "Spotify Monthly Listener Extract"
python scripts/fix_stuck_suggestions.py
```

**Sample Output**:
```
🔧 Fixing stuck suggestions...
Suggestions file: webapp/artist_suggestions.json
Followed artists file: data/results/spotify-followed-artists-master.json

🔍 Found 3 stuck suggestion(s):
  - Artist One (ID: abc123)
  - Artist Two (ID: def456)
  - Artist Three (ID: ghi789)

🔧 Processing: Artist One
  ✅ Added to followed artists

🔧 Processing: Artist Two
  ✅ Added to followed artists

🔧 Processing: Artist Three
  ℹ️ Already in followed artists list

💾 Saving changes...
  ✅ Updated suggestions file
  ✅ Updated followed artists file

🎉 Migration complete!
  - Fixed 3 stuck suggestion(s)
  - Added 2 artist(s) to followed list
  - All approved suggestions are now properly processed
```

**Features**:
- 🛡️ Safe execution with confirmation
- 📊 Detailed progress reporting
- 🔍 Duplicate detection and prevention
- 💾 Atomic operations (all-or-nothing)

### Deduplication Scripts

**Location**: `scripts/dedupe_daily_last.py`

**Usage**:
```bash
python scripts/dedupe_daily_last.py
```

**Purpose**: Remove duplicate listener entries, keeping the most recent data for each artist/date combination.

---

## 🗄️ Data File Structures

### Before Migration (Stuck Suggestion)
```json
{
  "artist_name": "Example Artist",
  "spotify_id": "1234567890",
  "timestamp": "2025-06-25T10:00:00",
  "status": "approved"
  // Missing: already_followed, admin_action_date
}
```

### After Migration (Fixed)
```json
{
  "artist_name": "Example Artist",
  "spotify_id": "1234567890",
  "timestamp": "2025-06-25T10:00:00",
  "status": "approved",
  "already_followed": true,
  "admin_action_date": "2025-06-25T22:33:00.000000"
}
```

### Followed Artists Entry (Added)
```json
{
  "artist_name": "Example Artist",
  "artist_id": "1234567890",
  "url": "https://open.spotify.com/artist/1234567890",
  "source": "migration_fix",
  "date_added": "2025-06-25",
  "removed": false
}
```

---

## 🔍 Diagnostic Tools

### Verify Data Integrity

**Check for Stuck Suggestions**:
```bash
# Look for approved suggestions without follow data
python -c "
import json
with open('webapp/artist_suggestions.json') as f:
    suggestions = json.load(f)
stuck = [s for s in suggestions if s.get('status') == 'approved' and not s.get('already_followed')]
print(f'Found {len(stuck)} stuck suggestions')
for s in stuck:
    print(f'  - {s.get(\"artist_name\", \"Unknown\")}')
"
```

**Check Data File Sizes**:
```bash
# Verify data files exist and have reasonable sizes
dir data\results\*.json
dir webapp\artist_*.json
```

**Validate JSON Syntax**:
```bash
# Test that JSON files are valid
python -m json.tool webapp/artist_suggestions.json > nul
python -m json.tool data/results/spotify-followed-artists-master.json > nul
echo "JSON files are valid"
```

---

## 🛡️ Safety Features

### Backup Creation

All maintenance tools create automatic backups:
```
webapp/artist_suggestions.json.backup.YYYYMMDD_HHMMSS
data/results/spotify-followed-artists-master.json.backup.YYYYMMDD_HHMMSS
```

### Atomic Operations

- Changes are made to memory first
- Files are only written if all operations succeed
- Rollback capability if any step fails

### Validation Checks

- JSON syntax validation before saving
- Duplicate ID prevention
- Required field validation
- Data type checking

---

## 📋 Maintenance Schedule

### Daily
- Automated scraping runs
- Built-in duplicate prevention during scraping

### Weekly  
- Check admin panel for stuck suggestions
- Review suggestion processing stats

### Monthly
- Run data integrity verification
- Clean up old backup files
- Review and update blacklist if needed

### Quarterly
- Full data deduplication run
- Archive old daily data files
- Review and update maintenance procedures

---

## 🚨 Emergency Procedures

### Complete Data Corruption

1. **Stop the web application**
2. **Restore from Git** (only includes template files)
3. **Restore data from backups**:
   ```bash
   copy "data\results\*.backup.*" "data\results\"
   copy "webapp\*.backup.*" "webapp\"
   ```
4. **Run data integrity verification**
5. **Restart application**

### Partial Data Issues

1. **Identify affected files**
2. **Run appropriate fix script**:
   ```bash
   python scripts/fix_stuck_suggestions.py
   python scripts/dedupe_daily_last.py
   ```
3. **Verify fixes in admin panel**
4. **Monitor for recurrence**

### Lost Followed Artists

1. **Use Spotify API to re-fetch followed artists**:
   ```bash
   cd scraping
   python get_artists.py
   ```
2. **Compare with existing data**
3. **Merge missing artists manually if needed**

---

## 📈 Monitoring & Alerts

### Success Indicators
- ✅ All approved suggestions have `already_followed: true`
- ✅ No duplicate entries in listener data
- ✅ Consistent date formats across files
- ✅ Admin panel loads without errors

### Warning Signs
- ⚠️ Suggestions stuck in "Pending" for >24 hours
- ⚠️ Large number of failed follow attempts
- ⚠️ JSON parsing errors in logs
- ⚠️ Unusual file size changes

### Error Conditions
- ❌ Cannot load suggestion/artist data files
- ❌ Admin panel maintenance tools failing
- ❌ Duplicate prevention not working
- ❌ Auto-follow system not functioning
