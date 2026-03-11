param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not ($Version -match '^v\d+\.\d+\.\d+$')) {
    throw "Version must match format vX.Y.Z (example: v1.0.0)"
}

Write-Step "Running health gate before packaging"
powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\check_project_health.ps1" -FailOnMojibake
if ($LASTEXITCODE -ne 0) {
    throw "Health gate failed; packaging aborted."
}

$distDir = Join-Path $root "dist"
if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$artifactName = "translategemma-$Version-$timestamp.zip"
$artifactPath = Join-Path $distDir $artifactName

$stagingDir = Join-Path $env:TEMP "translategemma_release_$timestamp"
if (Test-Path $stagingDir) {
    Remove-Item -Recurse -Force $stagingDir
}
New-Item -ItemType Directory -Path $stagingDir | Out-Null

Write-Step "Collecting release files"
$include = @(
    "app.py",
    "api.py",
    "mcp_server.py",
    "translator.py",
    "meeting_summarizer.py",
    "video_dubber.py",
    "languages.py",
    "history.py",
    "README.md",
    "requirements.txt",
    "LICENSE",
    "docs",
    "scripts",
    "tests\smoke",
    "datasets\eval",
    "tools"
)

foreach ($entry in $include) {
    $src = Join-Path $root $entry
    if (Test-Path $src) {
        Copy-Item -Recurse -Force $src $stagingDir
    }
}

Write-Step "Creating zip artifact"
if (Test-Path $artifactPath) {
    Remove-Item -Force $artifactPath
}
Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $artifactPath

Write-Step "Cleaning staging directory"
Remove-Item -Recurse -Force $stagingDir

$hash = (Get-FileHash $artifactPath -Algorithm SHA256).Hash

Write-Host "`nRelease package created:" -ForegroundColor Green
Write-Host " - Path: $artifactPath" -ForegroundColor Green
Write-Host " - SHA256: $hash" -ForegroundColor Green
