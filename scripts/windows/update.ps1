#Requires -Version 5.1
<#
.SYNOPSIS
    One-line DiscBot updater for Windows (PowerShell).

.DESCRIPTION
    Pulls the latest code into the DiscBot install folder (default E:\discbot),
    refreshes pip dependencies in .venv, and (optionally) restarts the running
    bot. Safe: refuses to update if you have uncommitted local changes.

.PARAMETER InstallDir
    Where DiscBot lives. Priority:
      1. -InstallDir parameter
      2. $env:DISCBOT_DIR
      3. the folder this script lives in (if inside a clone)
      4. E:\discbot
      If the folder doesn't exist, delegates to install.ps1.

.PARAMETER Branch
    Git branch to update to. Defaults to the currently checked-out branch.

.PARAMETER PullOnly
    Only update the source; do not restart anything.

.PARAMETER Restart
    After update, stop the bot, refresh deps, then start it again.

.PARAMETER NoPrompt
    Non-interactive mode.

.EXAMPLE
    # One-liner (updates E:\discbot by default):
    irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/update.ps1 | iex

    # Custom dir:
    $env:DISCBOT_DIR='E:\discbot'; irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/update.ps1 | iex
#>
[CmdletBinding()]
param(
    [string]$InstallDir = "",
    [string]$Branch     = "",
    [switch]$PullOnly,
    [switch]$Restart,
    [switch]$NoPrompt
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "DiscBot — Updater"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    OK  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    !   $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "    X   $msg" -ForegroundColor Red; exit 1 }

function Request-Confirm($question, $defaultY = $true) {
    if ($NoPrompt) { return $defaultY }
    $opts = if ($defaultY) { "[Y/n]" } else { "[y/N]" }
    $ans  = Read-Host "$question $opts"
    if (-not $ans) { return $defaultY }
    return $ans -match '^(?i:y|yes|д|да)$'
}

# Resolve install dir — same precedence as install.ps1
$defaultDir = "E:\discbot"
if (-not $InstallDir) {
    if ($env:DISCBOT_DIR) { $InstallDir = $env:DISCBOT_DIR }
    else {
        try {
            $hereRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..") -ErrorAction Stop
            if (Test-Path (Join-Path $hereRoot.Path ".git")) { $InstallDir = $hereRoot.Path }
        } catch {}
        if (-not $InstallDir) { $InstallDir = $defaultDir }
    }
}
$InstallDir = [IO.Path]::GetFullPath($InstallDir)

Write-Host ""
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "  DiscBot — Windows updater" -ForegroundColor Magenta
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "  Folder: $InstallDir"
Write-Host ""

# If the folder doesn't exist (or has no .git), hand off to install.ps1
if (-not (Test-Path $InstallDir) -or -not (Test-Path (Join-Path $InstallDir ".git"))) {
    Write-Warn "No DiscBot installation found at '$InstallDir'."
    if (Request-Confirm "Run the installer for '$InstallDir' now?" $true) {
        # Fetch install.ps1 from the same source this script came from, or use a local copy
        $localInstall = Join-Path $PSScriptRoot "install.ps1"
        if (Test-Path $localInstall) {
            & $localInstall -InstallDir $InstallDir -Branch $(if($Branch){$Branch}else{"master"}) -NoStart:(-not $Restart) -NoPrompt:$NoPrompt
            return
        }
        Invoke-Expression ((New-Object Net.WebClient).DownloadString(
            'https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/install.ps1'))
        return
    } else {
        Write-Fail "Nothing to update."
    }
}

Push-Location $InstallDir

# ---------- Git sanity ----------
Write-Step "Checking Git status"
$status = git status --porcelain
if ($status) {
    Write-Host $status
    Write-Fail "You have local changes. Commit/stash them, or delete $InstallDir and re-run install.ps1."
}

if (-not $Branch) {
    $Branch = (git branch --show-current).Trim()
}
Write-Ok "branch = $Branch"

# ---------- Pull ----------
Write-Step "Pulling latest commits"
git fetch --prune origin
$oldRev = (git rev-parse HEAD).Substring(0,7)

git merge --ff-only "origin/$Branch"
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Fast-forward failed (diverged history). Trying 'git pull --rebase'..."
    git pull --rebase origin $Branch
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Update failed. Resolve manually in '$InstallDir'."
    }
}
$newRev = (git rev-parse HEAD).Substring(0,7)
if ($oldRev -eq $newRev) {
    Write-Ok "Already up to date ($newRev)"
} else {
    Write-Ok "Updated $oldRev -> $newRev"
}

if ($PullOnly) {
    Write-Host "`n✅ Source updated (pull-only)." -ForegroundColor Green
    Pop-Location; return
}

# ---------- Refresh deps ----------
$venvPy = Join-Path $InstallDir ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
    Write-Step "Refreshing Python dependencies"
    & $venvPy -m pip install --upgrade pip --quiet
    & $venvPy -m pip install -r (Join-Path $InstallDir "requirements.txt") --upgrade
    if ($LASTEXITCODE -ne 0) { Write-Warn "pip reported errors; check above." }
    else { Write-Ok "dependencies up to date" }
} else {
    Write-Warn ".venv not found — skipping pip refresh (run install.ps1 if you need to reinstall)."
}

# ---------- application.yml / .env guards ----------
if (-not (Test-Path (Join-Path $InstallDir ".env"))) {
    Write-Warn ".env is missing — copying from .env.example. Please edit it before the bot can start."
    Copy-Item (Join-Path $InstallDir ".env.example") (Join-Path $InstallDir ".env")
}
if (-not (Test-Path (Join-Path $InstallDir "application.yml"))) {
    Copy-Item (Join-Path $InstallDir "application.yml.example") (Join-Path $InstallDir "application.yml")
}

# ---------- Restart ----------
if (-not $Restart) {
    $Restart = Request-Confirm "Stop and restart the running bot now?" $true
}
if ($Restart) {
    $stop  = Join-Path $PSScriptRoot "stop.ps1"
    $start = Join-Path $PSScriptRoot "start.ps1"
    if (Test-Path $stop) {
        Write-Step "Stopping running processes"
        & $stop
        Start-Sleep -Seconds 2
    }
    if (Test-Path $start) {
        Write-Step "Starting bot again"
        & $start -InstallDir $InstallDir
    } else {
        Write-Warn "start.ps1 not found — please start the bot manually."
    }
}

Write-Host "`n✅ Done. Install dir: $InstallDir" -ForegroundColor Green
Pop-Location
