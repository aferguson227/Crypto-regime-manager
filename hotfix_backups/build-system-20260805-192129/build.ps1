[CmdletBinding()]
param(
    [switch]$Screenshots,
    [switch]$AllowDirty,
    [string]$ProjectPath = $PSScriptRoot
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
. (Join-Path $PSScriptRoot 'build\Invoke-CRMCommand.ps1')
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
        if($v -ne '32.1.1'){throw "Expected VERSION 32.1.1, found $v"}
    }
    Run-Step 'Python tests' { Invoke-CRMCommand python @('-m','pytest','-q') $ProjectPath $log }
    Run-Step 'Publication validation' { Invoke-CRMCommand python @('scripts\validate_publish.py') $ProjectPath $log }
    Run-Step 'Python compilation' { Invoke-CRMCommand python @('-m','compileall','-q','app','scripts','tests') $ProjectPath $log }
    Run-Step 'Diagnostics and acceptance' {
        $a=@('scripts\diagnostics_engine.py','--full','--export')
        if($Screenshots){$a += '--screenshots'}
        Invoke-CRMCommand python $a $ProjectPath $log
    }
    $result='pass'
}
catch {
    $result='fail'; $failure=$_.Exception.Message
    Write-Host "`nBUILD FAILED: $failure" -ForegroundColor Red
}
finally {
    $report=[ordered]@{
        schema_version='1.0'; build_system='CRM Build System 1.0'; version='32.1.1'; result=$result
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
