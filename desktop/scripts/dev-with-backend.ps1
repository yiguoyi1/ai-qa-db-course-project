param(
    [string]$BackendUrl = $env:AI_QA_BACKEND_URL
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($BackendUrl)) {
    $BackendUrl = "http://127.0.0.1:8000"
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DesktopDir = Resolve-Path (Join-Path $ScriptDir "..")
$ProjectRoot = Resolve-Path (Join-Path $DesktopDir "..")
$backendProcess = $null

function Test-Backend {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri "$Url/health" -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
    }
    catch {
        return $false
    }
}

try {
    if (-not (Test-Backend -Url $BackendUrl)) {
        Write-Host "Starting FastAPI backend at $BackendUrl"
        Push-Location $ProjectRoot
        try {
            $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
            $python = if (Test-Path $venvPython) { $venvPython } else { "python" }
            $backendProcess = Start-Process -FilePath $python -ArgumentList @(
                "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"
            ) -PassThru -NoNewWindow

            for ($i = 0; $i -lt 40; $i++) {
                if (Test-Backend -Url $BackendUrl) {
                    break
                }
                Start-Sleep -Milliseconds 500
            }
        }
        finally {
            Pop-Location
        }
    }

    Push-Location $DesktopDir
    try {
        npm run dev
    }
    finally {
        Pop-Location
    }
}
finally {
    if ($null -ne $backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
