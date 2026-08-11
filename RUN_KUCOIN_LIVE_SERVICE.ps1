$ErrorActionPreference = "Stop"

# V22: preserve V66/V68/V69 launcher contracts while making execution context-aware.
# Credential compatibility contract: kucoin_credentials.json
# The credential variable names remain explicit because the resident service inherits
# these local environment variables: KUCOIN_API_KEY, KUCOIN_API_SECRET,
# KUCOIN_API_PASSPHRASE.
# Clean-room rehearsal sets CRM_PROJECT_PATH to the isolated Candidate tree;
# production falls back to the directory containing this launcher.
$Project = $env:CRM_PROJECT_PATH
if ([string]::IsNullOrWhiteSpace($Project)) {
    $Project = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$Project = [System.IO.Path]::GetFullPath($Project)
if (-not (Test-Path -LiteralPath (Join-Path $Project "scripts\kucoin_live_data_service.py"))) {
    throw "KuCoin live service source is missing from project context: $Project"
}
Set-Location -LiteralPath $Project
$env:CRM_PROJECT_PATH = $Project
$env:PYTHONPATH = $Project

# Preserve the isolated runtime-app architecture in production, but never let a
# clean-room Candidate rehearsal escape into C:\Crypto\CRM_Data\Runtime.
$IsCandidate = $Project -like "*\CRM_Data\Installer\Candidate*"
if ($IsCandidate) {
    $RuntimeApp = $Project
} else {
    $RuntimeApp = "C:\Crypto\CRM_Data\Runtime\Application"
}

# Prefer the exact interpreter supplied by the installer/resident. Fall back to
# the Python available on PATH for normal production/manual launches.
$Python = $env:CRM_PYTHON_EXECUTABLE
if ([string]::IsNullOrWhiteSpace($Python) -or -not (Test-Path -LiteralPath $Python)) {
    $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -eq $cmd) { $cmd = Get-Command python -ErrorAction SilentlyContinue }
    if ($null -eq $cmd) { throw "Python executable not found for KuCoin live service." }
    $Python = $cmd.Source
}

Write-Output "KuCoin launcher project context: $Project"
Write-Output "KuCoin launcher python: $Python"

# Runtime-state preparation must execute from the same source tree as the
# KuCoin worker. This is the V20 clean-room isolation invariant.
& $Python -m scripts.runtime_state_manager prepare
if ($LASTEXITCODE -ne 0) { throw "Runtime application preparation failed." }

# In production, runtime_state_manager prepares CRM_Data\Runtime\Application.
# Candidate rehearsal deliberately remains in $Project so validation is isolated.
if (-not $IsCandidate -and (Test-Path -LiteralPath (Join-Path $RuntimeApp "scripts\kucoin_live_data_service.py"))) {
    Set-Location -LiteralPath $RuntimeApp
    $env:PYTHONPATH = $RuntimeApp
}
& $Python -m scripts.kucoin_live_data_service
$ServiceExit = $LASTEXITCODE
if ($ServiceExit -ne 0) { throw "KuCoin live data service exited with code $ServiceExit." }
exit 0
