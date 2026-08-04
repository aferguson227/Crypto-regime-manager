$ErrorActionPreference='Stop'
$PackageRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot=Split-Path -Parent $PackageRoot
$UpdateRoot=Join-Path $PackageRoot 'update_files'

if (-not (Test-Path (Join-Path $ProjectRoot 'config.json'))) {
    throw "Place this extracted V25 update folder directly inside the Crypto Regime Manager project folder."
}
if (-not (Test-Path $UpdateRoot)) { throw "The update_files folder is missing. Extract the complete ZIP first." }

Write-Host "Installing Crypto Regime Manager V25.0.0..." -ForegroundColor Cyan
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$backup=Join-Path $ProjectRoot "backups\v25_0_$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null
$preserve=@('config.json','docs\candidate_registry.json','docs\health_history.json','docs\strategies.json','docs\threecommas.json')
foreach($rel in $preserve){$src=Join-Path $ProjectRoot $rel;if(Test-Path $src){$dst=Join-Path $backup $rel;New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent)|Out-Null;Copy-Item $src $dst -Force}}
Copy-Item (Join-Path $UpdateRoot '*') $ProjectRoot -Recurse -Force
$utf8=New-Object System.Text.UTF8Encoding($false)
Get-ChildItem $ProjectRoot -Recurse -Filter *.json | Where-Object {$_.FullName -notlike "*\backups\*"} | ForEach-Object {$text=[IO.File]::ReadAllText($_.FullName);[IO.File]::WriteAllText($_.FullName,$text,$utf8)}
$env:PYTHONPATH=Join-Path $ProjectRoot 'scripts'
python -m py_compile (Join-Path $ProjectRoot 'scripts\core\engine.py') (Join-Path $ProjectRoot 'scripts\core\research_queue.py') (Join-Path $ProjectRoot 'scripts\core\coin_discovery.py') (Join-Path $ProjectRoot 'scripts\cloud_update.py')
python -m pytest (Join-Path $ProjectRoot 'tests') -q
Write-Host "V25.0.0 installed successfully." -ForegroundColor Green
Write-Host "Backup: $backup"
Write-Host "Next: commit and push, then run the V25 Autonomous Crypto Regime Refresh workflow once."
