$ErrorActionPreference='Stop'
$PackageRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot=Split-Path -Parent $PackageRoot
$UpdateRoot=Join-Path $PackageRoot 'update_files'
if (-not (Test-Path (Join-Path $ProjectRoot 'config.json'))) { throw "Place this extracted V21 folder directly inside the Crypto Regime Manager project folder." }
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$backup=Join-Path $ProjectRoot "backups\v21_$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null
$preserve=@('config.json','docs\candidate_registry.json','docs\health_history.json','docs\strategies.json','docs\threecommas.json')
foreach($rel in $preserve){$src=Join-Path $ProjectRoot $rel;if(Test-Path $src){$dst=Join-Path $backup $rel;New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent)|Out-Null;Copy-Item $src $dst -Force}}
Copy-Item (Join-Path $UpdateRoot '*') $ProjectRoot -Recurse -Force
# V21 config intentionally replaces config.json after it has been backed up.
$utf8=New-Object System.Text.UTF8Encoding($false)
Get-ChildItem $ProjectRoot -Recurse -Filter *.json | Where-Object {$_.FullName -notlike "*\backups\*" -and $_.FullName -notlike "*\data\data\*"} | ForEach-Object {$text=[IO.File]::ReadAllText($_.FullName);[IO.File]::WriteAllText($_.FullName,$text,$utf8)}
python -m py_compile (Join-Path $ProjectRoot 'scripts\core\engine.py') (Join-Path $ProjectRoot 'scripts\core\research_queue.py')
python -m pytest (Join-Path $ProjectRoot 'tests\test_v21_research_queue.py') -q
Write-Host "V21.0.0 installed successfully." -ForegroundColor Green
Write-Host "Backup: $backup"
Write-Host "Next: review GitHub Desktop, commit, push, then run Update Crypto Regime Manager."
