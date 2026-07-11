#Requires -Version 5.1
<#
.SYNOPSIS
    One-line DiscBot updater for Windows (PowerShell).

.DESCRIPTION
    Pulls the latest code into the DiscBot install folder (default E:\discbot),
    refreshes pip dependencies in .venv, and (optionally) restarts the running
    bot.

    Safety model (matches update.sh):
      - Untracked / ignored files (e.g. generated-page.html, .env, data/) never block.
      - Tracked local edits block by default; you can stash, discard, or pass -Force.
      - Never overwrites .env, data/, logs/, or other gitignored runtime files.

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

.PARAMETER NoStart
    Alias used by install.ps1: skip the restart prompt (same as not setting -Restart
    and answering No). Kept for backward compatibility with install.ps1.

.PARAMETER Force
    Discard tracked local modifications/deletions (git reset --hard + clean deleted
    tracked files) before pulling. Untracked and ignored files are left alone.
    Useful when an old clone has stray edits like a deleted update.sh.

.PARAMETER NoPrompt
    Non-interactive mode. With local tracked changes and without -Force, exits 1.

.EXAMPLE
    # One-liner (updates E:\discbot by default):
    irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/update.ps1 | iex

    # Force-clean tracked edits then update:
    $env:DISCBOT_FORCE='1'; irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/update.ps1 | iex

    # Custom dir:
    $env:DISCBOT_DIR='E:\discbot'; irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/update.ps1 | iex
#>
[CmdletBinding()]
param(
    [string]$InstallDir = "",
    [string]$Branch     = "",
    [switch]$PullOnly,
    [switch]$Restart,
    [switch]$NoStart,
    [switch]$Force,
    [switch]$NoPrompt
)

$ErrorActionPreference = "Stop"
try { $Host.UI.RawUI.WindowTitle = "DiscBot — Updater" } catch {}

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

function Get-ScriptsDir($root) {
    # When run as a real file, prefer the script's own folder so local edits win.
    # When piped via `irm ... | iex`, $PSScriptRoot is empty — fall back to the
    # install tree so start/stop still work from the one-liner.
    if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "start.ps1"))) {
        return $PSScriptRoot
    }
    $fromInstall = Join-Path $root "scripts\windows"
    if (Test-Path $fromInstall) { return $fromInstall }
    return $null
}

# Honor DISCBOT_FORCE=1 from the environment for one-liner force updates
if (-not $Force -and $env:DISCBOT_FORCE -match '^(?i:1|true|yes)$') {
    $Force = $true
}

# Resolve install dir — same precedence as install.ps1
$defaultDir = "E:\discbot"
if (-not $InstallDir) {
    if ($env:DISCBOT_DIR) { $InstallDir = $env:DISCBOT_DIR }
    else {
        try {
            if ($PSScriptRoot) {
                $hereRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..") -ErrorAction Stop
                if (Test-Path (Join-Path $hereRoot.Path ".git")) { $InstallDir = $hereRoot.Path }
            }
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
        $scriptsDir = Get-ScriptsDir $InstallDir
        $localInstall = if ($scriptsDir) { Join-Path $scriptsDir "install.ps1" } else { $null }
        if ($localInstall -and (Test-Path $localInstall)) {
            & $localInstall -InstallDir $InstallDir -Branch $(if($Branch){$Branch}else{"master"}) -NoStart:($NoStart -or -not $Restart) -NoPrompt:$NoPrompt
            return
        }
        # Download and run install.ps1 (same source as this one-liner)
        $installSrc = (New-Object Net.WebClient).DownloadString(
            'https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/install.ps1')
        # Invoke with the same install dir via env so the downloaded script picks it up
        $env:DISCBOT_DIR = $InstallDir
        Invoke-Expression $installSrc
        return
    } else {
        Write-Fail "Nothing to update."
    }
}

Push-Location $InstallDir

# ---------- Git sanity ----------
Write-Step "Checking Git status"

# Match update.sh: only tracked modifications/deletions block the update.
# Untracked files (generated-page.html, local notes, copied scripts, …) are fine.
$trackedDirty = $false
git diff --quiet 2>$null
if ($LASTEXITCODE -ne 0) { $trackedDirty = $true }
git diff --cached --quiet 2>$null
if ($LASTEXITCODE -ne 0) { $trackedDirty = $true }

$untracked = @(git ls-files --others --exclude-standard 2>$null | Where-Object { $_ })
if ($untracked.Count -gt 0) {
    Write-Warn ("Untracked files present (left alone): " + ($untracked -join ", "))
}

if ($trackedDirty) {
    Write-Host ""
    Write-Host "  Tracked local changes:" -ForegroundColor Yellow
    git status --short --untracked-files=no
    Write-Host ""

    $action = $null
    if ($Force) {
        $action = "discard"
    } elseif ($NoPrompt) {
        Write-Fail "Tracked local changes found. Commit/stash them, re-run with -Force, or set `$env:DISCBOT_FORCE='1' for the one-liner."
    } else {
        Write-Host "  How should the updater handle them?" -ForegroundColor Yellow
        Write-Host "    [S] Stash them, update, then leave the stash for you (safe)" -ForegroundColor Gray
        Write-Host "    [D] Discard tracked changes and update (keeps .env / data / untracked)" -ForegroundColor Gray
        Write-Host "    [A] Abort" -ForegroundColor Gray
        $choice = Read-Host "  Choice [S/d/a]"
        if (-not $choice -or $choice -match '^(?i:s|stash)$') { $action = "stash" }
        elseif ($choice -match '^(?i:d|discard|force|f)$') { $action = "discard" }
        else { Write-Fail "Aborted. Commit/stash manually in '$InstallDir', then re-run." }
    }

    if ($action -eq "stash") {
        Write-Step "Stashing tracked local changes"
        git stash push -m "discbot-update auto-stash $(Get-Date -Format o)" --
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "git stash failed. Resolve manually in '$InstallDir'."
        }
        Write-Ok "stashed (restore later with: git stash pop)"
    } elseif ($action -eq "discard") {
        Write-Step "Discarding tracked local changes (untracked + ignored files kept)"
        # Hard-reset tracked tree only. Does NOT run git clean, so untracked
        # files and gitignored runtime data (.env, data/, logs/, Lavalink.jar) stay.
        git reset --hard HEAD
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "git reset --hard failed. Resolve manually in '$InstallDir'."
        }
        Write-Ok "tracked tree reset to HEAD"
    }
} else {
    Write-Ok "working tree clean (tracked files)"
}

if (-not $Branch) {
    $Branch = (git branch --show-current).Trim()
    if (-not $Branch) {
        Write-Fail "Detached HEAD — check out a branch first (e.g. git checkout master)."
    }
}
Write-Ok "branch = $Branch"

# ---------- Pull ----------
Write-Step "Pulling latest commits"
git fetch --prune origin
if ($LASTEXITCODE -ne 0) {
    Write-Fail "git fetch failed. Check your network / Git credentials."
}

$oldRev = (git rev-parse HEAD).Substring(0,7)
$upstream = "origin/$Branch"

# Verify remote branch exists
git rev-parse --verify --quiet "$upstream^{commit}" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Remote branch '$upstream' does not exist. Create it or pass -Branch <name>."
}

git merge --ff-only $upstream
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
# -NoStart (from install.ps1) suppresses the restart prompt.
# -Restart forces a restart. Otherwise ask (default yes when interactive).
if ($NoStart) {
    $doRestart = $false
} elseif ($Restart) {
    $doRestart = $true
} else {
    $doRestart = Request-Confirm "Stop and restart the running bot now?" $true
}

if ($doRestart) {
    $scriptsDir = Get-ScriptsDir $InstallDir
    $stop  = if ($scriptsDir) { Join-Path $scriptsDir "stop.ps1"  } else { $null }
    $start = if ($scriptsDir) { Join-Path $scriptsDir "start.ps1" } else { $null }
    if ($stop -and (Test-Path $stop)) {
        Write-Step "Stopping running processes"
        & $stop
        Start-Sleep -Seconds 2
    } else {
        Write-Warn "stop.ps1 not found — trying to continue."
    }
    if ($start -and (Test-Path $start)) {
        Write-Step "Starting bot again"
        & $start -InstallDir $InstallDir
    } else {
        Write-Warn "start.ps1 not found — please start the bot manually."
    }
}

Write-Host "`n✅ Done. Install dir: $InstallDir" -ForegroundColor Green
Pop-Location
