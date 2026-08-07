$ErrorActionPreference='Stop'
$TaskName='CryptoRegimeManager-LocalAgent'
$Project='C:\Crypto\Projects'
$task=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
  Write-Host 'Local Agent scheduled task is not configured yet; SETUP_LOCAL_AGENT.cmd will create the V44 15-minute schedule.'
  exit 0
}
$action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "'+(Join-Path $Project 'RUN_LOCAL_AGENT.ps1')+'"')
$trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15)
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description 'Read-only CRM local refresh, intelligence rebuild and autonomous diagnostics every 15 minutes while Windows can run the task.' -Force | Out-Null
Write-Host 'Local Agent schedule updated to every 15 minutes.' -ForegroundColor Green
