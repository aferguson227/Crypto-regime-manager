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
  python -m scripts.local_agent --publish
  exit $LASTEXITCODE
} finally {
  Remove-Item Env:KUCOIN_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:KUCOIN_API_SECRET -ErrorAction SilentlyContinue
  Remove-Item Env:KUCOIN_API_PASSPHRASE -ErrorAction SilentlyContinue
}
