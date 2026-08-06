[CmdletBinding()]
param([switch]$NoScreenshots)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogDir = Join-Path $Root "diagnostics_logs"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
$Log = Join-Path $LogDir "diagnostics-$Stamp.log"
Start-Transcript -Path $Log -Force | Out-Null
try {
  Set-Location $Root
  Write-Host "Running full diagnostics and acceptance checks..." -ForegroundColor Cyan
  $args = @("scripts\diagnostics_engine.py", "--full", "--export")
  if (-not $NoScreenshots) { $args += "--screenshots" }
  & python @args
  $code = $LASTEXITCODE
  $latest = Get-ChildItem (Join-Path $Root "diagnostics_exports\CRM_Diagnostics_*.zip") -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($latest) {
    Write-Host "Review package: $($latest.FullName)" -ForegroundColor Green
    Start-Process explorer.exe "/select,`"$($latest.FullName)`""
  }
  exit $code
}
finally { try { Stop-Transcript | Out-Null } catch {} }
