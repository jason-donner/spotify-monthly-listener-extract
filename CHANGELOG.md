# Changelog

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
