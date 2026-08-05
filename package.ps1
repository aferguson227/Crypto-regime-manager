[CmdletBinding()]
param([string]$ProjectPath=$PSScriptRoot,[switch]$SkipBuild)
$ErrorActionPreference='Stop';$ProgressPreference='SilentlyContinue'
if(-not $SkipBuild){& (Join-Path $ProjectPath 'build.ps1') -ProjectPath $ProjectPath -Screenshots;if($LASTEXITCODE -ne 0){throw 'Build gate failed; package not created.'}}
$version=(Get-Content (Join-Path $ProjectPath 'VERSION') -Raw).Trim()
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$out=Join-Path $ProjectPath 'release'
New-Item -ItemType Directory -Path $out -Force|Out-Null
$stage=Join-Path $env:TEMP "CRM-package-$stamp"
if(Test-Path $stage){Remove-Item $stage -Recurse -Force}
New-Item -ItemType Directory -Path $stage -Force|Out-Null
$payload=Join-Path $stage "Crypto_Regime_Manager_V$($version.Replace('.','_'))"
& robocopy $ProjectPath $payload /E /R:1 /W:1 /NFL /NDL /NP /XD .git .venv venv __pycache__ .pytest_cache diagnostics_exports diagnostics_logs release /XF .env *.pem *.key
if($LASTEXITCODE -gt 7){throw "Robocopy failed: $LASTEXITCODE"}
$zip=Join-Path $out "Crypto_Regime_Manager_V$($version.Replace('.','_'))_$stamp.zip"
Compress-Archive -Path $payload -DestinationPath $zip -CompressionLevel Optimal -Force
$hash=(Get-FileHash $zip -Algorithm SHA256).Hash
@{version=$version;created_at=(Get-Date).ToString('o');sha256=$hash;file=[IO.Path]::GetFileName($zip)}|ConvertTo-Json|Set-Content "$zip.sha256.json" -Encoding UTF8
Remove-Item $stage -Recurse -Force
Write-Host "Package: $zip" -ForegroundColor Green
Write-Host "SHA256:  $hash"
