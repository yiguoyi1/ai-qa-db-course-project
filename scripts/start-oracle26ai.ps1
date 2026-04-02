[CmdletBinding()]
param(
    [string]$ComposeFile = "compose.yaml",
    [string]$ServiceName = "oracle26ai",
    [string]$ContainerName = "oracle26ai",
    [int]$TimeoutSeconds = 900
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

if (-not [System.IO.Path]::IsPathRooted($ComposeFile)) {
    $ComposeFile = Join-Path $RepoRoot $ComposeFile
}

function Test-CommandExists {
    param([Parameter(Mandatory = $true)][string]$Name)

    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

if (-not (Test-Path -LiteralPath $ComposeFile)) {
    throw "Compose file not found: $ComposeFile"
}

if (-not (Test-CommandExists -Name "docker")) {
    throw "Docker CLI is not installed or not on PATH."
}

Write-Host "Starting Oracle 26ai container with docker compose..."
docker compose -f $ComposeFile up -d $ServiceName
if ($LASTEXITCODE -ne 0) {
    throw "docker compose up failed."
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)

while ((Get-Date) -lt $deadline) {
    $status = docker inspect -f "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" $ContainerName 2>$null

    if ($LASTEXITCODE -eq 0) {
        $status = $status.Trim()
        Write-Host "Container status: $status"

        if ($status -eq "healthy" -or $status -eq "running") {
            Write-Host "Oracle 26ai container is ready."
            exit 0
        }
    }

    Start-Sleep -Seconds 10
}

throw "Timed out waiting for container '$ContainerName' to become ready."
