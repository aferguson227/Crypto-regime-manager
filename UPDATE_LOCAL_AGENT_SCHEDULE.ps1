$ErrorActionPreference='Stop'
$Project='C:\Crypto\Projects'

# Fast operational Local Agent every 15 minutes.
$LocalTask='CryptoRegimeManager-LocalAgent'
$task=Get-ScheduledTask -TaskName $LocalTask -ErrorAction SilentlyContinue
if ($task) {
  Stop-ScheduledTask -TaskName $LocalTask -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 2
  $arg='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $Project 'RUN_LOCAL_AGENT.ps1')+'"'
  $action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arg
  $trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15)
  $settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
  Register-ScheduledTask -TaskName $LocalTask -Action $action -Trigger $trigger -Settings $settings -Description 'CRM fast private trading/accounting refresh every 15 minutes.' -Force | Out-Null
  Write-Host 'Local Agent schedule updated: hidden/background, every 15 minutes.' -ForegroundColor Green
} else {
  Write-Host 'Local Agent scheduled task is not configured yet; SETUP_LOCAL_AGENT.cmd will create it.'
}

# Heavy research is independent so it cannot block trading/accounting freshness.
$ResearchTask='CryptoRegimeManager-ResearchWorker'
$arg2='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $Project 'RUN_RESEARCH_WORKER.ps1')+'"'
$action2=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arg2
$trigger2=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 6)
$settings2=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 8)
Register-ScheduledTask -TaskName $ResearchTask -Action $action2 -Trigger $trigger2 -Settings $settings2 -Description 'CRM isolated heavy market research/backtesting every 6 hours.' -Force | Out-Null
Write-Host 'Research Worker schedule updated: isolated/background, every 6 hours.' -ForegroundColor Green
