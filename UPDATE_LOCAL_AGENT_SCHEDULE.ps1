$ErrorActionPreference='Stop'
$TaskName='CryptoRegimeManager-LocalAgent'
$Project='C:\Crypto\Projects'
$task=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) { Write-Host 'Local Agent scheduled task is not configured yet; SETUP_LOCAL_AGENT.cmd will create it.'; exit 0 }
# Hidden PowerShell prevents the 15-minute agent from interrupting the desktop.
$arg='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $Project 'RUN_LOCAL_AGENT.ps1')+'"'
$action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arg
$trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15)
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description 'CRM silent read-only refresh, research and diagnostics every 15 minutes.' -Force | Out-Null
Write-Host 'Local Agent schedule updated: silent/background, every 15 minutes.' -ForegroundColor Green
