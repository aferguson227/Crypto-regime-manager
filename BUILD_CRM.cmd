@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" -Screenshots
set RC=%ERRORLEVEL%
echo.
if %RC% EQU 0 (echo Build passed.) else (echo Build failed. No release should be produced.)
pause
exit /b %RC%
