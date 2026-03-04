$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$InstallDir = Join-Path $env:USERPROFILE '.openclaw-trader'

Write-Host "[1/5] Creating install directory at $InstallDir"
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $InstallDir 'plugin') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $InstallDir 'openplot_agent') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $InstallDir 'automation') -Force | Out-Null

Write-Host '[2/5] Copying strategy + agent files'
Copy-Item (Join-Path $RepoRoot 'plugin/ma_rsi_atr_plugin.pine') (Join-Path $InstallDir 'plugin/') -Force
Copy-Item (Join-Path $RepoRoot 'openplot_agent/bridge.py') (Join-Path $InstallDir 'openplot_agent/') -Force
if (-not (Test-Path (Join-Path $InstallDir 'openplot_agent/config.json'))) {
  Copy-Item (Join-Path $RepoRoot 'openplot_agent/config.example.json') (Join-Path $InstallDir 'openplot_agent/config.json')
}
Copy-Item (Join-Path $RepoRoot 'installer/install_tradingview_script.py') (Join-Path $InstallDir 'automation/') -Force

Write-Host '[3/5] Preparing Python environment'
$PythonExe = 'python'
& $PythonExe -m venv (Join-Path $InstallDir '.venv')
& (Join-Path $InstallDir '.venv/Scripts/python.exe') -m pip install --upgrade pip playwright
& (Join-Path $InstallDir '.venv/Scripts/python.exe') -m playwright install chromium

Write-Host '[4/5] Writing launchers'
@"
@echo off
set BASE_DIR=%~dp0
"%BASE_DIR%.venv\Scripts\python.exe" "%BASE_DIR%openplot_agent\bridge.py" --config "%BASE_DIR%openplot_agent\config.json"
"@ | Set-Content -Path (Join-Path $InstallDir 'run-openplot-agent.bat') -Encoding ASCII

@"
@echo off
set BASE_DIR=%~dp0
"%BASE_DIR%.venv\Scripts\python.exe" "%BASE_DIR%automation\install_tradingview_script.py" --pine "%BASE_DIR%plugin\ma_rsi_atr_plugin.pine"
"@ | Set-Content -Path (Join-Path $InstallDir 'install-tradingview-script.bat') -Encoding ASCII

Write-Host '[5/5] Done'
Write-Host "Edit config: $InstallDir\openplot_agent\config.json"
Write-Host "Run agent:   $InstallDir\run-openplot-agent.bat"
Write-Host "Install script in TradingView via browser automation: $InstallDir\install-tradingview-script.bat"
