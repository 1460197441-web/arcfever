$ErrorActionPreference = "Stop"

$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frpcExe = Join-Path $bundleRoot "frpc.exe"
$configPath = Join-Path $bundleRoot "frpc.toml"
$remoteUrl = "http://114.55.225.26:18787/?token=dd2e15efa3da24d8c55967fd37a0db1b"

Set-Location $bundleRoot

Write-Host "Starting local frpc tunnel..." -ForegroundColor Cyan
Write-Host "Bundle: $bundleRoot"
Write-Host "Remote URL: $remoteUrl"
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $frpcExe)) {
    Write-Host "frpc.exe not found: $frpcExe" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $configPath)) {
    Write-Host "frpc.toml not found: $configPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    & $frpcExe -c $configPath
}
catch {
    Write-Host ""
    Write-Host "frpc exited with an error:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
