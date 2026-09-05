@echo off
title GST Reconciler
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install dependencies if pandas is missing (first run)
python -c "import pandas, openpyxl, tkinterdnd2" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies, please wait...
    pip install -r requirements.txt
)

echo Starting GST Reconciler...
python run.py

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
