@echo off
REM ============================================================
REM Dashboard Standalone Start Script (if not running via bot)
REM Note: Dashboard is automatically started by the bot when DASHBOARD_ENABLED=true
REM ============================================================

cd /d "%~dp0"

echo [Dashboard] Starting standalone Dashboard server...
echo [Dashboard] Will be available at http://localhost:18080
echo.

call .venv\Scripts\activate.bat
python -m bot.dashboard.dashboard

pause