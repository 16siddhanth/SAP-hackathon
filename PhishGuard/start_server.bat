@echo off
echo =====================================================
echo        PhishGuard API Server Startup Script
echo =====================================================
echo.
echo This script will:
echo  1. Install required Python packages
echo  2. Start the Flask API server on port 5000
echo  3. Provide instructions for loading the extension
echo.
echo Make sure Chrome is installed on your system.
echo.
echo Press any key to continue or Ctrl+C to cancel
pause > nul
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    goto end
)

:: Install required packages
echo [STEP 1] Installing required Python packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some packages may not have installed correctly.
    echo You may need to install them manually with:
    echo pip install flask flask-cors pandas numpy scikit-learn tldextract requests beautifulsoup4
    echo.
    echo Continuing with server startup...
)
echo [OK] Packages installation completed
echo.

:: Clean up pycache directories
echo [STEP 2] Cleaning up __pycache__ directories...
if exist __pycache__ (
    rmdir /s /q __pycache__
    echo [OK] Removed __pycache__ directory
) else (
    echo [OK] No __pycache__ directory found
)
echo.

:: Start the Flask server
echo [STEP 3] Starting Flask API server...
echo.
echo IMPORTANT: Keep this window open while using the extension
echo.
echo =====================================================
echo        EXTENSION LOADING INSTRUCTIONS
echo =====================================================
echo.
echo After the server starts, load the extension in Chrome:
echo 1. Open Chrome and go to chrome://extensions/
echo 2. Enable "Developer mode" (toggle in top-right)
echo 3. Click "Load unpacked"
echo 4. Navigate to the PhishGuard folder
echo 5. Select this folder to load the extension
echo.
echo For detailed setup instructions, see SETUP_GUIDE.md
echo.
echo =====================================================
echo        STARTING SERVER...
echo =====================================================
echo.

:: Start server
python app.py

:end
pause
