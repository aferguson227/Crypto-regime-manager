$ErrorActionPreference='Stop'
$Project='C:\Crypto\Projects'
$Dir=Join-Path $env:LOCALAPPDATA 'CryptoRegimeManager'
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
# Operational cadence: New-TimeSpan -Minutes 5 is configured by UPDATE_LOCAL_AGENT_SCHEDULE.ps1.
function ProtectPrompt([string]$Prompt) { $s=Read-Host $Prompt -AsSecureString; return ConvertFrom-SecureString $s }
$data=[ordered]@{
 api_key=ProtectPrompt 'KuCoin API key (General/read-only)'
 api_secret=ProtectPrompt 'KuCoin API secret'
 api_passphrase=ProtectPrompt 'KuCoin API passphrase'
 api_key_version=(Read-Host 'API key version [press Enter for automatic 3/2 detection]')
 api_base_url=(Read-Host 'API base URL [press Enter for automatic global/EU detection]')
}
$data | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Dir 'kucoin_credentials.json')
& (Join-Path $Project 'UPDATE_LOCAL_AGENT_SCHEDULE.ps1')
Write-Host 'Local CRM credentials and background services configured.' -ForegroundColor Green
Write-Host 'The resident KuCoin service uses the same per-user credential store and starts without administrator rights.'
