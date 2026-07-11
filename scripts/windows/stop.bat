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

cd /d "E:\discbot" 2>nul
if errorlevel 1 (
    echo  ⚠️  E:\discbot does not exist or is not accessible. Will still try to stop matching processes.
)

REM Kill Lavalink launched from E:\discbot
wmic process where "commandline like '%%E:\\discbot%%' and commandline like '%%Lavalink.jar%%'" call terminate >nul 2>&1

REM Kill bot (python running -m bot.main or bot\main.py under E:\discbot)
wmic process where "commandline like '%%E:\\discbot%%' and commandline like '%%bot.main%%'" call terminate >nul 2>&1
wmic process where "commandline like '%%E:\\discbot%%' and commandline like '%%bot\\main.py%%'" call terminate >nul 2>&1

echo  ✅ Stop commands issued. If windows are still open, close them manually.
timeout /t 3 >nul
endlocal
exit /b 0
