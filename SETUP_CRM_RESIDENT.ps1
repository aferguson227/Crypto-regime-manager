$ErrorActionPreference='Stop'
Set-Location 'C:\Crypto\Projects'
python -m scripts.resident_task_manager install
if ($LASTEXITCODE -ne 0) { throw "CRM resident task manager failed." }
python -m scripts.crm_resident_health
exit $LASTEXITCODE
