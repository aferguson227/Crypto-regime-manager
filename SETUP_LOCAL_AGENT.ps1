$ErrorActionPreference='Stop'
$Project='C:\Crypto\Projects'
$Dir=Join-Path $env:LOCALAPPDATA 'CryptoRegimeManager'
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
function ProtectPrompt([string]$Prompt) {
  $s=Read-Host $Prompt -AsSecureString
  return ConvertFrom-SecureString $s
}
$data=[ordered]@{
 api_key=ProtectPrompt 'KuCoin API key (General/read-only)'
 api_secret=ProtectPrompt 'KuCoin API secret'
 api_passphrase=ProtectPrompt 'KuCoin API passphrase'
 api_key_version=(Read-Host 'API key version [press Enter for automatic 3/2 detection]')
 api_base_url=(Read-Host 'API base URL [press Enter for automatic global/EU detection]')
}
$data | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Dir 'kucoin_credentials.json')
$action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $Project 'RUN_LOCAL_AGENT.ps1')+'"')
$trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15)
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName 'CryptoRegimeManager-LocalAgent' -Action $action -Trigger $trigger -Settings $settings -Description 'Read-only CRM local KuCoin capital refresh and validated publication.' -Force | Out-Null
Write-Host 'Local CRM agent configured. It refreshes silently in the background every 15 minutes while Windows can run the task.' -ForegroundColor Green
Write-Host 'Run RUN_LOCAL_AGENT.cmd now for the first refresh.'

# Create/update independent heavy research worker.
$ResearchAction=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+(Join-Path $Project 'RUN_RESEARCH_WORKER.ps1')+'"')
$ResearchTrigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 6)
$ResearchSettings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 8)
Register-ScheduledTask -TaskName 'CryptoRegimeManager-ResearchWorker' -Action $ResearchAction -Trigger $ResearchTrigger -Settings $ResearchSettings -Description 'Isolated CRM heavy research/backtesting every 6 hours.' -Force | Out-Null
Write-Host 'Heavy research is now isolated from the 15-minute trading refresh.' -ForegroundColor Green
