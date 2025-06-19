@echo off
REM Spotify Monthly Listener Extract Automation Script
REM Prerequisites:
REM - Python installed and in PATH
REM - Virtual environment created as '.venv'
REM - Dependencies installed in the virtual environment

cd /d "%~dp0"

REM Set log file path
set LOGFILE=automation.log

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found. Please create it with 'python -m venv .venv'.
    exit /b 1
)

call "%~dp0.venv\Scripts\activate.bat"

echo %DATE% %TIME% - Starting monthly listener workflow >> %LOGFILE%

REM Step 1: Synchronize followed artists
echo Running spotify_follow_sync.py to sync followed artists...
"%~dp0.venv\Scripts\python.exe" src\spotify_follow_sync.py
if errorlevel 1 (
    echo %DATE% %TIME% - ERROR: spotify_follow_sync.py failed with exit code %ERRORLEVEL% >> %LOGFILE%
    pause
    exit /b %ERRORLEVEL%
)

REM Step 2: Run get_artists.py
"%~dp0.venv\Scripts\python.exe" src\get_artists.py --log get_artists.log
if errorlevel 1 (
    echo %DATE% %TIME% - ERROR: get_artists.py failed with exit code %ERRORLEVEL% >> %LOGFILE%
    exit /b %ERRORLEVEL%
)

REM Step 3: Run scrape.py
echo Running scrape.py...
"%~dp0.venv\Scripts\python.exe" src\scrape.py
echo scrape.py exited with %ERRORLEVEL%
if errorlevel 1 (
    echo %DATE% %TIME% - ERROR: scrape.py failed with exit code %ERRORLEVEL% >> %LOGFILE%
    pause
    exit /b %ERRORLEVEL%
)

echo %DATE% %TIME% - Monthly listener workflow completed >> %LOGFILE%
pause