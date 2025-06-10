from src.scrape import scrape_artist, parse_args

def test_parse_args_defaults(monkeypatch):
    monkeypatch.setenv("CHROMEDRIVER_PATH", "/tmp/chromedriver")
    args = parse_args()
    assert args.chromedriver == "/tmp/chromedriver"