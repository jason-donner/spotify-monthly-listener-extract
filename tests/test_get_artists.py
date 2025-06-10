import os
import tempfile
import json
from src.get_artists import save_artist_list

def test_save_artist_list_creates_file():
    artist_list = [
        {"name": "Test Artist", "url": "https://open.spotify.com/artist/123"}
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.json")
        save_artist_list(artist_list, output_path)
        assert os.path.exists(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data == artist_list