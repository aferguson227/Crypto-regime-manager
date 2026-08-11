$ErrorActionPreference='Stop'
$Project='C:\Crypto\Projects'
$Task='CryptoRegimeManager-ResidentRuntime'
$Runner=Join-Path $Project 'RUN_CRM_RESIDENT.ps1'
if (!(Test-Path $Runner)) { throw "Missing $Runner" }

# Disable legacy repeating owners; V70 resident supervises these components itself.
foreach($name in @('CryptoRegimeManager-LocalAgent','CryptoRegimeManager-ResearchWorker')){
  schtasks.exe /End /TN $name 2>$null | Out-Null
  schtasks.exe /Change /TN $name /DISABLE 2>$null | Out-Null
}

# Stop any previous resident instance before replacing the task.
python -m scripts.crm_resident_control stop 2>$null | Out-Null
Start-Sleep -Seconds 2
schtasks.exe /End /TN $Task 2>$null | Out-Null

$tr="powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Runner`""
schtasks.exe /Create /TN $Task /SC ONLOGON /RL LIMITED /TR $tr /F | Out-Host
schtasks.exe /Run /TN $Task | Out-Host
Write-Host "CRM V70 resident runtime task installed and started."
