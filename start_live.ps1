$ErrorActionPreference = "Stop"

$projectRoot = "C:\Users\arcfever\Documents\New project"
$packageRoot = Join-Path $projectRoot "python\gold_strategy_alert"
$pythonExe = Join-Path $projectRoot "runtime\python_embed\py312\python.exe"
$entryScript = Join-Path $packageRoot "run_service.py"
$dbPath = Join-Path $packageRoot "runtime\gold_strategy.db"
$logPath = Join-Path $packageRoot "runtime\service.log"

Set-Location $packageRoot
$env:PYTHONPATH = $packageRoot

Write-Host "Starting gold_strategy_alert live service..." -ForegroundColor Cyan
Write-Host "Project root: $projectRoot"
Write-Host "Package root: $packageRoot"
Write-Host "Database: $dbPath"
Write-Host "Log file: $logPath"
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $pythonExe)) {
    Write-Host "Python runtime not found: $pythonExe" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $entryScript)) {
    Write-Host "Entry script not found: $entryScript" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    & $pythonExe $entryScript
}
catch {
    Write-Host ""
    Write-Host "Service exited with an error:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
