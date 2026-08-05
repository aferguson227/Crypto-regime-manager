Set-StrictMode -Version Latest

function Invoke-CRMCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$Command,
        [string[]]$Arguments = @(),
        [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$WorkingDirectory,
        [string]$LogPath
    )

    if (-not (Test-Path -LiteralPath $WorkingDirectory -PathType Container)) {
        throw "Working directory does not exist: $WorkingDirectory"
    }

    Push-Location -LiteralPath $WorkingDirectory
    try {
        $display = "$Command $($Arguments -join ' ')".Trim()
        Write-Host "> $display" -ForegroundColor DarkGray
        if ([string]::IsNullOrWhiteSpace($LogPath)) {
            & $Command @Arguments
        }
        else {
            & $Command @Arguments 2>&1 | Tee-Object -FilePath $LogPath -Append
        }
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }
        if ($exitCode -ne 0) { throw "Command failed ($exitCode): $display" }
    }
    finally {
        Pop-Location
    }
}
