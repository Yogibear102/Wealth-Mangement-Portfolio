@echo off
REM Quickstart helper for local development (Windows batch)
REM Usage: quickstart.bat
REM Optionally set FINNHUB_API_KEY in environment to fetch live symbols.

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Wealth Management Website - Quickstart
echo ========================================
echo.

REM Check if venv exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please create it first:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    exit /b 1
)

echo.
echo Installing requirements (if needed)...
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo requirements.txt not found!
    exit /b 1
)

echo.
echo Running database setup (creates demo user and sample data)...
python setup_db.py
if errorlevel 1 (
    echo Database setup failed!
    exit /b 1
)

echo.
echo Updating master assets (uses FINNHUB_API_KEY if set, otherwise defaults)...
python scripts\update_master_assets.py
if errorlevel 1 (
    echo Master assets update failed!
    exit /b 1
)

echo.
echo Starting Flask app at http://127.0.0.1:5000
echo Press CTRL+C to quit
echo.

set FLASK_ENV=development
python app.py

endlocal
