@echo off
REM ============================================================
REM  DiscBot — Start Lavalink + Discord Bot
REM  ------------------------------------------------------------
REM  Runs only from E:\discbot. All bot files/config/data/logs live there.
REM  Opens two console windows: one for Lavalink, one for the bot.
REM ============================================================
setlocal
chcp 65001 >nul
title DiscBot Launcher

cd /d "E:\discbot" 2>nul
if errorlevel 1 (
    echo  ❌ E:\discbot does not exist or is not accessible. Run install.ps1 first.
    pause
    exit /b 1
)

echo  🎵 DiscBot @ %CD%
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
if not exist "Lavalink.jar" (
    echo  ❌ Lavalink.jar not found. Run setup.bat to download it,
    echo     or place Lavalink.jar in %CD%.
    pause
    exit /b 1
)
if not exist "application.yml" (
    copy "application.yml.example" "application.yml" >nul
)

echo  Starting Lavalink (new window)...
start "DiscBot — Lavalink" cmd /k "cd /d ""%CD%"" && java -jar Lavalink.jar"

echo  Waiting for Lavalink to boot...
timeout /t 8 /nobreak >nul

echo  Starting bot (new window)...
start "DiscBot — Bot" cmd /k "cd /d ""%CD%"" && .venv\Scripts\python.exe -m bot.main"

echo.
echo  ✅ Both processes launched in separate windows.
echo     Close the windows (or run stop.bat) to shut them down.
echo.
endlocal
exit /b 0
