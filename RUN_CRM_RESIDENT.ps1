$ErrorActionPreference='Stop'
$Project=$env:CRM_PROJECT_PATH
if (-not $Project) { $Project='C:\Crypto\Projects' }
Set-Location $Project
$python=(Get-Command python -ErrorAction Stop).Source
$pythonw=Join-Path (Split-Path $python) 'pythonw.exe'
$env:CRM_PROJECT_PATH=$Project
if (Test-Path $pythonw) {
  Start-Process -FilePath $pythonw -ArgumentList @('-m','scripts.crm_resident_runtime') -WindowStyle Hidden
  exit 0
}
Start-Process -FilePath $python -ArgumentList @('-m','scripts.crm_resident_runtime') -WindowStyle Hidden
exit 0
