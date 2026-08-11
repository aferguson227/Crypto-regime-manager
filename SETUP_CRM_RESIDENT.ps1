$ErrorActionPreference='Stop'
$Project='C:\Crypto\Projects'
$Task='CryptoRegimeManager-ResidentRuntime'
$Runner=Join-Path $Project 'RUN_CRM_RESIDENT.ps1'
if (!(Test-Path $Runner)) { throw "Missing $Runner" }

function Test-ScheduledTaskExists([string]$Name) {
  $null = schtasks.exe /Query /TN $Name 2>$null
  return ($LASTEXITCODE -eq 0)
}

function Stop-ScheduledTaskIfExists([string]$Name) {
  if (Test-ScheduledTaskExists $Name) {
    schtasks.exe /End /TN $Name 2>$null | Out-Null
  }
}

function Disable-ScheduledTaskIfExists([string]$Name) {
  if (Test-ScheduledTaskExists $Name) {
    schtasks.exe /Change /TN $Name /DISABLE 2>$null | Out-Null
  }
}

# Disable legacy repeating owners; V70 resident supervises these components itself.
foreach($name in @('CryptoRegimeManager-LocalAgent','CryptoRegimeManager-ResearchWorker')){
  Stop-ScheduledTaskIfExists $name
  Disable-ScheduledTaskIfExists $name
}

# Stop an old resident instance only if a prior V70 task already exists.
python -m scripts.crm_resident_control stop 2>$null | Out-Null
Start-Sleep -Seconds 2
Stop-ScheduledTaskIfExists $Task

# Create/replace resident task idempotently.
$tr="powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Runner`""
schtasks.exe /Create /TN $Task /SC ONLOGON /RL LIMITED /TR $tr /F | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Could not create $Task scheduled task." }

# Verify task exists before starting it.
if (!(Test-ScheduledTaskExists $Task)) { throw "$Task was not created successfully." }

schtasks.exe /Run /TN $Task | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Could not start $Task scheduled task." }

Write-Host "CRM V70 resident runtime task installed and started."
