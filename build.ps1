[CmdletBinding()]
param(
    [switch]$Screenshots,
    [switch]$AllowDirty,
    [string]$ProjectPath = $PSScriptRoot
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
    $ProjectPath = $PSScriptRoot
}
$ProjectPath = [System.IO.Path]::GetFullPath($ProjectPath)

. (Join-Path $PSScriptRoot 'build\Invoke-CRMCommand.ps1')

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$logDir = Join-Path $ProjectPath 'diagnostics_logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$log = Join-Path $logDir "build-$stamp.log"
$reportPath = Join-Path $logDir "build-$stamp.json"
$started = Get-Date
$script:steps = @()
$result = 'fail'
$failure = $null

function Run-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )
    $stepStarted = Get-Date
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    try {
        & $Action
        $script:steps += [pscustomobject]@{
            name = $Name
            status = 'pass'
            seconds = [math]::Round(((Get-Date) - $stepStarted).TotalSeconds, 2)
        }
    }
    catch {
        $script:steps += [pscustomobject]@{
            name = $Name
            status = 'fail'
            seconds = [math]::Round(((Get-Date) - $stepStarted).TotalSeconds, 2)
            error = $_.Exception.Message
        }
        throw
    }
}

try {
    Write-Host 'Crypto Regime Manager Build System 1.0' -ForegroundColor Green
    Write-Host "Project: $ProjectPath"
    Write-Host "Log:     $log"

    Run-Step -Name 'Pre-flight' -Action {
        if (-not (Test-Path -LiteralPath (Join-Path $ProjectPath '.git'))) { throw '.git folder not found' }
        if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python is unavailable' }
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is unavailable' }
        $dirty = (& git -C $ProjectPath status --porcelain | Out-String).Trim()
        if ($dirty -and -not $AllowDirty) { throw 'Repository has uncommitted changes. Commit them or rerun with -AllowDirty.' }
        $versionPath = Join-Path $ProjectPath 'VERSION'
        $version = (Get-Content -LiteralPath $versionPath -Raw).Trim()
        if ($version -ne '32.1.1') { throw "Expected VERSION 32.1.1, found $version" }
    }

    Run-Step -Name 'Python tests' -Action {
        Invoke-CRMCommand -Command 'python' -Arguments @('-m', 'pytest', '-q') -WorkingDirectory $ProjectPath -LogPath $log
    }
    Run-Step -Name 'Publication validation' -Action {
        Invoke-CRMCommand -Command 'python' -Arguments @('scripts\validate_publish.py') -WorkingDirectory $ProjectPath -LogPath $log
    }
    Run-Step -Name 'Python compilation' -Action {
        Invoke-CRMCommand -Command 'python' -Arguments @('-m', 'compileall', '-q', 'app', 'scripts', 'tests') -WorkingDirectory $ProjectPath -LogPath $log
    }
    Run-Step -Name 'Diagnostics and acceptance' -Action {
        $arguments = @('scripts\diagnostics_engine.py', '--full', '--export')
        if ($Screenshots) { $arguments += '--screenshots' }
        Invoke-CRMCommand -Command 'python' -Arguments $arguments -WorkingDirectory $ProjectPath -LogPath $log
    }
    $result = 'pass'
}
catch {
    $result = 'fail'
    $failure = $_.Exception.Message
    Write-Host "`nBUILD FAILED: $failure" -ForegroundColor Red
}
finally {
    $gitCommit = ''
    try { $gitCommit = ((& git -C $ProjectPath rev-parse HEAD 2>$null | Out-String).Trim()) } catch { }
    $report = [ordered]@{
        schema_version = '1.0'
        build_system = 'CRM Build System 1.0'
        version = '32.1.1'
        result = $result
        started_at = $started.ToString('o')
        completed_at = (Get-Date).ToString('o')
        duration_seconds = [math]::Round(((Get-Date) - $started).TotalSeconds, 2)
        git_commit = $gitCommit
        steps = $script:steps
        log = $log
    }
    if ($failure) { $report.failure = $failure }
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    Write-Host "Build report: $reportPath"
}

if ($result -ne 'pass') { exit 1 }
Write-Host "`nBUILD PASSED - release packaging is permitted." -ForegroundColor Green
exit 0
