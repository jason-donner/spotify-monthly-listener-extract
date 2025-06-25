# Changelog

## [2025-06-25] - Real-Time Progress Indicator

### Added
- **Real-Time Progress Bar**: Visual progress tracking during scraping operations in admin panel
- **Live Artist Counter**: Shows current/total artists processed (e.g., "45/150")
- **Current Artist Display**: Shows which specific artist is currently being processed
- **Phase Tracking**: Clear status phases (Starting, Scraping, Completed)
- **Progress Animations**: Smooth green gradient progress bar with percentage display

### Technical Details
#### Backend Changes (`webapp/app/services/job_service.py`)
- Modified `_execute_scraping_job()` to use `subprocess.Popen` for real-time output capture
- Added `_parse_progress_line()` method to parse progress markers from scraping output
- Implemented line-by-line stdout processing for immediate progress updates
- Added progress data structure: `{current, total, phase, details, current_artist}`

#### Frontend Changes (`webapp/templates/admin.html`)
- Added progress bar UI component with Bootstrap styling
- Enhanced `updateScrapingUI()` function to handle progress data
- Added progress elements: progressBar, progressLabel, progressCounter, progressDetails
- Implemented conditional progress bar visibility (only shows when progress data available)

#### Scraping Script Changes (`scraping/scrape.py`)
- Added "PROGRESS:" prefixed output markers for reliable parsing
- Enhanced artist processing output with current/total counters
- Added structured progress messages for initialization and completion
- Maintained backward compatibility with existing tqdm progress bars

### Benefits
1. **Better User Experience**: Users can see exactly what's happening during long scraping operations
2. **Progress Transparency**: Clear visibility into scraping progress and current artist
3. **Professional UI**: Modern progress indicators with smooth animations
4. **Real-Time Feedback**: Updates every 2 seconds without blocking the interface
5. **Error Prevention**: Users can see if scraping is stuck on a specific artist

### Progress Output Format
```
PROGRESS: Starting scrape of 150 artists
PROGRESS: Processing artist 1/150: Artist Name
PROGRESS: Processing artist 2/150: Another Artist
...
PROGRESS: Completed scraping 150 artists
```

### UI Components
- **Progress Bar**: Green gradient bar showing percentage completion
- **Counter**: "45/150" format showing current position
- **Phase Label**: "Starting to scrape 150 artists" or "Scraping artists (45/150)"
- **Details**: "Processing: Artist Name" or "Successfully processed 150 artists"

---

## [2025-06-25] - Leaderboard Current Month Enhancement

### Changed
- **Leaderboard Date Range**: Modified leaderboard to show only current month data instead of last 30 days
- **Date Display**: Updated date range display from "Comparing data from [start] to [end]" to "Showing data for [Month Year]"
- **Data Filtering**: Enhanced `get_leaderboard_data()` method to filter by calendar month boundaries

### Technical Details
#### Backend Changes (`webapp/app/services/data_service.py`)
- Modified `get_leaderboard_data()` method signature:
  - Changed parameter from `days: int = 30` to `current_month: bool = True`
  - Added logic to calculate start of current month as cutoff date
  - Set explicit `start_date` and `end_date` for current month display

#### Frontend Changes (`webapp/templates/leaderboard.html`)
- Updated date range display section
- Changed from showing date range to showing month name only
- Format: "Showing data for June 2025" (using `start_date.strftime('%B %Y')`)

### Benefits
1. **More Relevant Data**: Shows artist performance for the current calendar month
2. **Cleaner UI**: Simplified date display that's easier to understand
3. **Automatic Updates**: Will automatically show "July 2025" when July arrives
4. **Consistent Timeframe**: All users see the same month period regardless of when they access the site

### Migration Notes
- No database migration required
- Existing data remains unchanged
- Feature is backward compatible
- Default behavior changed from 30-day lookback to current month

### Future Considerations
- Could add toggle option to switch between "current month" and "last 30 days" views
- Could extend to show previous months in a dropdown
- Consider adding month navigation controls

---

## [2025-06-25] - Authentication Security Fix

### Fixed
- **Admin Route Security**: Added missing `@admin_login_required` decorators to scraping endpoints
- **Environment Variables**: Fixed `ADMIN_PASSWORD` environment variable handling
- **"Failed to fetch" Error**: Resolved authentication issues preventing admin scraping functionality

### Technical Details
- Added `@admin_login_required` decorator to `/admin/run_scraping` endpoint
- Added `@admin_login_required` decorator to `/admin/scraping_status/<job_id>` endpoint
- Added `@admin_login_required` decorator to `/admin/scraping_jobs` endpoint
- Updated documentation for proper environment variable setup

---

## [Previous Updates]
See README.md for complete feature history and improvements.
