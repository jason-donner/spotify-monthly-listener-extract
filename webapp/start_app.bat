@echo off
echo Starting Spotify Monthly Listener Tracker...
cd /d "%~dp0"

echo Loading credentials from .env file...
echo.
echo NOTE: Make sure ADMIN_PASSWORD is set in your .env file
echo.
echo Starting app...

"%~dp0..\.venv\Scripts\python.exe" app.py
pause
