@echo off
REM ============================================================
REM  DiscBot — Update (Windows)
REM  ------------------------------------------------------------
REM  Pulls latest code from git, refreshes pip dependencies in
REM  .venv, and reminds you to restart the bot. Everything stays
REM  inside the repo folder (default E:\discbot if installed there).
REM  Ensure lavalink/application.yml exists after update.
REM ============================================================
setlocal
chcp 65001 >nul
title DiscBot — Update

cd /d "E:\discbot" 2>nul
if errorlevel 1 (
    echo  ❌ E:\discbot does not exist or is not accessible. Run install.ps1 first.
    pause
    exit /b 1
)

echo  ⬆️  Updating DiscBot in %CD%
echo.

where git >nul 2>&1
if errorlevel 1 (
    echo  ❌ git not found. Install Git for Windows: https://git-scm.com/
    pause
    exit /b 1
)

REM Only tracked edits block (same policy as update.ps1).
REM Untracked files (generated-page.html, local notes, …) are fine.
git diff --quiet
set TRACKED_DIRTY=0
if errorlevel 1 set TRACKED_DIRTY=1
git diff --cached --quiet
if errorlevel 1 set TRACKED_DIRTY=1

if "%TRACKED_DIRTY%"=="1" (
    echo  ⚠️  Tracked local changes found:
    git status --short --untracked-files=no
    echo.
    if /I "%DISCBOT_FORCE%"=="1" (
        echo  DISCBOT_FORCE=1 — discarding tracked changes (keeps .env / data / untracked)...
        git reset --hard HEAD
        if errorlevel 1 (
            echo  ❌ git reset failed.
            pause
            exit /b 1
        )
    ) else (
        echo  Commit/stash them, set DISCBOT_FORCE=1, or delete the repo and re-run install.ps1.
        echo  PowerShell one-liner force:  set DISCBOT_FORCE=1 ^& irm ...update.ps1 ^| iex
        pause
        exit /b 1
    )
)

echo  Pulling latest code...
git fetch --prune origin
git pull --ff-only
if errorlevel 1 (
    echo  ❌ git pull failed.
    pause
    exit /b 1
)

if exist ".venv\Scripts\python.exe" (
    echo  Refreshing dependencies...
    .venv\Scripts\python.exe -m pip install -r requirements.txt --upgrade
) else (
    echo  ⚠️  .venv not found — skipping pip refresh (run setup.bat first).
)

REM Ensure application.yml exists in lavalink/ subdirectory
if not exist "lavalink\application.yml" (
    if not exist "lavalink" mkdir lavalink
    copy "application.yml.example" "lavalink\application.yml" >nul
    echo  ✅ Ensured lavalink\application.yml exists
) else (
    echo  lavalink\application.yml already exists — skipping.
)

echo.
echo  ✅ Update complete. Stop and re-run start.bat to apply changes.
pause
endlocal
exit /b 0