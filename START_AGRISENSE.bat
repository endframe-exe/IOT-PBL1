@echo off
title AgriSense Smart Irrigation Controller Launcher
cd /d "%~dp0"

echo =====================================================================
echo    AgriSense: Smart Irrigation Monitoring System Launcher
echo    DEC0101 / DEC0151 Digital Electronics & IoT Systems (Group 11)
echo =====================================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10+ is not found in system PATH!
    echo Please install Python 3.10 or higher from https://python.org and add it to PATH.
    pause
    exit /b 1
)

:: 2. Check or Create Virtual Environment (.venv)
if not exist ".venv\Scripts\activate.bat" (
    echo [INFO] Virtual environment (.venv) not found. Bootstrapping isolated environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [INFO] Installing required dependencies from requirements.txt...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
) else (
    call .venv\Scripts\activate.bat
)

echo.
echo [INFO] Virtual environment active.
echo [INFO] Opening AgriSense Dashboard at http://localhost:8501 ...
echo.

:: 3. Open browser
start "" http://localhost:8501

:: 4. Run Streamlit Application
streamlit run app.py --server.port 8501 --server.headless false

pause
