#Requires -Version 5.1
<#
.SYNOPSIS
    One-line DiscBot installer for Windows (PowerShell).

.DESCRIPTION
    Installs DiscBot only to the fixed directory E:\discbot. Safe to re-run:
    if the target folder already has a Git clone it updates instead of
    overwriting. Custom install directories are intentionally rejected so all
    bot files, config, venv, logs, data, and Lavalink live in one place.

    Steps:
      - Creates/chdir to the install folder
      - Clones (or verifies) the Git repo
      - Verifies Python 3.12+ and Java 17+ (opens download pages if missing)
      - Creates .venv and pip-installs requirements
      - Creates .env / application.yml from examples
      - Downloads the latest Lavalink.jar and YouTube plugin
      - Optionally starts the bot when done.

.PARAMETER InstallDir
    Backward-compatible parameter. Only E:\discbot is accepted.

.PARAMETER Branch
    Git branch to clone/update. Default: master

.PARAMETER NoStart
    Do not launch the bot after install.

.PARAMETER NoPrompt
    Run non-interactively (won't stop to ask, just prints steps).

.EXAMPLE
    # Default one-liner (installs to E:\discbot):
    irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/install.ps1 | iex

    # Locally (from inside the repo; still installs/updates E:\discbot):
    powershell -ExecutionPolicy Bypass -File .\scripts\windows\install.ps1
#>
[CmdletBinding()]
param(
    [string]$InstallDir = "",
    [string]$Branch     = "master",
    [switch]$NoStart,
    [switch]$NoPrompt
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "DiscBot — Installer"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    OK  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    !   $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "    X   $msg" -ForegroundColor Red; exit 1 }

function Test-Command($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

function Request-Confirm($question, $defaultY = $true) {
    if ($NoPrompt) { return $defaultY }
    $opts = if ($defaultY) { "[Y/n]" } else { "[y/N]" }
    $ans  = Read-Host "$question $opts"
    if (-not $ans) { return $defaultY }
    return $ans -match '^(?i:y|yes|д|да)$'
}

# ---------- Resolve install dir ----------
# Hard requirement: every bot-related file must live under E:\discbot.
$fixedDir = [IO.Path]::GetFullPath("E:\discbot")
if ($InstallDir -and ([IO.Path]::GetFullPath($InstallDir).TrimEnd('\') -ne $fixedDir.TrimEnd('\'))) {
    Write-Fail "DiscBot is locked to E:\discbot. Refusing custom InstallDir: $InstallDir"
}
if ($env:DISCBOT_DIR -and ([IO.Path]::GetFullPath($env:DISCBOT_DIR).TrimEnd('\') -ne $fixedDir.TrimEnd('\'))) {
    Write-Fail "DiscBot is locked to E:\discbot. Remove DISCBOT_DIR or set it to E:\discbot. Current: $env:DISCBOT_DIR"
}
$InstallDir = $fixedDir

Write-Host ""
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "  DiscBot — Windows installer" -ForegroundColor Magenta
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "  Install dir : $InstallDir"
Write-Host "  Branch      : $Branch"
Write-Host ""

# ---------- 1. Create / verify install folder ----------
Write-Step "Preparing install folder"
if (Test-Path $InstallDir) {
    if (Test-Path (Join-Path $InstallDir ".git")) {
        Write-Ok "Folder already contains a Git clone — running update instead of re-installing."
        $update = Join-Path $InstallDir "scripts\windows\update.ps1"
        if (Test-Path $update) {
            # Delegate to the local update.ps1 so any local fixes are honored.
            # -NoStart maps to "don't restart"; -Force is honored via env DISCBOT_FORCE too.
            & $update -InstallDir $InstallDir -Branch $Branch -NoStart:$NoStart -NoPrompt:$NoPrompt
            return
        }
        # Otherwise fall through — continue install (idempotent).
    } else {
        if ((Get-ChildItem $InstallDir -Force -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0) {
            Write-Fail "E:\discbot exists but is not a Git clone. Move/backup its contents, empty the folder, or run setup.bat if this is a manually copied repo."
        }
    }
} else {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}
Write-Ok $InstallDir

# ---------- 2. Git ----------
Write-Step "Checking for Git"
if (-not (Test-Command "git")) {
    Write-Fail "Git is not installed. Install from https://git-scm.com/download/win and re-run."
}
Write-Ok ("git " + (git --version))

# ---------- 3. Clone ----------
$repoUrl = "https://github.com/devilforcex/discbot.git"
if (-not (Test-Path (Join-Path $InstallDir ".git"))) {
    Write-Step "Cloning $repoUrl (branch '$Branch') -> $InstallDir"
    Push-Location (Split-Path $InstallDir -Parent)
    $leaf = Split-Path $InstallDir -Leaf
    git clone --depth 1 --branch $Branch $repoUrl $leaf
    Pop-Location
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Branch '$Branch' not found; falling back to default branch."
        Push-Location (Split-Path $InstallDir -Parent)
        $leaf = Split-Path $InstallDir -Leaf
        git clone --depth 1 $repoUrl $leaf
        Pop-Location
        if ($LASTEXITCODE -ne 0) { Write-Fail "git clone failed." }
    }
    Write-Ok "clone finished"
}
Push-Location $InstallDir

# ---------- 4. Python ----------
Write-Step "Checking Python 3.12+"
$py = $null
foreach ($c in ("py", "python", "python3")) {
    if (Test-Command $c) {
        try {
            $v = & $c -c "import sys;print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
            if ($v -and ($v -match "^3\.(\d+)")) {
                $minor = [int]$Matches[1]
                if ($minor -ge 12) { $py = $c; Write-Ok ("Python $v ($c)"); break }
            }
        } catch {}
    }
}
if (-not $py) {
    Write-Warn "Python 3.12+ was not found."
    if (Request-Confirm "  Open the Python download page in your browser?" $true) {
        Start-Process "https://www.python.org/downloads/"
    }
    Write-Fail "Install Python (tick 'Add Python to PATH'), then re-run this script."
}

# ---------- 5. Java ----------
Write-Step "Checking Java 17+"
$javaOk = $false
if (Test-Command "java") {
    $jline = (java -version 2>&1 | Select-Object -First 1)
    if ($jline -match '"(\d+)(?:\.|\.)') {
        $jv = [int]$Matches[1]
        if ($jv -ge 17) { Write-Ok ("Java $jv — $jline"); $javaOk = $true }
        else { Write-Warn "Java $jv found, but 17+ is needed for Lavalink v4." }
    }
}
if (-not $javaOk) {
    Write-Warn "Java 17+ not found."
    if (Request-Confirm "  Open Adoptium (recommended JRE) download page?" $true) {
        Start-Process "https://adoptium.net/temurin/releases/?version=17&os=windows&arch=x64&package=jre"
    }
    Write-Fail "Install Java and re-run this script. (JRE is enough, JDK is not required.)"
}

# ---------- 6. Virtual env ----------
Write-Step "Creating virtual environment (.venv)"
$venvPy = Join-Path $InstallDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    & $py -m venv .venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPy)) {
        Write-Fail "Failed to create virtual environment."
    }
    Write-Ok ".venv created"
} else {
    Write-Ok ".venv already exists"
}
& $venvPy -m pip install --upgrade pip --quiet

Write-Step "Installing Python dependencies (requirements.txt)"
& $venvPy -m pip install -r (Join-Path $InstallDir "requirements.txt")
if ($LASTEXITCODE -ne 0) { Write-Fail "pip install failed." }
Write-Ok "dependencies installed"

# ---------- 7. .env / application.yml ----------
Write-Step "Setting up configuration files"
$envPath = Join-Path $InstallDir ".env"
if (-not (Test-Path $envPath)) {
    Copy-Item (Join-Path $InstallDir ".env.example") $envPath
    Write-Ok ".env created from .env.example"
} else { Write-Ok ".env already exists — left untouched" }

# ---------- 8. Lavalink ----------
$lavalinkDir = Join-Path $InstallDir "lavalink"
if (-not (Test-Path $lavalinkDir)) {
    New-Item -ItemType Directory -Path $lavalinkDir -Force | Out-Null
}

$lavalinkPluginsDir = Join-Path $lavalinkDir "plugins"
if (-not (Test-Path $lavalinkPluginsDir)) {
    New-Item -ItemType Directory -Path $lavalinkPluginsDir -Force | Out-Null
}

# Copy application.yml to lavalink/ subdirectory
$lavalinkAppYml = Join-Path $lavalinkDir "application.yml"
if (-not (Test-Path $lavalinkAppYml)) {
    Copy-Item (Join-Path $InstallDir "application.yml.example") $lavalinkAppYml
    Write-Ok "lavalink/application.yml created from application.yml.example"
} else { Write-Ok "lavalink/application.yml already exists — left untouched" }

Write-Step "Checking Lavalink.jar"
$ll = Join-Path $lavalinkDir "Lavalink.jar"
if (Test-Path $ll) {
    Write-Ok "Lavalink.jar already present in lavalink/"
} else {
    Write-Host "    Downloading latest Lavalink v4..."
    $llUrl = "https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar"
    try {
        Invoke-WebRequest -Uri $llUrl -OutFile $ll -UseBasicParsing
        Write-Ok "Lavalink.jar downloaded to lavalink/"
    } catch {
        Write-Warn "Auto-download failed: $_"
        Write-Warn "Manually download Lavalink.jar from https://github.com/lavalink-devs/Lavalink/releases and place it in '$lavalinkDir'."
    }
}

Write-Step "Checking YouTube plugin"
$ytPlugin = Join-Path $lavalinkPluginsDir "youtube-plugin-1.18.0.jar"
if (Test-Path $ytPlugin) {
    Write-Ok "youtube-plugin already present in lavalink/plugins/"
} else {
    Write-Host "    Downloading youtube-plugin v1.18.0..."
    $ytPluginUrl = "https://github.com/lavalink-devs/youtube-source/releases/download/1.18.0/youtube-plugin-1.18.0.jar"
    try {
        Invoke-WebRequest -Uri $ytPluginUrl -OutFile $ytPlugin -UseBasicParsing
        Write-Ok "youtube-plugin downloaded to lavalink/plugins/"
    } catch {
        Write-Warn "Auto-download failed: $_"
        Write-Warn "Manually download youtube-plugin-1.18.0.jar from https://github.com/lavalink-devs/youtube-source/releases and place it in '$lavalinkPluginsDir'."
    }
}

Pop-Location

# ---------- 9. Done ----------
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  ✅ Installation complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Location : $InstallDir"
Write-Host ""
Write-Host "  Next:"
Write-Host "   1. Edit    : notepad `"$envPath`""
Write-Host "   2. Start   : powershell -ExecutionPolicy Bypass -File `"$InstallDir\scripts\windows\start.ps1`""
Write-Host "   3. Update  : irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/update.ps1 | iex"
Write-Host ""

if (Test-Path $envPath) {
    if (Request-Confirm "Open .env in Notepad now?" $true) {
        Start-Process notepad.exe $envPath
    }
}

if (-not $NoStart -and (Request-Confirm "Start the bot now?" $false)) {
    $sp = Join-Path $InstallDir "scripts\windows\start.ps1"
    if (Test-Path $sp) {
        & $sp -InstallDir $InstallDir
    } else {
        Write-Warn "start.ps1 not found — run scripts\windows\start.ps1 manually."
    }
}
