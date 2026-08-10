$ErrorActionPreference='Stop'
$Project='C:\Crypto\Projects'
Set-Location $Project
python -m scripts.research_worker
exit $LASTEXITCODE
