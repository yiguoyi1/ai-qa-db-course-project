[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Username,
    [Parameter(Mandatory = $true)]
    [string]$Password,
    [string]$ApiHost = "127.0.0.1",
    [int]$Port = 8001,
    [switch]$SkipApiStart,
    [switch]$WriteSmoke
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$BaseUrl = "http://$ApiHost`:$Port"
$HealthUrl = "$BaseUrl/health"
$StartedProcess = $null

function Test-ApiHealthy {
    param(
        [Parameter(Mandatory = $true)]
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
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [int]$TimeoutSeconds = 30
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-ApiHealthy -Url $Url) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }

    return $false
}

function Invoke-ApiJson {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Method,
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [object]$Body,
        [string]$Token
    )

    $params = @{
        Uri         = "$BaseUrl$Path"
        Method      = $Method
        TimeoutSec  = 30
        ErrorAction = "Stop"
    }

    if (-not [string]::IsNullOrWhiteSpace($Token)) {
        $params.Headers = @{
            Authorization = "Bearer $Token"
        }
    }

    if ($null -ne $Body) {
        $params.ContentType = "application/json"
        $params.Body = ($Body | ConvertTo-Json -Depth 10)
    }

    return Invoke-RestMethod @params
}

try {
    if (-not $SkipApiStart) {
        if (Test-ApiHealthy -Url $HealthUrl) {
            Write-Host "Detected running API at $BaseUrl, reusing it."
            Write-Host "If you recently changed code, consider testing on a fresh port."
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

    Write-Host "Logging in as $Username ..."
    $loginResponse = Invoke-ApiJson `
        -Method "POST" `
        -Path "/api/auth/login" `
        -Body @{
            username = $Username
            password = $Password
        }

    if ($loginResponse.role -ne "ADMIN") {
        throw "User '$Username' is not an ADMIN. Run .\scripts\grant-admin.ps1 -Username $Username first."
    }

    $token = $loginResponse.access_token
    $userId = [int]$loginResponse.user_id

    Write-Host "Checking admin users ..."
    $adminUsers = Invoke-ApiJson `
        -Method "GET" `
        -Path "/api/admin/users?role=ADMIN&page=1&page_size=10" `
        -Token $token

    Write-Host "Checking categories ..."
    $categories = Invoke-ApiJson `
        -Method "GET" `
        -Path "/api/admin/categories?page=1&page_size=10" `
        -Token $token

    Write-Host "Checking login logs ..."
    $loginLogs = Invoke-ApiJson `
        -Method "GET" `
        -Path "/api/admin/logs/login?user_id=$userId&page=1&page_size=10" `
        -Token $token

    Write-Host "Checking operation logs ..."
    $operationLogs = Invoke-ApiJson `
        -Method "GET" `
        -Path "/api/admin/logs/operations?user_id=$userId&page=1&page_size=10" `
        -Token $token

    $summary = [ordered]@{
        base_url              = $BaseUrl
        username              = $Username
        user_id               = $userId
        role                  = $loginResponse.role
        admin_users_total     = [int]$adminUsers.total
        categories_total      = [int]$categories.total
        login_logs_total      = [int]$loginLogs.total
        operation_logs_total  = [int]$operationLogs.total
        write_smoke_executed  = [bool]$WriteSmoke
    }

    if ($WriteSmoke) {
        $timestamp = Get-Date -Format "yyyyMMddHHmmss"
        $categoryName = "zz_admin_smoke_$timestamp"

        Write-Host "Running write smoke with temporary category $categoryName ..."
        $createdCategory = Invoke-ApiJson `
            -Method "POST" `
            -Path "/api/admin/categories" `
            -Body @{
                category_name = $categoryName
                description   = "temporary category created by admin smoke test"
                status        = "ACTIVE"
            } `
            -Token $token

        $updatedCategory = Invoke-ApiJson `
            -Method "PATCH" `
            -Path "/api/admin/categories/$($createdCategory.category_id)" `
            -Body @{
                description = "temporary category updated by admin smoke test"
                status      = "INACTIVE"
            } `
            -Token $token

        $summary.created_category_id = [int]$createdCategory.category_id
        $summary.created_category_name = $createdCategory.category_name
        $summary.updated_category_status = $updatedCategory.status

        $operationLogsAfterWrite = Invoke-ApiJson `
            -Method "GET" `
            -Path "/api/admin/logs/operations?user_id=$userId&page=1&page_size=20" `
            -Token $token

        $operationActions = @($operationLogsAfterWrite.items | ForEach-Object { $_.op_type })
        $summary.operation_logs_total_after_write = [int]$operationLogsAfterWrite.total
        $summary.has_create_category_log = $operationActions -contains "ADMIN_CREATE_CATEGORY"
        $summary.has_update_category_log = $operationActions -contains "ADMIN_UPDATE_CATEGORY"
    }

    Write-Host ""
    Write-Host "Admin API smoke test completed successfully."
    $summary | ConvertTo-Json -Depth 10
}
finally {
    if ($null -ne $StartedProcess -and -not $StartedProcess.HasExited) {
        Write-Host "Stopping API process started by this script ..."
        Stop-Process -Id $StartedProcess.Id
    }
}
