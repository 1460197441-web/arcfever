@echo off
setlocal

set "PS_SCRIPT=C:\Users\arcfever\Documents\New project\start_live.ps1"

if not exist "%PS_SCRIPT%" (
  echo start_live.ps1 not found:
  echo %PS_SCRIPT%
  pause
  exit /b 1
)

powershell.exe -NoLogo -NoExit -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
