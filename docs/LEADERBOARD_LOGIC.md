# Leaderboard Data Logic

## Overview
The leaderboard displays the top 10 artists with the highest percentage growth (or loss) in monthly listeners for a specific time period.

## Current Month Implementation

### Date Range Calculation
As of June 25, 2025, the leaderboard uses **current month** filtering instead of a rolling 30-day window.

```python
if current_month:
    # Get start and end of current month
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)
    cutoff = start_of_month
else:
    # Use traditional 30-day lookback
    cutoff = datetime.now() - timedelta(days=30)
```

### Data Processing Steps

1. **Load Data**: All historical monthly listener data is loaded
2. **Filter by Date**: Only entries from the current month (June 1, 2025 onwards) are considered
3. **Group by Artist**: Data is grouped by artist name
4. **Minimum Data Requirement**: Artists must have at least 2 data points in the month
5. **Calculate Changes**: 
   - Absolute change: `end_listeners - start_listeners`
   - Percentage change: `((end - start) / start) * 100`
6. **Filter by Tier**: Artists are filtered by listener count tiers if specified
7. **Sort and Limit**: Top 10 artists by percentage change (growth or loss)

### Tier Definitions
- **Micro**: ≤ 1,000 monthly listeners
- **Small**: 1,001 - 3,000 monthly listeners  
- **Medium**: 3,001 - 15,000 monthly listeners
- **Large**: 15,001 - 50,000 monthly listeners
- **Major**: > 50,000 monthly listeners

### Date Display Logic
The leaderboard displays "Showing data for [Month Year]" format:
- June 2025: Shows all data from June 1, 2025 to current date
- July 2025: Will automatically show July 1, 2025 onwards (when July arrives)

### Example Output Structure
```json
{
  "leaderboard": [
    {
      "artist": "Artist Name",
      "artist_id": "spotify_id",
      "change": 15000,
      "percent_change": 25.5,
      "start": 60000,
      "end": 75000,
      "artist_url": "https://open.spotify.com/artist/..."
    }
  ],
  "start_date": "2025-06-01T00:00:00",
  "end_date": "2025-06-25T23:59:59",
  "mode": "growth",
  "tier": "all"
}
```

## Benefits of Current Month Approach

1. **Consistent Timeframe**: All users see the same period regardless of access date
2. **Monthly Performance**: Better reflects how artists perform in specific months
3. **Easier Understanding**: "June 2025" is clearer than "May 25 - June 25"
4. **Calendar Aligned**: Matches how people naturally think about time periods

## Future Enhancements

### Possible Additions
- **Month Navigation**: Previous/next month buttons
- **Time Period Toggle**: Switch between current month and last 30 days
- **Historical View**: Compare current month to same month last year
- **Export Options**: Download leaderboard data for specific months

### Technical Considerations
- Consider caching leaderboard data for performance
- Add database indexes on date fields for faster queries
- Implement real-time updates when new data is scraped
