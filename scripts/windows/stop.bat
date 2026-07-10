@echo off
REM ============================================================
REM  DiscBot — Stop Lavalink + Bot
REM  ------------------------------------------------------------
REM  Kills any java.exe whose command line contains Lavalink.jar
REM  and any python.exe running bot\main.py.
REM ============================================================
setlocal
chcp 65001 >nul
title DiscBot — Stop

echo  🛑 Stopping DiscBot...
echo.

if defined DISCBOT_DIR (
    cd /d "%DISCBOT_DIR%"
) else (
    cd /d "%~dp0..\.."
)

REM Kill Lavalink
wmic process where "commandline like '%%Lavalink.jar%%'" call terminate >nul 2>&1

REM Kill bot (python running bot\main.py under .venv)
wmic process where "commandline like '%%bot\\main.py%%'" call terminate >nul 2>&1

echo  ✅ Stop commands issued. If windows are still open, close them manually.
timeout /t 3 >nul
endlocal
exit /b 0
