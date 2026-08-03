$ErrorActionPreference='Stop'
$PackageRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot=Split-Path -Parent $PackageRoot
$UpdateRoot=Join-Path $PackageRoot 'update_files'

if (-not (Test-Path (Join-Path $ProjectRoot 'config.json'))) {
    throw "Place this extracted V22 update folder directly inside the Crypto Regime Manager project folder (for example C:\Crypto\Projects)."
}
if (-not (Test-Path $UpdateRoot)) {
    throw "The update_files folder is missing. Extract the complete ZIP before running the installer."
}

Write-Host "Installing Crypto Regime Manager V22.0.0..." -ForegroundColor Cyan
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$backup=Join-Path $ProjectRoot "backups\v22_$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null

# Back up user state and generated/private integration data. These files are not overwritten by the package.
$preserve=@(
    'config.json',
    'docs\candidate_registry.json',
    'docs\health_history.json',
    'docs\strategies.json',
    'docs\threecommas.json'
)
foreach($rel in $preserve){
    $src=Join-Path $ProjectRoot $rel
    if(Test-Path $src){
        $dst=Join-Path $backup $rel
        New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
        Copy-Item $src $dst -Force
    }
}

Copy-Item (Join-Path $UpdateRoot '*') $ProjectRoot -Recurse -Force

# V22 config intentionally replaces config.json after the previous version has been backed up.
# Normalise JSON to UTF-8 without BOM to prevent GitHub Actions JSONDecodeError failures.
$utf8=New-Object System.Text.UTF8Encoding($false)
Get-ChildItem $ProjectRoot -Recurse -Filter *.json |
    Where-Object {$_.FullName -notlike "*\backups\*" -and $_.FullName -notlike "*\data\data\*"} |
    ForEach-Object {
        $text=[IO.File]::ReadAllText($_.FullName)
        [IO.File]::WriteAllText($_.FullName,$text,$utf8)
    }

python -m py_compile (Join-Path $ProjectRoot 'scripts\core\engine.py') (Join-Path $ProjectRoot 'scripts\core\research_queue.py')
python -m pytest `
    (Join-Path $ProjectRoot 'tests\test_v19_operational_intelligence.py') `
    (Join-Path $ProjectRoot 'tests\test_v20_user_experience.py') `
    (Join-Path $ProjectRoot 'tests\test_v21_research_queue.py') `
    (Join-Path $ProjectRoot 'tests\test_v22_decision_intelligence.py') -q

Write-Host "V22.0.0 installed successfully." -ForegroundColor Green
Write-Host "Backup: $backup"
Write-Host "Next: review GitHub Desktop, commit, push, then run Update Crypto Regime Manager."
