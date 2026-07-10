#Requires -Version 5.1
<#
.SYNOPSIS
    Stops any running DiscBot / Lavalink processes.
#>
[CmdletBinding()]
param()

Write-Host "🛑 Stopping DiscBot..." -ForegroundColor Cyan

$killed = 0

# Kill Lavalink java processes whose command line contains "Lavalink.jar"
Get-CimInstance Win32_Process -Filter "Name='java.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*Lavalink.jar*" } |
    ForEach-Object {
        Write-Host "   Stopping java (PID $($_.ProcessId))"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        $killed++
    }

# Kill python processes whose command line points at bot\main.py
Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*bot\main.py*" } |
    ForEach-Object {
        Write-Host "   Stopping python (PID $($_.ProcessId))"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        $killed++
    }

if ($killed -eq 0) {
    Write-Host "   No running DiscBot processes found." -ForegroundColor DarkGray
} else {
    Write-Host "✅ Killed $killed process(es)." -ForegroundColor Green
}
