$ErrorActionPreference='Stop'
$Project='C:\Crypto\Projects'
Set-Location $Project
$python=(Get-Command python -ErrorAction Stop).Source
$pythonw=Join-Path (Split-Path $python) 'pythonw.exe'
if (Test-Path $pythonw) {
  & $pythonw -m scripts.crm_resident_runtime
} else {
  & $python -m scripts.crm_resident_runtime
}
exit $LASTEXITCODE
