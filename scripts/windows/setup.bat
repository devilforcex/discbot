@echo off
REM ============================================================
REM  DrusaBoT — First-time Windows setup
REM  ------------------------------------------------------------
REM  Installs everything in E:\DrusaBoT — everything
REM  (.venv, lavalink\Lavalink.jar, .env, data/, logs/) stays there.
REM  Lavalink runs from lavalink/ subdirectory with application.yml and plugins.
REM
REM  Steps:
REM    1. Check for Python 3.12+ and Java 17+
REM    2. Create virtual environment (.venv) and pip-install deps
REM    3. Create .env from .env.example (if missing)
REM    4. Create application.yml in lavalink/ from example
REM    5. Download latest Lavalink.jar to lavalink/ (if missing)
REM    6. Download youtube-plugin to lavalink/plugins/ (if missing)
REM    7. Open .env in Notepad for editing
REM ============================================================
setlocal enabledelayedexpansion
chcp 65001 >nul
title DrusaBoT — First-time Setup

echo.
echo  ==========================================
echo   🎵 DrusaBoT — Windows Setup
echo  ==========================================
echo.

REM ---------- Resolve repo root ----------
REM Hard requirement: everything runs only from E:\DrusaBoT.
if /I not "%CD%"=="E:\DrusaBoT" (
    cd /d "E:\DrusaBoT" 2>nul
)
if errorlevel 1 (
    echo  ❌ E:\DrusaBoT does not exist or is not accessible.
    echo     Run install.ps1 first, or create E:\DrusaBoT and clone the repo there.
    pause
    exit /b 1
)
echo     Working in: %CD%
echo.

REM ---------- 1. Python check ----------
echo [1/7] Checking Python...
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
echo [2/7] Checking Java...
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
echo [3/7] Setting up Python virtual environment (.venv^)...
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
echo [4/7] Setting up .env...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo       ✅ Created .env from .env.example
    echo       ⚠️  Now open .env in Notepad and fill in your DISCORD_BOT_TOKEN,
    echo          GUILD_ID, MUSIC_CHANNEL_ID, OWNER_ID.
) else (
    echo       .env already exists — skipping.
)

REM ---------- 5. lavalink directory ----------
echo [5/7] Creating lavalink directory structure...
if not exist "lavalink" mkdir lavalink
if not exist "lavalink\plugins" mkdir lavalink\plugins
echo       ✅ Created lavalink/ and lavalink/plugins/ directories

REM ---------- 6. application.yml ----------
echo [6/7] Setting up Lavalink config...
if not exist "lavalink\application.yml" (
    copy "application.yml.example" "lavalink\application.yml" >nul
    echo       ✅ Created lavalink\application.yml
) else (
    echo       lavalink\application.yml already exists — skipping.
)

REM ---------- 7. Download Lavalink and YouTube plugin ----------
echo [7/7] Downloading Lavalink and YouTube plugin...

REM Download Lavalink.jar
if exist "lavalink\Lavalink.jar" (
    echo       Lavalink.jar already present — skipping download.
) else (
    echo       Downloading Lavalink v4 (this may take a minute)...
    where curl >nul 2>&1
    if errorlevel 1 (
        echo  ❌ curl not found. Please download Lavalink v4 manually from:
        echo     https://github.com/lavalink-devs/Lavalink/releases
        echo     Place Lavalink.jar in %CD%\lavalink\
    ) else (
        curl -L -o lavalink\Lavalink.jar "https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar"
        if errorlevel 1 (
            echo  ❌ Download failed. Grab it manually from
            echo     https://github.com/lavalink-devs/Lavalink/releases
            echo     and place it in %CD%\lavalink\
        ) else (
            echo       ✅ Downloaded Lavalink.jar to lavalink\
        )
    )
)

REM Download YouTube plugin
if exist "lavalink\plugins\youtube-plugin-1.18.0.jar" (
    echo       youtube-plugin already present — skipping download.
) else (
    echo       Downloading youtube-plugin v1.18.0...
    where curl >nul 2>&1
    if errorlevel 1 (
        echo  ❌ curl not found. Please download youtube-plugin manually from:
        echo     https://github.com/lavalink-devs/youtube-source/releases
        echo     Place youtube-plugin-1.18.0.jar in %CD%\lavalink\plugins\
    ) else (
        curl -L -o lavalink\plugins\youtube-plugin-1.18.0.jar "https://github.com/lavalink-devs/youtube-source/releases/download/1.18.0/youtube-plugin-1.18.0.jar"
        if errorlevel 1 (
            echo  ❌ Download failed. Grab it manually from
            echo     https://github.com/lavalink-devs/youtube-source/releases
            echo     and place it in %CD%\lavalink\plugins\
        ) else (
            echo       ✅ Downloaded youtube-plugin to lavalink\plugins\
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
echo   1. Edit .env (fill in your bot token + IDs)
echo   2. Double-click start.bat to run Lavalink + the bot
echo.
echo  Opening .env in Notepad for you...
timeout /t 2 >nul
start notepad .env

pause
endlocal
exit /b 0