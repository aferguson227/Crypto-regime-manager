@echo off
setlocal
cd /d "%~dp0"
echo CRM V37.2 Safe Self-Healing Scan
python -m scripts.self_healing_engine --apply-safe
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" echo Review docs\self_healing_status.json
pause
exit /b %RC%
