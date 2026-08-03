$ErrorActionPreference='Stop'
$source=Join-Path $PSScriptRoot 'Crypto_Regime_Manager_V20_0_0'
$target=Split-Path $PSScriptRoot -Parent
Write-Host 'Installing Crypto Regime Manager V20.0.0...' -ForegroundColor Cyan
if(!(Test-Path (Join-Path $target 'docs')) -or !(Test-Path (Join-Path $target 'scripts'))){throw 'Place v20_easy_package inside your existing Crypto Regime Manager project folder before running the installer.'}
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$backup=Join-Path $target ('backups\v20_preinstall_'+$stamp)
$preserve=@('.git','data','threecommas','threecommas_private_setup','.env','docs\candidate_registry.json','docs\health_history.json','docs\strategies.json','docs\threecommas.json')
New-Item -ItemType Directory -Force -Path $backup | Out-Null
foreach($item in $preserve){$p=Join-Path $target $item;if(Test-Path $p){$dest=Join-Path $backup $item;New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null;Copy-Item $p $dest -Recurse -Force}}
Copy-Item (Join-Path $source '*') $target -Recurse -Force
foreach($item in $preserve){$p=Join-Path $backup $item;if(Test-Path $p){$dest=Join-Path $target $item;New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null;Copy-Item $p $dest -Recurse -Force}}
# Preserve the user's config, but guarantee release labels are correct.
$configPath=Join-Path $target 'config.json'
if(Test-Path $configPath){$cfg=Get-Content $configPath -Raw | ConvertFrom-Json;if(-not $cfg.app){$cfg | Add-Member -NotePropertyName app -NotePropertyValue ([pscustomobject]@{})};$cfg.app.version='20.0.0';$cfg | ConvertTo-Json -Depth 100 | Set-Content $configPath -Encoding UTF8}
@{version='20.0.0';release='Professional Trading Intelligence'} | ConvertTo-Json | Set-Content (Join-Path $target 'docs\version.json') -Encoding UTF8
Set-Content (Join-Path $target 'VERSION') '20.0.0' -Encoding UTF8
Write-Host ''
Write-Host 'V20.0.0 installed successfully.' -ForegroundColor Green
Write-Host ('Backup created: '+$backup) -ForegroundColor DarkGray
Write-Host 'Preserved: data, Git history, 3Commas state, candidate registry, health history and generated strategy results.' -ForegroundColor Green
Write-Host 'Updated: Home, Assets, Research, Data, More, mobile settings and version metadata.' -ForegroundColor Green
