param(
  [string]$EnvId = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Find-WechatDevtoolsCli {
  $candidates = @(
    (Join-Path ${env:ProgramFiles(x86)} 'Tencent\微信web开发者工具\cli.bat'),
    (Join-Path $env:ProgramFiles 'Tencent\微信web开发者工具\cli.bat')
  )

  foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) {
      return $candidate
    }
  }

  $found = Get-ChildItem "$env:SystemDrive\" -Recurse -Filter cli.bat -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -like '*微信*开发者工具*' } |
    Select-Object -First 1

  if ($found) {
    return $found.FullName
  }

  throw "未找到微信开发者工具 CLI。"
}

$CliPath = Find-WechatDevtoolsCli

if ([string]::IsNullOrWhiteSpace($EnvId)) {
  $EnvId = Read-Host "请输入云开发环境 ID"
}

if ([string]::IsNullOrWhiteSpace($EnvId)) {
  throw "环境 ID 不能为空"
}

$envFile = Join-Path $ProjectRoot "utils\env.js"
$envContent = @"
module.exports = {
  useCloud: true,
  cloudEnvId: '$EnvId'
};
"@
Set-Content -Path $envFile -Value $envContent -Encoding UTF8

Push-Location (Join-Path $ProjectRoot "cloudfunctions\gateway")
npm install
Pop-Location

Push-Location (Join-Path $ProjectRoot "cloudfunctions\bootstrap")
npm install
Pop-Location

& $CliPath cloud functions deploy --project $ProjectRoot --env $EnvId --names gateway bootstrap

Write-Host ""
Write-Host "云函数已部署。"
Write-Host "下一步请在微信开发者工具 -> 云开发控制台里运行一次 bootstrap 云函数。"
Write-Host "运行成功后，gateway 会优先读取真实云数据库，失败时自动回退到 mock。"
