$ErrorActionPreference = "Stop"

$ports = @(7000, 18787)
foreach ($port in $ports) {
    $ruleName = "gold-frp-$port"
    if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule `
            -DisplayName $ruleName `
            -Direction Inbound `
            -Action Allow `
            -Protocol TCP `
            -LocalPort $port `
            -Profile Any | Out-Null
    }
}

Write-Host "Firewall rules ensured for ports 7000 and 18787." -ForegroundColor Green
