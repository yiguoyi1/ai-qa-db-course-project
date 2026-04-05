[CmdletBinding()]
param(
    [string]$ContainerName = "oracle26ai",
    [string]$ServiceName = "FREEPDB1",
    [string]$SqlFile = "sql/seed_data.sql"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

function Test-CommandExists {
    param([Parameter(Mandatory = $true)][string]$Name)

    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-DotEnvValue {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Key
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -match "^\s*$" -or $line -match "^\s*#") {
            continue
        }

        $parts = $line.Split("=", 2)
        if ($parts.Count -eq 2 -and $parts[0].Trim() -eq $Key) {
            return $parts[1].Trim()
        }
    }

    return $null
}

function Wait-ContainerHealthy {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [int]$TimeoutSeconds = 300
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        $status = docker inspect -f "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" $Name 2>$null
        if ($LASTEXITCODE -eq 0) {
            $status = $status.Trim()
            if ($status -eq "healthy" -or $status -eq "running") {
                return
            }
        }

        Start-Sleep -Seconds 5
    }

    throw "Timed out waiting for container '$Name' to become healthy."
}

if (-not (Test-CommandExists -Name "docker")) {
    throw "Docker CLI is not installed or not on PATH."
}

$envFile = Join-Path $RepoRoot ".env"
$appUser = Get-DotEnvValue -Path $envFile -Key "APP_USER"
$appPassword = Get-DotEnvValue -Path $envFile -Key "APP_USER_PASSWORD"

if ([string]::IsNullOrWhiteSpace($appUser) -or [string]::IsNullOrWhiteSpace($appPassword)) {
    throw "APP_USER and APP_USER_PASSWORD must be set in .env before loading demo data."
}

if (-not [System.IO.Path]::IsPathRooted($SqlFile)) {
    $SqlFile = Join-Path $RepoRoot $SqlFile
}

if (-not (Test-Path -LiteralPath $SqlFile)) {
    throw "Seed SQL file not found: $SqlFile"
}

Wait-ContainerHealthy -Name $ContainerName

$fileName = Split-Path -Path $SqlFile -Leaf
$containerPath = "/tmp/$fileName"

Write-Host "Copying $SqlFile to container..."
docker cp $SqlFile "${ContainerName}:$containerPath"
if ($LASTEXITCODE -ne 0) {
    throw "docker cp failed for $SqlFile"
}

Write-Host "Executing $SqlFile as $appUser on $ServiceName..."
$escapedPassword = $appPassword.Replace('"', '""')
$sqlplusInput = @"
WHENEVER SQLERROR EXIT SQL.SQLCODE
CONNECT $appUser/"$escapedPassword"@//localhost:1521/$ServiceName
@$containerPath
EXIT
"@

$sqlplusInput | docker exec -i $ContainerName sqlplus -L -s /nolog
if ($LASTEXITCODE -ne 0) {
    throw "sqlplus execution failed for $SqlFile"
}

Write-Host "Persistent demo data load completed successfully."
