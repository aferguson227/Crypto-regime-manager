$ErrorActionPreference='Stop'
$Project='C:\Crypto\Projects'
$CredPath=Join-Path $env:LOCALAPPDATA 'CryptoRegimeManager\kucoin_credentials.json'
if (!(Test-Path $CredPath)) { throw "Local CRM credentials are not configured. Run SETUP_LOCAL_AGENT.cmd first." }
$data=Get-Content $CredPath -Raw | ConvertFrom-Json
function Unprotect([string]$v) {
  $s=ConvertTo-SecureString $v
  $ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
  try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
$env:KUCOIN_API_KEY=Unprotect $data.api_key
$env:KUCOIN_API_SECRET=Unprotect $data.api_secret
$env:KUCOIN_API_PASSPHRASE=Unprotect $data.api_passphrase
if ($data.api_key_version) { $env:KUCOIN_API_KEY_VERSION=$data.api_key_version }
if ($data.api_base_url) { $env:KUCOIN_API_BASE_URL=$data.api_base_url }
try {
  Set-Location $Project
  # Refresh the isolated runtime application mirror from committed source.
  python -m scripts.runtime_state_manager prepare
  if ($LASTEXITCODE -ne 0) { throw "Runtime application preparation failed." }
  $RuntimeApp=Join-Path 'C:\Crypto\CRM_Data\Runtime' 'App'
  if ($env:CRM_DATA_ROOT) { $RuntimeApp=Join-Path (Join-Path $env:CRM_DATA_ROOT 'Runtime') 'App' }
  Set-Location $RuntimeApp
  python -m scripts.kucoin_live_data_service
  exit $LASTEXITCODE
} finally {
  Remove-Item Env:KUCOIN_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:KUCOIN_API_SECRET -ErrorAction SilentlyContinue
  Remove-Item Env:KUCOIN_API_PASSPHRASE -ErrorAction SilentlyContinue
}
