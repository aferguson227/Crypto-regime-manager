@echo off
cd /d "%~dp0"
python -m scripts.engineering_scheduler --mode pre-release
if errorlevel 1 (echo Release audit failed.& pause& exit /b 1)
python -m scripts.engineering_package
pause
