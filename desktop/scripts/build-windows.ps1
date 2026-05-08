param(
    [ValidateSet("all", "nsis", "msi")]
    [string]$Bundle = "all"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DesktopDir = Resolve-Path (Join-Path $ScriptDir "..")
$bundleArg = switch ($Bundle) {
    "all" { "nsis,msi" }
    "nsis" { "nsis" }
    "msi" { "msi" }
}

Push-Location $DesktopDir
try {
    if (-not (Test-Path "node_modules")) {
        npm install
    }

    npm run icon
    npx tauri build --bundles $bundleArg
}
finally {
    Pop-Location
}
