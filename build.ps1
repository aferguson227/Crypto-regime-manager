[CmdletBinding()]
param(
    [switch]$Screenshots,
    [switch]$AllowDirty,
    [string]$ProjectPath = ""
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
if([string]::IsNullOrWhiteSpace($ProjectPath)){ $ProjectPath = Split-Path -Parent $MyInvocation.MyCommand.Path }
$failure=$null
$result='fail'
. (Join-Path $ProjectPath 'build\Invoke-CRMCommand.ps1')
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$logDir=Join-Path $ProjectPath 'diagnostics_logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$log=Join-Path $logDir "build-$stamp.log"
$reportPath=Join-Path $logDir "build-$stamp.json"
$started=Get-Date
$steps=@()
function Run-Step([string]$Name,[scriptblock]$Action){
    $s=Get-Date; Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    try { & $Action; $steps += [pscustomobject]@{name=$Name;status='pass';seconds=[math]::Round(((Get-Date)-$s).TotalSeconds,2)} }
    catch { $steps += [pscustomobject]@{name=$Name;status='fail';seconds=[math]::Round(((Get-Date)-$s).TotalSeconds,2);error=$_.Exception.Message}; throw }
}
try {
    Write-Host 'Crypto Regime Manager Build System 1.0' -ForegroundColor Green
    Write-Host "Project: $ProjectPath"
    Write-Host "Log:     $log"
    Run-Step 'Pre-flight' {
        if(-not(Test-Path (Join-Path $ProjectPath '.git'))){throw '.git folder not found'}
        if(-not(Get-Command python -ErrorAction SilentlyContinue)){throw 'Python is unavailable'}
        if(-not(Get-Command git -ErrorAction SilentlyContinue)){throw 'Git is unavailable'}
        $dirty=(& git -C $ProjectPath status --porcelain | Out-String).Trim()
        if($dirty -and -not $AllowDirty){throw 'Repository has uncommitted changes. Commit them or rerun with -AllowDirty.'}
        $v=(Get-Content (Join-Path $ProjectPath 'VERSION') -Raw).Trim()
        if($v -ne '32.3.0'){throw "Expected VERSION 32.3.0, found $v"}
    }
    Run-Step 'Python tests' { Invoke-CRMCommand -Command 'python' -Arguments @('-m','pytest','-q') -WorkingDirectory $ProjectPath -LogPath $log }
    Run-Step 'Publication validation' { Invoke-CRMCommand -Command 'python' -Arguments @('scripts\validate_publish.py') -WorkingDirectory $ProjectPath -LogPath $log }
    Run-Step 'Python compilation' { Invoke-CRMCommand -Command 'python' -Arguments @('-m','compileall','-q','app','scripts','tests') -WorkingDirectory $ProjectPath -LogPath $log }
    Run-Step 'Diagnostics and acceptance' {
        $a=@('scripts\diagnostics_engine.py','--full','--export')
        if($Screenshots){$a += '--screenshots'}
        Invoke-CRMCommand -Command 'python' -Arguments $a -WorkingDirectory $ProjectPath -LogPath $log
    }
    $result='pass'
}
catch {
    $result='fail'; $failure=$_.Exception.Message
    Write-Host "`nBUILD FAILED: $failure" -ForegroundColor Red
}
finally {
    $report=[ordered]@{
        schema_version='1.0'; build_system='CRM Build System 1.0'; version='32.3.0'; result=$result
        started_at=$started.ToString('o'); completed_at=(Get-Date).ToString('o')
        duration_seconds=[math]::Round(((Get-Date)-$started).TotalSeconds,2)
        git_commit=((& git -C $ProjectPath rev-parse HEAD 2>$null | Out-String).Trim())
        steps=$steps; log=$log
    }
    if($failure){$report.failure=$failure}
    $report | ConvertTo-Json -Depth 8 | Set-Content -Path $reportPath -Encoding UTF8
    Write-Host "Build report: $reportPath"
}
if($result -ne 'pass'){exit 1}
Write-Host "`nBUILD PASSED - release packaging is permitted." -ForegroundColor Green
exit 0
