#Requires -Version 5.1
<#
.SYNOPSIS
    Starts DiscBot (Lavalink + Discord bot) from PowerShell.

.DESCRIPTION
    Launches Lavalink (java) in one new console window and the bot
    (python from .venv) in another. Waits a few seconds between them
    so Lavalink has time to bind before the bot connects.

.PARAMETER InstallDir
    Backward-compatible parameter. Only E:\discbot is accepted.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\windows\start.ps1
#>
[CmdletBinding()]
param(
    [string]$InstallDir = ""
)

$ErrorActionPreference = "Stop"

# Fixed install dir: all DiscBot files live under E:\discbot.
$fixedDir = [IO.Path]::GetFullPath("E:\discbot")
if ($InstallDir -and ([IO.Path]::GetFullPath($InstallDir).TrimEnd('\') -ne $fixedDir.TrimEnd('\'))) {
    Write-Host "X  DiscBot is locked to E:\discbot. Refusing custom InstallDir: $InstallDir" -ForegroundColor Red
    exit 1
}
if ($env:DISCBOT_DIR -and ([IO.Path]::GetFullPath($env:DISCBOT_DIR).TrimEnd('\') -ne $fixedDir.TrimEnd('\'))) {
    Write-Host "X  DiscBot is locked to E:\discbot. Remove DISCBOT_DIR or set it to E:\discbot." -ForegroundColor Red
    exit 1
}
$InstallDir = $fixedDir

Push-Location $InstallDir

if (-not (Test-Path ".env"))                       { Write-Host "X  .env not found at $InstallDir. Run install.ps1 first." -ForegroundColor Red; exit 1 }
if (-not (Test-Path ".venv\Scripts\python.exe"))   { Write-Host "X  .venv not found at $InstallDir. Run install.ps1 first." -ForegroundColor Red; exit 1 }
# Lavalink runs from lavalink/ subdirectory
$lavalinkDir = Join-Path $InstallDir "lavalink"

if (-not (Test-Path (Join-Path $lavalinkDir "Lavalink.jar"))) {
    Write-Host "X  Lavalink.jar not found in $lavalinkDir. Run install.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "🎵 DiscBot @ $InstallDir" -ForegroundColor Magenta
Write-Host "🎵 Starting Lavalink..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$lavalinkDir'; java -jar Lavalink.jar" -WorkingDirectory $lavalinkDir

Write-Host "   Waiting 8 seconds for Lavalink to boot..." -ForegroundColor DarkGray
Start-Sleep -Seconds 8

Write-Host "🎵 Starting Discord bot..." -ForegroundColor Cyan
$botCmd = "cd '$InstallDir'; .\.venv\Scripts\python.exe -m bot.main"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $botCmd -WorkingDirectory $InstallDir

Write-Host ""
Write-Host "✅ Both processes started in separate windows." -ForegroundColor Green
Write-Host "   Use stop.ps1 / stop.bat to shut everything down." -ForegroundColor DarkGray
Pop-Location
