@echo off
title Survey Hunter - daily check
cd /d "%~dp0"
wscript "run-listener.vbs" 2>nul
echo ============================================
echo   Survey Hunter -today check + classification
echo ============================================
echo.
python main.py %*
if "%1"=="--auto" exit /b
echo.
echo Done! Snapshot saved to data\surveys.json
echo Double-click open-site.bat to view the site locally.
echo.
pause
