Set-StrictMode -Version Latest
function Invoke-CRMCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Command,
        [string[]]$Arguments = @(),
        [Parameter(Mandatory=$true)][string]$WorkingDirectory,
        [string]$LogPath
    )
    Push-Location $WorkingDirectory
    try {
        $display = "$Command $($Arguments -join ' ')".Trim()
        Write-Host "> $display" -ForegroundColor DarkGray
        if ($LogPath) {
            & $Command @Arguments 2>&1 | Tee-Object -FilePath $LogPath -Append
        } else {
            & $Command @Arguments
        }
        $code = $LASTEXITCODE
        if ($null -eq $code) { $code = 0 }
        if ($code -ne 0) { throw "Command failed ($code): $display" }
    }
    finally { Pop-Location }
}
