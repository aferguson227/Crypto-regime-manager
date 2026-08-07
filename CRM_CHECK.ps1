$ErrorActionPreference='Stop'
Set-Location 'C:\Crypto\Projects'
python -m scripts.autonomous_diagnostics --full
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m scripts.diagnostics_manager --full
exit $LASTEXITCODE
