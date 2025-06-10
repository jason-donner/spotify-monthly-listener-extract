@echo off
REM Spotify Monthly Listener Extract Automation Script
REM Prerequisites:
REM - Python installed and in PATH
REM - Virtual environment created as '.venv'
REM - Dependencies installed in the virtual environment
REM
REM Usage: Double-click or run from command line

cd /d "%~dp0"

REM Set log file path
set LOGFILE=automation.log

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate" (
    echo ERROR: Virtual environment not found. Please create it with 'python -m venv .venv'.
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate

REM Log start
echo %DATE% %TIME% - Starting monthly listener workflow >> %LOGFILE%

REM Run get_artists.py (logging handled by script)
echo %DATE% %TIME% - Running get_artists.py >> %LOGFILE%
python src\get_artists.py --no-prompt --log get_artists.log
if errorlevel 1 (
    echo %DATE% %TIME% - ERROR: get_artists.py failed with exit code %ERRORLEVEL% >> %LOGFILE%
    exit /b %ERRORLEVEL%
)

REM Run scrape.py (logging handled by script)
echo %DATE% %TIME% - Running scrape.py >> %LOGFILE%
python src\scrape.py --no-prompt --log scrape.log
if errorlevel 1 (
    echo %DATE% %TIME% - ERROR: scrape.py failed with exit code %ERRORLEVEL% >> %LOGFILE%
    exit /b %ERRORLEVEL%
)

echo %DATE% %TIME% - Monthly listener workflow completed >> %LOGFILE%