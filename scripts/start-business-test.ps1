param(
    [string]$ApiHost = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$SkipApiStart
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$BaseUrl = "http://$ApiHost`:$Port"
$HealthUrl = "$BaseUrl/health"
$StartedProcess = $null

function Test-ApiHealthy {
    param(
        [string]$Url
    )

    try {
        $response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 3
        return $response.status -eq "ok"
    }
    catch {
        return $false
    }
}

function Wait-ApiReady {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 30
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-ApiHealthy -Url $Url) {
            return $true
        }
        Start-Sleep -Seconds 1
    }

    return $false
}

try {
    if (-not $SkipApiStart) {
        if (Test-ApiHealthy -Url $HealthUrl) {
            Write-Host "Detected running API at $BaseUrl, reusing it."
        }
        else {
            Write-Host "Starting API at $BaseUrl ..."
            $StartedProcess = Start-Process python `
                -ArgumentList "-m", "uvicorn", "app.main:app", "--host", $ApiHost, "--port", $Port `
                -WorkingDirectory $RepoRoot `
                -PassThru

            if (-not (Wait-ApiReady -Url $HealthUrl -TimeoutSeconds 30)) {
                throw "API did not become healthy within 30 seconds."
            }
        }
    }
    elseif (-not (Test-ApiHealthy -Url $HealthUrl)) {
        throw "SkipApiStart was set, but the API is not reachable at $BaseUrl."
    }

    Write-Host "Opening business test menu ..."
    python -m frontend_cli.main --base-url $BaseUrl menu
}
finally {
    if ($null -ne $StartedProcess -and -not $StartedProcess.HasExited) {
        Write-Host "Stopping API process started by this script ..."
        Stop-Process -Id $StartedProcess.Id
    }
}
