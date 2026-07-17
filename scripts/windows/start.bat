@echo off
REM ============================================================
REM  DrusaBoT — Start Lavalink + Discord Bot
REM  ------------------------------------------------------------
REM  Runs only from E:\DrusaBoT. All bot files/config/data/logs live there.
REM  Lavalink runs from lavalink/ subdirectory with application.yml and plugins.
REM  Opens two console windows: one for Lavalink, one for the bot.
REM ============================================================
setlocal
chcp 65001 >nul
title DrusaBoT Launcher

cd /d "E:\DrusaBoT" 2>nul
if errorlevel 1 (
    echo  ❌ E:\DrusaBoT does not exist or is not accessible. Run install.ps1 first.
    pause
    exit /b 1
)

echo  🎵 DrusaBoT @ %CD%
echo.

if not exist ".env" (
    echo  ❌ .env not found. Run setup.bat first.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo  ❌ .venv not found. Run setup.bat first.
    pause
    exit /b 1
)
if not exist "lavalink\Lavalink.jar" (
    echo  ❌ Lavalink.jar not found in lavalink\. Run install.ps1 to download it.
    pause
    exit /b 1
)

echo  Starting Lavalink (new window)...
start "DrusaBoT — Lavalink" cmd /k "cd /d ""%CD%\lavalink"" && java -jar Lavalink.jar"

echo  Waiting for Lavalink to boot...
timeout /t 8 /nobreak >nul

echo  Starting bot (new window)...
start "DrusaBoT — Bot" cmd /k "cd /d ""%CD%"" && .venv\Scripts\python.exe -m bot.main"

echo.
echo  ✅ Both processes launched in separate windows.
echo     Close the windows (or run stop.bat) to shut them down.
echo.
endlocal
exit /b 0