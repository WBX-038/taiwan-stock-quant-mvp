@echo off
set ROOT=%~dp0
set PYTHON=%ROOT%.venv_app\Scripts\python.exe
set PYTHONPATH=%ROOT%backend
echo Starting Taiwan Stock Quant MVP at http://127.0.0.1:8000
cd /d "%ROOT%backend"
"%PYTHON%" "%ROOT%backend\run_server.py"
