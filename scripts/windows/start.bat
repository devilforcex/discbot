@echo off
REM ============================================================
REM  DiscBot — Start Lavalink + Discord Bot
REM  ------------------------------------------------------------
REM  By default runs from the repo root (i.e. E:\discbot if you
REM  installed there). Override with the DISCBOT_DIR env var.
REM  Opens two console windows: one for Lavalink, one for the bot.
REM ============================================================
setlocal
chcp 65001 >nul
title DiscBot Launcher

if defined DISCBOT_DIR (
    cd /d "%DISCBOT_DIR%"
) else (
    cd /d "%~dp0..\.."
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
start "DiscBot — Bot" cmd /k "cd /d ""%CD%"" && .venv\Scripts\activate.bat && python bot\main.py"

echo.
echo  ✅ Both processes launched in separate windows.
echo     Close the windows (or run stop.bat) to shut them down.
echo.
endlocal
exit /b 0
