@echo off
title PhotoFit Studio v1.4
cd /d "%~dp0"

:: ============================================
:: PhotoFit Studio v1.4 - AI Enhancement
:: ============================================

:: Check if Python is available
where py >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Auto-install dependencies if customtkinter is missing (first-run check)
py -c "import customtkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] First run detected - installing dependencies...
    echo This may take a few minutes. Please wait...
    echo.
    py -m pip install -r requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to install dependencies. Please run manually:
        echo   py -m pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo [SETUP] Dependencies installed successfully!
    echo.
)

:: Also check rembg onnxruntime backend
py -c "import onnxruntime" >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] Installing background removal engine...
    py -m pip install "rembg[cpu]" --quiet
)

:: Launch the application
echo ============================================
echo  PhotoFit Studio v1.4
echo  AI Enhancement Enabled
echo ============================================
echo.
py main.py
