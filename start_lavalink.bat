@echo off
REM ============================================================
REM Lavalink Server Start Script
REM Runs on port 12333, requires application.yml in lavalink/
REM ============================================================

cd /d "%~dp0\lavalink"

echo [Lavalink] Starting Lavalink server...
echo [Lavalink] Port: 12333
echo [Lavalink] Config: application.yml
echo [Lavalink] Plugins: ./plugins/
echo [Lavalink] Cookies: ./ytcookies.txt
echo.

java -Xms256m -Xmx1g -XX:+UseG1GC -jar Lavalink.jar

pause