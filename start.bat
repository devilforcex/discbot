@echo off
cd /d e:\discbot\lavalink

REM Kill any existing processes
taskkill /f /im java.exe 2>nul
taskkill /f /im python.exe 2>nul

REM Start Lavalink in background
echo Започване на Lavalink сървъра...
start /B java -jar Lavalink.jar > lavalink.log 2>&1

REM Wait for Lavalink to start
timeout /t 10 /nobreak >nul

REM Start the bot
echo Стартиране на Discord бота...
cd /d e:\discbot
python -m bot.main

exit