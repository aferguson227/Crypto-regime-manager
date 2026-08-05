[CmdletBinding()]
param([string]$ProjectPath=$PSScriptRoot,[switch]$Push,[switch]$Tag)
$ErrorActionPreference='Stop'
& (Join-Path $ProjectPath 'build.ps1') -ProjectPath $ProjectPath -Screenshots
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
& (Join-Path $ProjectPath 'package.ps1') -ProjectPath $ProjectPath -SkipBuild
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$v=(Get-Content (Join-Path $ProjectPath 'VERSION') -Raw).Trim()
if($Tag){
  $dirty=(& git -C $ProjectPath status --porcelain|Out-String).Trim();if($dirty){throw 'Cannot tag a dirty repository'}
  git -C $ProjectPath tag -a "v$v" -m "Crypto Regime Manager v$v"
  if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
}
if($Push){git -C $ProjectPath push origin main;if($LASTEXITCODE -ne 0){exit $LASTEXITCODE};if($Tag){git -C $ProjectPath push origin "v$v"}}
Write-Host 'Release completed.' -ForegroundColor Green
