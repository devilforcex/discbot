@echo off
REM ============================================================
REM DiscBot - Complete Stack Shutdown Script
REM Stops Lavalink server and Discord bot
REM ============================================================

cd /d "%~dp0"

echo [DiscBot] Stopping all services...

REM Stop Python processes (bot)
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq DiscBot - Bot*" 2>nul
if %errorlevel% equ 0 (
    echo [DiscBot] Stopped Discord Bot
) else (
    echo [DiscBot] Bot process not found (may already be stopped)
)

REM Stop Java processes (Lavalink)
taskkill /F /FI "IMAGENAME eq java.exe" /FI "WINDOWTITLE eq DiscBot - Lavalink*" 2>nul
if %errorlevel% equ 0 (
    echo [DiscBot] Stopped Lavalink
) else (
    echo [DiscBot] Lavalink process not found (may already be stopped)
)

echo.
echo [DiscBot] All services stopped
pause