param(
 [string]$ProjectRoot = "C:\Crypto\Projects",
 [string]$TrainingDir,
 [string]$ValidationDir
)
$ErrorActionPreference='Stop'
if(-not (Test-Path (Join-Path $ProjectRoot 'scripts\kraken_research_pipeline.py'))){ throw "V30.1 is not installed in $ProjectRoot" }
if(-not $TrainingDir){ $TrainingDir=Read-Host 'Training folder or ZIP containing data through Q4 2025' }
if(-not $ValidationDir){ $ValidationDir=Read-Host 'Validation folder or ZIP containing Q1 2026 Kraken data' }
if(-not (Test-Path $TrainingDir)){ throw "Training source not found: $TrainingDir" }
if(-not (Test-Path $ValidationDir)){ throw "Validation source not found: $ValidationDir" }
Push-Location $ProjectRoot
try {
 python scripts\kraken_research_pipeline.py --training-dir "$TrainingDir" --validation-dir "$ValidationDir"
 if($LASTEXITCODE -ne 0){ throw "Research pipeline failed with exit code $LASTEXITCODE" }
 Write-Host "`nCompleted. Results: docs\walk_forward_registry.json" -ForegroundColor Green
 Write-Host "Commit and push the updated registry to display it in the app." -ForegroundColor Cyan
} finally { Pop-Location }
Read-Host 'Press Enter to close'
