$ErrorActionPreference='Stop'
$Project='C:\Crypto\Projects'

# Fast publication/decision Local Agent every 5 minutes.
$LocalTask='CryptoRegimeManager-LocalAgent'
if (Get-ScheduledTask -TaskName $LocalTask -ErrorAction SilentlyContinue) {
  Stop-ScheduledTask -TaskName $LocalTask -ErrorAction SilentlyContinue
}
$localArg='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $Project 'RUN_LOCAL_AGENT.ps1')+'"'
$localAction=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $localArg
$localTrigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 5)
$localSettings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName $LocalTask -Action $localAction -Trigger $localTrigger -Settings $localSettings -Description 'CRM fast publication/decision refresh every 5 minutes.' -Force | Out-Null

# Resident private KuCoin truth service. It owns the credential context and stays alive.
$LiveTask='CryptoRegimeManager-LiveDataService'
if (Get-ScheduledTask -TaskName $LiveTask -ErrorAction SilentlyContinue) {
  Stop-ScheduledTask -TaskName $LiveTask -ErrorAction SilentlyContinue
}
Remove-Item (Join-Path $env:LOCALAPPDATA 'CryptoRegimeManager\kucoin_live_service.lock') -Force -ErrorAction SilentlyContinue
$liveArg='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $Project 'RUN_KUCOIN_LIVE_SERVICE.ps1')+'"'
$liveAction=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $liveArg
$liveTrigger=New-ScheduledTaskTrigger -AtLogOn
$liveSettings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName $LiveTask -Action $liveAction -Trigger $liveTrigger -Settings $liveSettings -Description 'CRM resident read-only KuCoin live trading data service.' -Force | Out-Null
Start-ScheduledTask -TaskName $LiveTask

# Heavy research remains isolated every six hours.
$ResearchTask='CryptoRegimeManager-ResearchWorker'
$researchArg='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $Project 'RUN_RESEARCH_WORKER.ps1')+'"'
$researchAction=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $researchArg
$researchTrigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 6)
$researchSettings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 8)
Register-ScheduledTask -TaskName $ResearchTask -Action $researchAction -Trigger $researchTrigger -Settings $researchSettings -Description 'CRM isolated heavy research/backtesting every 6 hours.' -Force | Out-Null

Write-Host 'CRM schedules updated:' -ForegroundColor Green
Write-Host ' - KuCoin Live Data Service: resident/background, starts at logon, prices/orders every ~20s, private refresh ~60s.'
Write-Host ' - Local Agent: every 5 minutes for publication/decision state.'
Write-Host ' - Research Worker: every 6 hours.'
