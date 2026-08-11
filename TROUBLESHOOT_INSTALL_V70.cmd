@echo off
setlocal
cd /d C:\Crypto\Projects
title CRM Installer Doctor
python -m scripts.troubleshoot_installer
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
 echo Installer Doctor found a blocker. Review C:\Crypto\CRM_Data\Installer\installer_doctor_report.json
) else (
 echo Installer Doctor completed. Safe known issues were repaired automatically.
)
pause
exit /b %RC%
