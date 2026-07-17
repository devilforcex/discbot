@echo off
REM ============================================================
REM DrusaBoT - Discord Bot Start Script (includes Dashboard)
REM Requires Lavalink running on port 12333
REM ============================================================

cd /d "%~dp0"

echo [DrusaBoT] Starting Discord Bot...
echo [DrusaBoT] Dashboard will be available at http://localhost:18080
echo [DrusaBoT] Make sure Lavalink is running on port 12333
echo.

call .venv\Scripts\activate.bat
python -m bot.main

pause