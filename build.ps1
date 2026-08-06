[CmdletBinding()]
param(
    [switch]$Screenshots,
    [switch]$AllowDirty,
    [string]$ProjectPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
    $ProjectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$failure = $null
$result = 'fail'
$v = $null

. (Join-Path $ProjectPath 'build\Invoke-CRMCommand.ps1')

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$logDir = Join-Path $ProjectPath 'diagnostics_logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$log = Join-Path $logDir "build-$stamp.log"
$reportPath = Join-Path $logDir "build-$stamp.json"
$started = Get-Date
$script:steps = @()

function Run-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
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
    Write-Host 'Crypto Regime Manager Build System 2.0' -ForegroundColor Green
    Write-Host "Project: $ProjectPath"
    Write-Host "Log:     $log"

    Run-Step -Name 'Pre-flight' -Action {
        if (-not (Test-Path (Join-Path $ProjectPath '.git'))) {
            throw '.git folder not found'
        }
        if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
            throw 'Python is unavailable'
        }
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            throw 'Git is unavailable'
        }

        foreach ($generated in @('docs/diagnostics.json')) { & git -C $ProjectPath restore --worktree -- $generated 2>$null }
        $dirty = (& git -C $ProjectPath status --porcelain | Out-String).Trim()
        if ($dirty -and -not $AllowDirty) {
            throw 'Repository has uncommitted changes. Commit them or rerun with -AllowDirty.'
        }

        $versionPath = Join-Path $ProjectPath 'VERSION'
        if (-not (Test-Path $versionPath)) {
            throw 'VERSION file is missing.'
        }

        $script:v = (Get-Content $versionPath -Raw).Trim()
        if ([string]::IsNullOrWhiteSpace($script:v)) {
            throw 'VERSION file is empty.'
        }
    }

    Run-Step -Name 'Python tests' -Action {
        Invoke-CRMCommand -Command 'python' -Arguments @('-m', 'pytest', '-q') -WorkingDirectory $ProjectPath -LogPath $log
    }

    Run-Step -Name 'Publication validation' -Action {
        Invoke-CRMCommand -Command 'python' -Arguments @('scripts\validate_publish.py') -WorkingDirectory $ProjectPath -LogPath $log
    }

    Run-Step -Name 'Release metadata validation' -Action {
        Invoke-CRMCommand -Command 'python' -Arguments @('scripts\validate_release_metadata.py') -WorkingDirectory $ProjectPath -LogPath $log
    }

    Run-Step -Name 'Python compilation' -Action {
        Invoke-CRMCommand -Command 'python' -Arguments @('-m', 'compileall', '-q', 'app', 'scripts', 'tests') -WorkingDirectory $ProjectPath -LogPath $log
    }

    Run-Step -Name 'Diagnostics and acceptance' -Action {
        $arguments = @('scripts\diagnostics_engine.py', '--full', '--export')
        if ($Screenshots) {
            $arguments += '--screenshots'
        }
        Invoke-CRMCommand -Command 'python' -Arguments $arguments -WorkingDirectory $ProjectPath -LogPath $log
        # diagnostics.json is a generated acceptance artefact; leave the source tree clean.
        & git -C $ProjectPath restore --worktree -- 'docs/diagnostics.json' 2>$null
        if ($LASTEXITCODE -ne 0) { throw 'Could not restore generated docs/diagnostics.json.' }
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
    try {
        $gitCommit = (& git -C $ProjectPath rev-parse HEAD 2>$null | Out-String).Trim()
    }
    catch {
        $gitCommit = ''
    }

    $report = [ordered]@{
        schema_version = '1.0'
        build_system = 'CRM Build System 2.0'
        version = $v
        result = $result
        started_at = $started.ToString('o')
        completed_at = (Get-Date).ToString('o')
        duration_seconds = [math]::Round(((Get-Date) - $started).TotalSeconds, 2)
        git_commit = $gitCommit
        steps = $script:steps
        log = $log
    }

    if ($failure) {
        $report.failure = $failure
    }

    $report | ConvertTo-Json -Depth 8 | Set-Content -Path $reportPath -Encoding UTF8
    Write-Host "Build report: $reportPath"
}

if ($result -ne 'pass') {
    exit 1
}

Write-Host "`nBUILD PASSED - release packaging is permitted." -ForegroundColor Green
exit 0
