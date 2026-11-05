@echo off
title Survey Hunter - local site
cd /d "%~dp0"
start "Survey Hunter local server (keep this window open)" cmd /k python -m http.server 8000
timeout /t 1 /nobreak >nul
start "" http://localhost:8000
echo Site running at http://localhost:8000
echo Close the server window to stop it.
timeout /t 5 >nul
exit
