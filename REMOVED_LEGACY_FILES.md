## Removed Legacy Scripts (July 2025)

The following obsolete scripts were deleted as part of the final cleanup:

- `scraping/scrape_filtered.py` (filtered scraping, now redundant)
- `scraping/process_suggestions.py` (legacy suggestion processing)
- `scraping/spotify_follow_sync.py` (dual-account sync, obsolete)
- `scripts/merge_artists.py` (legacy merge logic)
- `scripts/test_oauth_api.py` (legacy OAuth test)
- `scripts/test_suggestion_messages.py` (legacy suggestion test)

All scraping and artist management is now handled by `scrape.py` and the admin panel workflow.
# Legacy scripts and files removed after workflow refactor

The following files were removed as part of the migration away from the suggestion/approval/processing workflow:
- scripts/test_suggestion_messages.py
- scripts/merge_artists.py
- scripts/test_oauth_api.py
- scraping/process_suggestions.py
- scraping/process_suggestions.log

If you need to restore any of these for historical reference, check your version control history.
