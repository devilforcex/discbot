@echo off
REM ============================================================
REM  DiscBot — First-time Windows setup
REM  ------------------------------------------------------------
REM  Installs everything next to this script (i.e. in the repo root).
REM  By convention for this install that is E:\discbot — everything
REM  (.venv, Lavalink.jar, .env, data/, logs/) stays there.
REM
REM  Steps:
REM    1. Check for Python 3.12+ and Java 17+
REM    2. Create virtual environment (.venv) and pip-install deps
REM    3. Create .env from .env.example (if missing)
REM    4. Create application.yml from example
REM    5. Download latest Lavalink.jar (if missing)
REM    6. Open .env in Notepad for editing
REM ============================================================
setlocal enabledelayedexpansion
chcp 65001 >nul
title DiscBot — First-time Setup

echo.
echo  ==========================================
echo   🎵 DiscBot — Windows Setup
echo  ==========================================
echo.

REM ---------- Resolve repo root ----------
REM Hard requirement: everything runs only from E:\discbot.
if /I not "%CD%"=="E:\discbot" (
    cd /d "E:\discbot" 2>nul
)
if errorlevel 1 (
    echo  ❌ E:\discbot does not exist or is not accessible.
    echo     Run install.ps1 first, or create E:\discbot and clone the repo there.
    pause
    exit /b 1
)
echo     Working in: %CD%
echo.

REM ---------- 1. Python check ----------
echo [1/6] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo  ❌ Python was not found.
        echo     Install Python 3.12+ from https://www.python.org/downloads/
        echo     Make sure to tick "Add Python to PATH" during install.
        echo.
        pause
        exit /b 1
    )
    set "PY=py"
) else (
    set "PY=python"
)

REM Python version check
for /f "tokens=1,2 delims=." %%a in ('%PY% -c "import sys;print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2^>nul') do (
    set "PYMAJ=%%a"
    set "PYMIN=%%b"
)
if not defined PYMAJ (
    echo  ❌ Could not detect Python version.
    pause
    exit /b 1
)
if not "%PYMAJ%"=="3" (
    echo  ❌ Python 3 is required (found %PYMAJ%.%PYMIN%).
    pause
    exit /b 1
)
if %PYMIN% LSS 12 (
    echo  ❌ Python 3.12+ is required (found 3.%PYMIN%).
    pause
    exit /b 1
)
echo       Found Python %PYMAJ%.%PYMIN% — OK.

REM ---------- 2. Java check ----------
echo [2/6] Checking Java...
where java >nul 2>&1
if errorlevel 1 (
    echo  ❌ Java was not found.
    echo     Install Java 17+ (JRE) from https://adoptium.net/
    echo     Make sure to tick "Set JAVA_HOME variable" / "Add to PATH".
    echo.
    pause
    exit /b 1
)
for /f tokens^=2-5^ delims^=.-_+^" %%a in ('java -version 2^>^&1 ^| findstr /i "version"') do (
    set "JAVAVER=%%a"
)
if not defined JAVAVER (
    echo  ❌ Could not detect Java version.
    pause
    exit /b 1
)
if %JAVAVER% LSS 17 (
    echo  ⚠️  Java 17+ is recommended (found %JAVAVER%). Lavalink v4 may not start.
    echo     Continuing anyway — press Ctrl+C now to abort, or:
    pause
) else (
    echo       Found Java %JAVAVER% — OK.
)

REM ---------- 3. Virtual env + pip ----------
echo [3/6] Setting up Python virtual environment (.venv^)...
if not exist ".venv\Scripts\python.exe" (
    %PY% -m venv .venv
    if errorlevel 1 (
        echo  ❌ Failed to create virtual environment.
        pause
        exit /b 1
    )
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
echo       Installing requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo  ❌ pip install failed. Check your internet connection.
    pause
    exit /b 1
)

REM ---------- 4. .env ----------
echo [4/6] Setting up .env...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo       ✅ Created .env from .env.example
    echo       ⚠️  Now open .env in Notepad and fill in your DISCORD_BOT_TOKEN,
    echo          GUILD_ID, MUSIC_CHANNEL_ID, OWNER_ID.
) else (
    echo       .env already exists — skipping.
)

REM ---------- 5. application.yml ----------
echo [5/6] Setting up Lavalink config...
if not exist "application.yml" (
    copy "application.yml.example" "application.yml" >nul
    echo       ✅ Created application.yml
) else (
    echo       application.yml already exists — skipping.
)

REM ---------- 6. Download Lavalink ----------
echo [6/6] Lavalink.jar...
if exist "Lavalink.jar" (
    echo       Lavalink.jar already present — skipping download.
) else (
    echo       Downloading Lavalink v4 (this may take a minute)...
    where curl >nul 2>&1
    if errorlevel 1 (
        echo  ❌ curl not found. Please download Lavalink v4 manually from:
        echo     https://github.com/lavalink-devs/Lavalink/releases
        echo     Place Lavalink.jar in %CD%
    ) else (
        curl -L -o Lavalink.jar "https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar"
        if errorlevel 1 (
            echo  ❌ Download failed. Grab it manually from
            echo     https://github.com/lavalink-devs/Lavalink/releases
            echo     and place it in %CD%
        ) else (
            echo       ✅ Downloaded Lavalink.jar
        )
    )
)

echo.
echo  ==========================================
echo   ✅ Setup complete!
echo  ==========================================
echo.
echo     Location : %CD%
echo.
echo  Next steps:
echo    1. Edit .env (fill in your bot token + IDs)
echo    2. Double-click start.bat to run Lavalink + the bot
echo.
echo  Opening .env in Notepad for you...
timeout /t 2 >nul
start notepad .env

pause
endlocal
exit /b 0
