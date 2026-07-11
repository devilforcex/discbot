@echo off
REM DiscBot fixed-path installer wrapper.
REM It may be launched from this checkout, but it installs/updates only E:\discbot.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows\install.ps1"
