@echo off
REM ============================================================
REM DrusaBoT - Complete Stack Startup Script
REM Starts Lavalink server, then the Discord bot (with dashboard)
REM ============================================================

cd /d "%~dp0"

echo [DrusaBoT] Starting complete stack...
echo [DrusaBoT] Working directory: %CD%

REM ------------------------------------------------------------
REM 1. Start Lavalink server
REM ------------------------------------------------------------
echo.
echo [DrusaBoT] Starting Lavalink on port 12333...
cd lavalink
start "DrusaBoT - Lavalink" /B run_lavalink.bat
cd ..

REM Give Lavalink time to start
timeout /t 5 /nobreak >nul

REM ------------------------------------------------------------
REM 2. Start Discord Bot (includes Dashboard on port 18080)
REM ------------------------------------------------------------
echo.
echo [DrusaBoT] Starting Discord Bot with Dashboard on port 18080...
start "DrusaBoT - Bot" cmd /C "call .venv\Scripts\activate.bat && python -m bot.main"

echo.
echo [DrusaBoT] All services starting...
echo [DrusaBoT] Dashboard: http://localhost:18080
echo [DrusaBoT] Lavalink:  http://localhost:12333
echo [DrusaBoT] Health:    http://localhost:18080/api/health
echo.
echo [DrusaBoT] Press Ctrl+C in the Lavalink/Bot windows to stop services
pause