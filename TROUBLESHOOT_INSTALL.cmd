@echo off
setlocal
cd /d "%~dp0"
title CRM Install Troubleshooter
python -m scripts.installer_preflight
echo.
if errorlevel 1 (
 echo Troubleshooter found an item that still needs attention. Review the report above.
) else (
 echo Troubleshooter completed: CRM is ready for an installer.
)
pause
