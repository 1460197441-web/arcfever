$ErrorActionPreference = "Stop"

$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frpsExe = Join-Path $bundleRoot "frps.exe"
$configPath = Join-Path $bundleRoot "frps.toml"

Set-Location $bundleRoot

Write-Host "Starting ECS frps service..." -ForegroundColor Cyan
Write-Host "Bundle: $bundleRoot"
Write-Host "Bind port: 7000"
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $frpsExe)) {
    Write-Host "frps.exe not found: $frpsExe" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $configPath)) {
    Write-Host "frps.toml not found: $configPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    & $frpsExe -c $configPath
}
catch {
    Write-Host ""
    Write-Host "frps exited with an error:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
