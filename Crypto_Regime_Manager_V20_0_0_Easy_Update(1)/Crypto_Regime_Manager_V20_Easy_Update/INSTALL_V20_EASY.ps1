$ErrorActionPreference='Stop'
$source=Join-Path $PSScriptRoot 'Crypto_Regime_Manager_V20_0_0'
$target=Split-Path $PSScriptRoot -Parent
Write-Host 'Installing Crypto Regime Manager V20.0.0...' -ForegroundColor Cyan

$preserve=@(
  'data',
  'threecommas',
  '.git',
  'docs\candidate_registry.json',
  'docs\health_history.json',
  'docs\strategies.json',
  'docs\threecommas.json',
  'config.json'
)
$backup=Join-Path $env:TEMP ('crm_v20_preserve_'+[guid]::NewGuid())
New-Item -ItemType Directory -Force -Path $backup | Out-Null
try {
  foreach($item in $preserve){
    $p=Join-Path $target $item
    if(Test-Path $p){
      $dest=Join-Path $backup $item
      New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
      Copy-Item $p $dest -Recurse -Force
    }
  }

  Copy-Item (Join-Path $source '*') $target -Recurse -Force

  foreach($item in $preserve){
    $p=Join-Path $backup $item
    if(Test-Path $p){
      $dest=Join-Path $target $item
      New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
      Copy-Item $p $dest -Recurse -Force
    }
  }

  # Preserve the user's complete configuration, but move its release label to V20.
  $configPath=Join-Path $target 'config.json'
  if(Test-Path $configPath){
    $config=Get-Content $configPath -Raw | ConvertFrom-Json
    $config.version='20.0.0'
    if($config.PSObject.Properties.Name -contains 'note'){
      $config.note='V20 simplified operator experience; trading and forward-validation logic preserved.'
    }
    $config | ConvertTo-Json -Depth 100 | Set-Content $configPath -Encoding UTF8
  }

  Set-Content (Join-Path $target 'VERSION') '20.0.0' -Encoding ASCII
  @{version='20.0.0';release='Production';name='Simplified Operator Experience'} |
    ConvertTo-Json | Set-Content (Join-Path $target 'docs\version.json') -Encoding UTF8

  Write-Host ''
  Write-Host 'V20.0.0 installed successfully.' -ForegroundColor Green
  Write-Host 'Preserved: data, Git history, 3Commas files, configuration, candidate registry and forward evidence.' -ForegroundColor Green
  Write-Host 'Next: open GitHub Desktop, review the changed files, commit, then Push origin.' -ForegroundColor Yellow
}
finally {
  if(Test-Path $backup){Remove-Item $backup -Recurse -Force}
}
