[CmdletBinding()]
param([string]$ProjectPath=$PSScriptRoot)
$ErrorActionPreference='Stop'
Set-Location $ProjectPath
python -m pytest -q
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
python scripts\validate_publish.py
exit $LASTEXITCODE
