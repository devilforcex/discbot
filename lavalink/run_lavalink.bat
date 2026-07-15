@echo off
cd /d "%~dp0"
title DiscBot — Lavalink
echo [DiscBot] Starting Lavalink from %CD%
echo [DiscBot] Port: 12333 ^| Plugins: ./plugins/ ^| Cookies: ./ytcookies.txt
java -jar Lavalink.jar
