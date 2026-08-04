param([string]$ProjectRoot="C:\Crypto\Projects")
$ErrorActionPreference='Stop'
$Source=Join-Path $PSScriptRoot 'update_files'
if(-not (Test-Path (Join-Path $ProjectRoot '.git'))){ throw "Git project not found at $ProjectRoot" }
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'; $backup=Join-Path $ProjectRoot ".update-backups\V30_1_$stamp"; New-Item -ItemType Directory -Force -Path $backup | Out-Null
$files=Get-ChildItem $Source -File -Recurse
foreach($f in $files){
 $rel=$f.FullName.Substring($Source.Length).TrimStart('\'); $dest=Join-Path $ProjectRoot $rel
 if(Test-Path $dest){ $b=Join-Path $backup $rel; New-Item -ItemType Directory -Force -Path (Split-Path $b) | Out-Null; Copy-Item $dest $b -Force }
 New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null; Copy-Item $f.FullName $dest -Force
}
Copy-Item (Join-Path $PSScriptRoot 'RUN_V30_1_KRAKEN_RESEARCH.ps1') (Join-Path $ProjectRoot 'RUN_V30_1_KRAKEN_RESEARCH.ps1') -Force
Copy-Item (Join-Path $PSScriptRoot 'RUN_V30_1_KRAKEN_RESEARCH.bat') (Join-Path $ProjectRoot 'RUN_V30_1_KRAKEN_RESEARCH.bat') -Force
Push-Location $ProjectRoot
try {
 python -m py_compile scripts\cloud_update.py scripts\kraken_research_pipeline.py scripts\core\data_import.py scripts\core\backtest_lab.py scripts\core\walk_forward_lab.py
 if($LASTEXITCODE -ne 0){ throw 'Python validation failed' }
 python -m pytest -q tests\test_v29_strategy_factory.py tests\test_v30_kraken_pipeline.py tests\test_v30_1_zip_import.py
 if($LASTEXITCODE -ne 0){ throw 'V30 tests failed' }
 Write-Host "V30.1 installed and validated." -ForegroundColor Green
 Write-Host "Backup: $backup"
} finally { Pop-Location }
Read-Host 'Press Enter to close'
