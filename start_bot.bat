@echo off
REM ============================================================
REM DiscBot - Discord Bot Start Script (includes Dashboard)
REM Requires Lavalink running on port 12333
REM ============================================================

cd /d "%~dp0"

echo [DiscBot] Starting Discord Bot...
echo [DiscBot] Dashboard will be available at http://localhost:18080
echo [DiscBot] Make sure Lavalink is running on port 12333
echo.

call .venv\Scripts\activate.bat
python -m bot.main

pause