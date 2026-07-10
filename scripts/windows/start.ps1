#Requires -Version 5.1
<#
.SYNOPSIS
    Starts DiscBot (Lavalink + Discord bot) from PowerShell.

.DESCRIPTION
    Launches Lavalink (java) in one new console window and the bot
    (python from .venv) in another. Waits a few seconds between them
    so Lavalink has time to bind before the bot connects.

.PARAMETER InstallDir
    Project root. Priority:
      1. -InstallDir
      2. $env:DISCBOT_DIR
      3. the folder containing this script (scripts/windows -> repo root)
      4. E:\discbot

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\windows\start.ps1
#>
[CmdletBinding()]
param(
    [string]$InstallDir = ""
)

$ErrorActionPreference = "Stop"

# Resolve install dir
if (-not $InstallDir) {
    if ($env:DISCBOT_DIR) { $InstallDir = $env:DISCBOT_DIR }
    else {
        try {
            $hereRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
            if (Test-Path (Join-Path $hereRoot ".git")) { $InstallDir = $hereRoot }
        } catch {}
        if (-not $InstallDir) { $InstallDir = "E:\discbot" }
    }
}
$InstallDir = [IO.Path]::GetFullPath($InstallDir)

Push-Location $InstallDir

if (-not (Test-Path ".env"))                       { Write-Host "X  .env not found at $InstallDir. Run install.ps1 first." -ForegroundColor Red; exit 1 }
if (-not (Test-Path ".venv\Scripts\python.exe"))   { Write-Host "X  .venv not found at $InstallDir. Run install.ps1 first." -ForegroundColor Red; exit 1 }
if (-not (Test-Path "Lavalink.jar"))               { Write-Host "X  Lavalink.jar not found at $InstallDir. Run install.ps1 first." -ForegroundColor Red; exit 1 }
if (-not (Test-Path "application.yml")) { Copy-Item "application.yml.example" "application.yml" }

Write-Host "🎵 DiscBot @ $InstallDir" -ForegroundColor Magenta
Write-Host "🎵 Starting Lavalink..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$InstallDir'; java -jar Lavalink.jar" -WorkingDirectory $InstallDir

Write-Host "   Waiting 8 seconds for Lavalink to boot..." -ForegroundColor DarkGray
Start-Sleep -Seconds 8

Write-Host "🎵 Starting Discord bot..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$InstallDir'; .\.venv\Scripts\Activate.ps1; python bot\main.py" -WorkingDirectory $InstallDir

Write-Host ""
Write-Host "✅ Both processes started in separate windows." -ForegroundColor Green
Write-Host "   Use stop.ps1 / stop.bat to shut everything down." -ForegroundColor DarkGray
Pop-Location
