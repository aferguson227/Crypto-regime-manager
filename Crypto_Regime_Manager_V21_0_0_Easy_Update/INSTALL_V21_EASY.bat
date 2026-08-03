@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALL_V21_EASY.ps1"
if errorlevel 1 (
 echo.
 echo Installation failed. No automatic Git commit was attempted.
 pause
 exit /b 1
)
pause
