@echo off
REM ============================================================
REM  DiscBot — Update (Windows)
REM  ------------------------------------------------------------
REM  Pulls latest code from git, refreshes pip dependencies in
REM  .venv, and reminds you to restart the bot. Everything stays
REM  inside the repo folder (default E:\discbot if installed there).
REM ============================================================
setlocal
chcp 65001 >nul
title DiscBot — Update

if defined DISCBOT_DIR (
    cd /d "%DISCBOT_DIR%"
) else (
    cd /d "%~dp0..\.."
)

echo  ⬆️  Updating DiscBot in %CD%
echo.

where git >nul 2>&1
if errorlevel 1 (
    echo  ❌ git not found. Install Git for Windows: https://git-scm.com/
    pause
    exit /b 1
)

REM Make sure we don't clobber local changes
git diff --quiet
if errorlevel 1 (
    echo  ⚠️  You have local uncommitted changes. Commit/stash them first,
    echo     or delete the repo and re-run install.ps1 if you want a clean update.
    pause
    exit /b 1
)

echo  Pulling latest code...
git pull --ff-only
if errorlevel 1 (
    echo  ❌ git pull failed.
    pause
    exit /b 1
)

if exist ".venv\Scripts\python.exe" (
    echo  Refreshing dependencies...
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt --upgrade
) else (
    echo  ⚠️  .venv not found — skipping pip refresh (run setup.bat first).
)

echo.
echo  ✅ Update complete. Stop and re-run start.bat to apply changes.
pause
endlocal
exit /b 0
