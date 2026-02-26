@echo off
title Build PhotoFit Studio
cd /d "%~dp0"

:: ============================================
:: Build PhotoFit Studio to .exe - OPTIMIZED VERSION
:: ============================================

:: ============================================
:: VERSION CONFIGURATION
:: Change version in version.txt file to update
:: ============================================

:: Read version from version.txt file
set /p VERSION=<version.txt
if "%VERSION%"=="" set "VERSION=1.0.0"

set "APP_NAME=PhotoFitStudio"

echo ============================================
echo  PhotoFit Studio v%VERSION% - BUILD TOOL
echo ============================================
echo.

:: Check Python
py -3 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

:: Install PyInstaller if not exists
py -3 -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing PyInstaller...
    py -3 -m pip install pyinstaller --quiet
)

echo [1/4] Preparing build environment...
echo.
echo Current version: %VERSION%
echo.

:: Clean only build folder (keep dist for version comparison)
if exist "build" rmdir /S /Q build
if exist "__pycache__" rmdir /S /Q __pycache__
echo [OK] Build folder cleaned.

echo.
echo [2/4] Building .exe (this may take a few minutes)...
echo.

:: ============================================
:: OPTIMIZED BUILD COMMAND
:: - Use --hidden-import instead of --collect-all for large packages
:: - Only use --collect-all for small, commonly used packages
:: - This reduces build time significantly
:: ============================================

py -3 -m PyInstaller --onefile --windowed --name "%APP_NAME%_v%VERSION%" main.py --clean ^
--add-data "models;models" ^
--add-data "templates;templates" ^
--add-data "config.json;." ^
--add-data "docs;docs" ^
--collect-all=mediapipe ^
--collect-all=rembg ^
--collect-all=PIL ^
--collect-all=cv2 ^
--collect-all=numpy ^
--hidden-import=scipy ^
--hidden-import=scipy.ndimage ^
--hidden-import=scipy.special ^
--hidden-import=scipy.linalg ^
--hidden-import=skimage ^
--hidden-import=skimage.morphology ^
--hidden-import=skimage.filters ^
--hidden-import=skimage.segmentation ^
--hidden-import=skimage.restoration ^
--hidden-import=pymatting ^
--hidden-import=pymatting.estimate ^
--hidden-import=pymatting.util

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [3/4] Processing output files...
echo.

:: Check if file already exists in dist
set "OLD_EXE=dist\%APP_NAME%.exe"
set "NEW_EXE=dist\%APP_NAME%_v%VERSION%.exe"

:: If same version exists, ask to overwrite
if exist "%NEW_EXE%" (
    echo [INFO] Version %VERSION% already exists.
    echo Overwriting existing file...
    del /F /Q "%NEW_EXE%" 2>nul
)

:: Also delete old version without version suffix if exists
if exist "%OLD_EXE%" (
    echo [INFO] Removing old version (no version suffix)...
    del /F /Q "%OLD_EXE%" 2>nul
)

:: Copy new exe to standard name (without version for easy access)
copy /Y "dist\%APP_NAME%_v%VERSION%.exe" "dist\%APP_NAME%.exe" >nul

echo.
echo [4/4] Build complete!
echo.

:: Show output
echo ============================================
echo  BUILD SUCCESSFUL!
echo ============================================
echo.
echo Version: %VERSION%
echo Output 1: dist\%APP_NAME%_v%VERSION%.exe
echo Output 2: dist\%APP_NAME%.exe ^(latest^)
echo.
echo Press any key to open output folder...
pause >nul

:: Open output folder
start explorer dist

exit /b 0
