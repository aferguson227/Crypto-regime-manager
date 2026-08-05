@echo off
setlocal
cd /d "%~dp0"
echo Crypto Regime Manager V32.1 Diagnostics Engine
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_DIAGNOSTICS.ps1"
set CODE=%ERRORLEVEL%
echo.
if %CODE% EQU 0 (
  echo Diagnostics completed successfully.
) else (
  echo Diagnostics found one or more required failures.
)
pause
exit /b %CODE%
