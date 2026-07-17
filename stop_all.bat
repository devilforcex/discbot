@echo off
REM ============================================================
REM DrusaBoT - Complete Stack Shutdown Script
REM Stops Lavalink server and Discord bot
REM ============================================================

cd /d "%~dp0"

echo [DrusaBoT] Stopping all services...

REM Stop Python processes (bot)
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq DrusaBoT - Bot*" 2>nul
if %errorlevel% equ 0 (
    echo [DrusaBoT] Stopped Discord Bot
) else (
    echo [DrusaBoT] Bot process not found (may already be stopped)
)

REM Stop Java processes (Lavalink)
taskkill /F /FI "IMAGENAME eq java.exe" /FI "WINDOWTITLE eq DrusaBoT - Lavalink*" 2>nul
if %errorlevel% equ 0 (
    echo [DrusaBoT] Stopped Lavalink
) else (
    echo [DrusaBoT] Lavalink process not found (may already be stopped)
)

echo.
echo [DrusaBoT] All services stopped
pause