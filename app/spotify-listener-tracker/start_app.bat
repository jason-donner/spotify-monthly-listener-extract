@echo off
echo Starting Spotify Monthly Listener Tracker...
cd /d "C:\Users\Jason\Spotify Monthly Listener Extract\app\spotify-listener-tracker"

REM Set correct Spotify API credentials (these override any system variables)
set SPOTIPY_CLIENT_ID=5e36297fe74744de9fd4a7cf6c3a9941
set SPOTIPY_CLIENT_SECRET=703744d10ba54d779b199134a85333bc
set SPOTIPY_REDIRECT_URI=http://127.0.0.1:5000/callback

echo Environment variables set:
echo Client ID: %SPOTIPY_CLIENT_ID%
echo Redirect URI: %SPOTIPY_REDIRECT_URI%
echo Starting app...

"C:/Users/Jason/Spotify Monthly Listener Extract/.venv/Scripts/python.exe" app.py
pause
