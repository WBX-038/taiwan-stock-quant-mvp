$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "$Root\.venv_app\Scripts\python.exe"
$env:PYTHONPATH = "$Root\backend"

Write-Host "Starting Taiwan Stock Quant MVP at http://127.0.0.1:8000"
Set-Location "$Root\backend"
& $Python "$Root\backend\run_server.py"
