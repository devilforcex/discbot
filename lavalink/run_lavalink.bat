@echo off
cd /d "%~dp0"
title DrusaBoT — Lavalink
echo [DrusaBoT] Starting Lavalink from %CD%
echo [DrusaBoT] Port: 12333 ^| Plugins: ./plugins/ ^| Cookies: ./ytcookies.txt
java -jar Lavalink.jar
