@echo off
setlocal
cd /d C:\Crypto\Projects
powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "%CD%\RUN_CRM_RESIDENT.ps1"
