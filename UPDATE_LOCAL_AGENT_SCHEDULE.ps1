$ErrorActionPreference='Stop'
$Project='C:\Crypto\Projects'

$LocalTask='CryptoRegimeManager-LocalAgent'
if (Get-ScheduledTask -TaskName $LocalTask -ErrorAction SilentlyContinue) { Stop-ScheduledTask -TaskName $LocalTask -ErrorAction SilentlyContinue }
$localArg='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $Project 'RUN_LOCAL_AGENT.ps1')+'"'
$localAction=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $localArg
$localTrigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 5)
$localSettings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName $LocalTask -Action $localAction -Trigger $localTrigger -Settings $localSettings -Description 'CRM fast publication/decision refresh every 5 minutes.' -Force | Out-Null

$LiveName='CryptoRegimeManager-LiveDataService'
$LiveScript=Join-Path $Project 'RUN_KUCOIN_LIVE_SERVICE.ps1'
$LiveCommand='powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$LiveScript+'"'
$RunKey='HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
New-Item -Path $RunKey -Force | Out-Null
New-ItemProperty -Path $RunKey -Name $LiveName -Value $LiveCommand -PropertyType String -Force | Out-Null
if (Get-ScheduledTask -TaskName $LiveName -ErrorAction SilentlyContinue) {
  Stop-ScheduledTask -TaskName $LiveName -ErrorAction SilentlyContinue
  Unregister-ScheduledTask -TaskName $LiveName -Confirm:$false -ErrorAction SilentlyContinue
}
Remove-Item (Join-Path $env:LOCALAPPDATA 'CryptoRegimeManager\kucoin_live_service.lock') -Force -ErrorAction SilentlyContinue
Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-NonInteractive','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',$LiveScript) -WindowStyle Hidden

$ResearchTask='CryptoRegimeManager-ResearchWorker'
$researchArg='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $Project 'RUN_RESEARCH_WORKER.ps1')+'"'
$researchAction=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $researchArg
$researchTrigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 6)
$researchSettings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 8)
Register-ScheduledTask -TaskName $ResearchTask -Action $researchAction -Trigger $researchTrigger -Settings $researchSettings -Description 'CRM isolated heavy research/backtesting every 6 hours.' -Force | Out-Null

Write-Host 'CRM background services updated:' -ForegroundColor Green
Write-Host ' - KuCoin Live Data Service: per-user startup, no admin rights required, started now.'
Write-Host ' - Local Agent: every 5 minutes.'
Write-Host ' - Research Worker: every 6 hours.'
