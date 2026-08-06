@echo off
setlocal
cd /d "%~dp0"
echo Generating CRM Engineering Package...
python -m scripts.operational_intelligence_engine || goto :fail
python -m scripts.github_actions_intelligence_engine || goto :fail
python -m scripts.decision_quality_engine || goto :fail
python -m scripts.self_healing_engine || goto :fail
python -m scripts.ui_health_engine || goto :fail
python -m scripts.engineering_intelligence_engine || goto :fail
python -m scripts.engineering_package || goto :fail
echo.
echo Engineering package generated successfully.
pause
exit /b 0
:fail
echo.
echo Engineering package generation failed.
pause
exit /b 1
