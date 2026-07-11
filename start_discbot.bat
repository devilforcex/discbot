@echo off
echo Starting DiscBot...

REM Start Lavalink server
cd /d e:\discbot\lavalink
start "Lavalink" java -jar Lavalink.jar
echo Lavalink started on port 12333

REM Wait for Lavalink to be ready
timeout /t 5 /nobreak >nul

REM Start the bot
cd /d e:\discbot
python -m bot.main