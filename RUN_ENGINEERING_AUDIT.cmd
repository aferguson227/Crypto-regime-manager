@echo off
cd /d "%~dp0"
python -m scripts.engineering_scheduler --mode daily
pause
