$ErrorActionPreference='Stop'
$source=Join-Path $PSScriptRoot 'Crypto_Regime_Manager_V19_0_0'
$target=Split-Path $PSScriptRoot -Parent
Write-Host 'Installing Crypto Regime Manager V19.0.0...' -ForegroundColor Cyan
$preserve=@('data','threecommas','.git','docs\candidate_registry.json','docs\health_history.json','docs\strategies.json','config.json')
$backup=Join-Path $env:TEMP ('crm_v19_preserve_'+[guid]::NewGuid())
New-Item -ItemType Directory -Force -Path $backup | Out-Null
foreach($item in $preserve){$p=Join-Path $target $item;if(Test-Path $p){$dest=Join-Path $backup $item;New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null;Copy-Item $p $dest -Recurse -Force}}
Copy-Item (Join-Path $source '*') $target -Recurse -Force
foreach($item in $preserve){$p=Join-Path $backup $item;if(Test-Path $p){$dest=Join-Path $target $item;New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null;Copy-Item $p $dest -Recurse -Force}}
Write-Host 'V19.0.0 installed. Your data, 3Commas files, Git history and candidate evidence were preserved.' -ForegroundColor Green
