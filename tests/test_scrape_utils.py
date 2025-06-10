from unittest.mock import MagicMock
from src.scrape import scrape_artist

def test_scrape_artist_handles_missing_elements():
    driver = MagicMock()
    driver.get.return_value = None
    # Simulate element not found
    driver.find_element.side_effect = Exception("Not found")
    result = scrape_artist(driver, {"url": "https://open.spotify.com/artist/123"})
    assert result is None or result == (None, None)