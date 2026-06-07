@echo off
setlocal
cd /d "%~dp0\.."
set PYTHONPATH=desktop
python -m second_monitor %*
