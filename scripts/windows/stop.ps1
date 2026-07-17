#Requires -Version 5.1
<#
.SYNOPSIS
    Stops DrusaBoT / Lavalink processes launched from E:\DrusaBoT.

.DESCRIPTION
    This Windows build is locked to E:\DrusaBoT, so the stopper only terminates
    Java/Python processes whose command line references that directory. This
    avoids killing unrelated Java/Python programs on the machine.
#>
[CmdletBinding()]
param()

$InstallDir = [IO.Path]::GetFullPath("E:\DrusaBoT")
Write-Host "🛑 Stopping DrusaBoT in $InstallDir..." -ForegroundColor Cyan

$killed = 0

# Kill Lavalink java processes launched from E:\DrusaBoT.
Get-CimInstance Win32_Process -Filter "Name='java.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*$InstallDir*" -and $_.CommandLine -like "*Lavalink.jar*" } |
    ForEach-Object {
        Write-Host "   Stopping Lavalink java (PID $($_.ProcessId))"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        $script:killed++
    }

# Kill bot Python processes launched from E:\DrusaBoT. Supports both legacy
# `python bot\main.py` and current `python -m bot.main` launch styles.
Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
        $_.CommandLine -like "*$InstallDir*" -and
        ($_.CommandLine -like "*bot.main*" -or $_.CommandLine -like "*bot\main.py*")
    } |
    ForEach-Object {
        Write-Host "   Stopping bot python (PID $($_.ProcessId))"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        $script:killed++
    }

if ($killed -eq 0) {
    Write-Host "   No running DrusaBoT processes found for E:\DrusaBoT." -ForegroundColor DarkGray
} else {
    Write-Host "✅ Killed $killed process(es)." -ForegroundColor Green
}
