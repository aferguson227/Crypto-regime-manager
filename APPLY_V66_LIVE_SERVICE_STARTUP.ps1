$ErrorActionPreference='Stop'
$Project='C:\Crypto\Projects'
$LiveName='CryptoRegimeManager-LiveDataService'
$LiveScript=Join-Path $Project 'RUN_KUCOIN_LIVE_SERVICE.ps1'
$LiveCommand='powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$LiveScript+'"'
$RunKey='HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'

New-Item -Path $RunKey -Force | Out-Null
New-ItemProperty -Path $RunKey -Name $LiveName -Value $LiveCommand -PropertyType String -Force | Out-Null

# Remove obsolete scheduled-task version if it exists. Failure to remove it is non-blocking.
if (Get-ScheduledTask -TaskName $LiveName -ErrorAction SilentlyContinue) {
  Stop-ScheduledTask -TaskName $LiveName -ErrorAction SilentlyContinue
  Unregister-ScheduledTask -TaskName $LiveName -Confirm:$false -ErrorAction SilentlyContinue
}

Remove-Item (Join-Path $env:LOCALAPPDATA 'CryptoRegimeManager\kucoin_live_service.lock') -Force -ErrorAction SilentlyContinue
Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-NonInteractive','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',$LiveScript) -WindowStyle Hidden
Start-Sleep -Seconds 3

Write-Host 'KuCoin Live Data Service startup hotfix applied.' -ForegroundColor Green
Write-Host 'Mechanism: current-user HKCU startup; administrator rights are not required.'
Write-Host 'The service was also started immediately.'
