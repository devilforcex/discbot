@echo off
REM DrusaBoT fixed-path installer wrapper.
REM It may be launched from this checkout, but it installs/updates only E:\DrusaBoT.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows\install.ps1"
