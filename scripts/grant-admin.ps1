[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Username,
    [string]$ContainerName = "oracle26ai",
    [string]$ServiceName = "FREEPDB1"
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

if (-not (Test-CommandExists -Name "docker")) {
    throw "Docker CLI is not installed or not on PATH."
}

$envFile = Join-Path $RepoRoot ".env"
$appUser = Get-DotEnvValue -Path $envFile -Key "APP_USER"
$appPassword = Get-DotEnvValue -Path $envFile -Key "APP_USER_PASSWORD"

if ([string]::IsNullOrWhiteSpace($appUser) -or [string]::IsNullOrWhiteSpace($appPassword)) {
    throw "APP_USER and APP_USER_PASSWORD must be set in .env before granting admin role."
}

$escapedPassword = $appPassword.Replace('"', '""')
$escapedUsername = $Username.Replace("'", "''")

$sqlplusInput = @"
WHENEVER SQLERROR EXIT SQL.SQLCODE
CONNECT $appUser/"$escapedPassword"@//localhost:1521/$ServiceName
DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM users
     WHERE username = '$escapedUsername';

    IF l_count = 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'User not found: $escapedUsername');
    END IF;

    UPDATE users
       SET role = 'ADMIN',
           status = 'ACTIVE'
     WHERE username = '$escapedUsername';

    COMMIT;
END;
/
EXIT
"@

Write-Host "Granting ADMIN role to user '$Username' ..."
$sqlplusInput | docker exec -i $ContainerName sqlplus -L -s /nolog

if ($LASTEXITCODE -ne 0) {
    throw "Failed to grant ADMIN role to '$Username'."
}

Write-Host "User '$Username' is now an ACTIVE ADMIN."
