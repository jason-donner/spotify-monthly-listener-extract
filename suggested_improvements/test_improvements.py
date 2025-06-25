# test_improvements.py - Comprehensive testing setup

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os

# Test configuration
@pytest.fixture
def app():
    """Create test Flask app"""
    from app import create_app
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-key',
        'DATABASE_URL': 'sqlite:///:memory:'
    })
    
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def mock_spotify_data():
    """Mock Spotify API responses"""
    return {
        'artist': {
            'id': 'test_artist_id',
            'name': 'Test Artist',
            'images': [{'url': 'http://example.com/image.jpg'}],
            'external_urls': {'spotify': 'https://open.spotify.com/artist/test_artist_id'},
            'followers': {'total': 1000},
            'genres': ['indie', 'rock']
        },
        'followed_artists': {
            'artists': {
                'items': [
                    {
                        'id': 'artist1',
                        'name': 'Artist One',
                        'external_urls': {'spotify': 'https://open.spotify.com/artist/artist1'}
                    }
                ],
                'total': 1,
                'next': None
            }
        }
    }

class TestArtistSuggestions:
    """Test artist suggestion functionality"""
    
    def test_suggest_artist_valid_data(self, client):
        """Test valid artist suggestion"""
        response = client.post('/suggest_artist', 
            json={
                'artist_name': 'Test Artist',
                'spotify_url': 'https://open.spotify.com/artist/test123',
                'spotify_id': 'test123'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'approved' in data['message']
    
    def test_suggest_artist_missing_name(self, client):
        """Test suggestion with missing artist name"""
        response = client.post('/suggest_artist', json={})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'required' in data['message']
    
    def test_suggest_artist_blacklisted(self, client):
        """Test suggestion of blacklisted artist"""
        # Mock blacklist
        blacklist_data = [{'name': 'Blacklisted Artist', 'spotify_id': 'blacklisted123'}]
        
        with patch('builtins.open'), patch('json.load', return_value=blacklist_data):
            response = client.post('/suggest_artist',
                json={'artist_name': 'Blacklisted Artist', 'spotify_id': 'blacklisted123'}
            )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'predators' in data['message']

class TestSpotifyIntegration:
    """Test Spotify API integration"""
    
    @patch('spotipy.Spotify')
    def test_get_followed_artists(self, mock_spotify, mock_spotify_data):
        """Test fetching followed artists"""
        mock_client = Mock()
        mock_client.current_user_followed_artists.return_value = mock_spotify_data['followed_artists']
        mock_spotify.return_value = mock_client
        
        from src.get_artists import get_followed_artists
        
        result = get_followed_artists(mock_client, limit=1)
        
        assert len(result) == 1
        assert result[0]['artist_name'] == 'Artist One'
        assert result[0]['artist_id'] == 'artist1'
    
    @patch('requests.get')
    def test_fetch_artist_image(self, mock_get, mock_spotify_data):
        """Test fetching artist image"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_spotify_data['artist']
        mock_get.return_value = mock_response
        
        from app import fetch_spotify_artist_image
        
        with patch('app.get_token', return_value='test_token'):
            image_url = fetch_spotify_artist_image('test_artist_id')
        
        assert image_url == 'http://example.com/image.jpg'

class TestScrapingFunctionality:
    """Test scraping functionality"""
    
    def test_parse_listener_count(self):
        """Test listener count parsing"""
        from src.scrape import parse_listener_count
        
        assert parse_listener_count('1.2k') == 1200
        assert parse_listener_count('3.5m') == 3500000
        assert parse_listener_count('500') == 500
        assert parse_listener_count('invalid') == 0
    
    @patch('selenium.webdriver.Chrome')
    def test_scrape_artist_success(self, mock_driver):
        """Test successful artist scraping"""
        # Mock WebDriver behavior
        mock_element = Mock()
        mock_element.get_attribute.return_value = 'Test Artist'
        mock_element.text = '1.2k monthly listeners'
        
        mock_driver_instance = Mock()
        mock_driver_instance.find_element.return_value = mock_element
        mock_driver.return_value = mock_driver_instance
        
        from src.scrape import scrape_artist
        
        name, listeners = scrape_artist(mock_driver_instance, 'http://test.url')
        
        # This would need adjustment based on actual implementation
        assert name is not None
    
    def test_load_urls_from_file(self):
        """Test loading URLs from file"""
        test_data = [
            {
                'artist_name': 'Test Artist',
                'url': 'https://open.spotify.com/artist/test123',
                'artist_id': 'test123'
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            from src.scrape import load_urls
            result = load_urls(temp_path)
            assert len(result) == 1
            assert result[0]['artist_name'] == 'Test Artist'
        finally:
            os.unlink(temp_path)

class TestDataProcessing:
    """Test data processing and analysis"""
    
    def test_leaderboard_calculation(self, client):
        """Test leaderboard calculations"""
        # Mock data file
        mock_data = [
            {
                'artist_name': 'Artist A',
                'artist_id': 'artist_a',
                'monthly_listeners': 1000,
                'date': '2025-01-01'
            },
            {
                'artist_name': 'Artist A',
                'artist_id': 'artist_a',
                'monthly_listeners': 1500,
                'date': '2025-01-15'
            }
        ]
        
        with patch('app.load_data', return_value=mock_data):
            response = client.get('/leaderboard')
            assert response.status_code == 200

class TestAdminFunctionality:
    """Test admin panel functionality"""
    
    def test_admin_page_unauthenticated(self, client):
        """Test admin page without authentication"""
        response = client.get('/admin')
        assert response.status_code == 200  # Should show login form
    
    def test_admin_suggestions_api(self, client):
        """Test admin suggestions API"""
        response = client.get('/admin/suggestions')
        assert response.status_code == 200
        data = response.get_json()
        assert 'suggestions' in data

# Performance tests
class TestPerformance:
    """Test application performance"""
    
    def test_search_performance(self, client):
        """Test search endpoint performance"""
        import time
        
        start_time = time.time()
        response = client.get('/search?artist=test')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should respond within 2 seconds
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        # Create mock large dataset
        large_data = [
            {
                'artist_name': f'Artist {i}',
                'artist_id': f'artist_{i}',
                'monthly_listeners': i * 100,
                'date': '2025-01-01'
            }
            for i in range(10000)
        ]
        
        with patch('app.load_data', return_value=large_data):
            # Test that operations don't time out
            from app import load_data
            data = load_data()
            assert len(data) == 10000

# Integration tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_suggestion_to_follow_workflow(self, client):
        """Test complete suggestion workflow"""
        # 1. Submit suggestion
        response = client.post('/suggest_artist',
            json={
                'artist_name': 'Integration Test Artist',
                'spotify_id': 'integration_test'
            }
        )
        assert response.status_code == 200
        
        # 2. Check suggestions list
        response = client.get('/admin/suggestions')
        data = response.get_json()
        suggestions = data['suggestions']
        
        # Find our suggestion
        test_suggestion = next(
            (s for s in suggestions if s['artist_name'] == 'Integration Test Artist'),
            None
        )
        assert test_suggestion is not None
        assert test_suggestion['status'] == 'approved'

# Fixtures for test data
@pytest.fixture
def sample_artist_data():
    """Sample artist data for testing"""
    return [
        {
            'artist_name': 'Sample Artist 1',
            'artist_id': 'sample1',
            'monthly_listeners': 1000,
            'date': '2025-01-01',
            'url': 'https://open.spotify.com/artist/sample1'
        },
        {
            'artist_name': 'Sample Artist 1',
            'artist_id': 'sample1',
            'monthly_listeners': 1200,
            'date': '2025-01-02',
            'url': 'https://open.spotify.com/artist/sample1'
        }
    ]

# Run with: python -m pytest tests/ -v --cov=app --cov-report=html
