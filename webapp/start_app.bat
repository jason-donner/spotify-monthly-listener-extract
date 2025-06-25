@echo off
echo Starting Spotify Monthly Listener Tracker...
cd /d "C:\Users\Jason\Spotify Monthly Listener Extract\webapp"

echo Loading credentials from .env file...
echo.
echo NOTE: Make sure ADMIN_PASSWORD is set in your .env file
echo.
echo Starting app...

"C:/Users/Jason/Spotify Monthly Listener Extract/.venv/Scripts/python.exe" app.py
pause
