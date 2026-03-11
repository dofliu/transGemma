param(
    [switch]$FailOnMojibake
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Test-Utf8File([string]$Path) {
    try {
        $bytes = [System.IO.File]::ReadAllBytes($Path)
        $utf8 = New-Object System.Text.UTF8Encoding($false, $true)
        [void]$utf8.GetString($bytes)
        return $true
    }
    catch {
        return $false
    }
}

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Step "Scanning text files for UTF-8 validity"
$extensions = @("*.py", "*.md", "*.json", "*.toml", "*.txt", "*.yml", "*.yaml", "*.ps1")
$files = foreach ($ext in $extensions) {
    Get-ChildItem -Path $root -Recurse -File -Filter $ext |
        Where-Object {
            $_.FullName -notmatch "\\\.git\\" -and
            $_.FullName -notmatch "\\__pycache__\\" -and
            $_.FullName -notmatch "\\temp\\"
        }
}

$invalidEncoding = @()
foreach ($file in $files) {
    if (-not (Test-Utf8File -Path $file.FullName)) {
        $invalidEncoding += $file.FullName
    }
}

if ($invalidEncoding.Count -gt 0) {
    Write-Host "Found invalid UTF-8 files:" -ForegroundColor Red
    $invalidEncoding | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    exit 1
}
Write-Host "UTF-8 check passed ($($files.Count) files)." -ForegroundColor Green

Write-Step "Scanning for suspicious mojibake markers"
$mojibakeMarkers = @([char]0xFFFD, "Ã", "Â", "ðŸ")
$suspects = @()
foreach ($file in $files) {
    if ($file.FullName -like "*scripts\check_project_health.ps1") {
        continue
    }
    $content = Get-Content -Raw -Path $file.FullName
    foreach ($marker in $mojibakeMarkers) {
        if ($content.Contains($marker)) {
            $suspects += "$($file.FullName) :: marker '$marker'"
            break
        }
    }
}

if ($suspects.Count -gt 0) {
    Write-Host "Potential mojibake markers found ($($suspects.Count) files)." -ForegroundColor Yellow
    $suspects | Select-Object -First 15 | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
    if ($FailOnMojibake) {
        Write-Host "Failing due to -FailOnMojibake." -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "No mojibake markers detected." -ForegroundColor Green
}

Write-Step "Running Python syntax compile check"
$cachePrefix = Join-Path $env:TEMP "tg_pycache_health"
if (Test-Path $cachePrefix) {
    Remove-Item -Recurse -Force $cachePrefix -ErrorAction SilentlyContinue
}
$env:PYTHONPYCACHEPREFIX = $cachePrefix
python -m py_compile app.py translator.py languages.py api.py mcp_server.py
$env:PYTHONPYCACHEPREFIX = ""
if ($LASTEXITCODE -ne 0) {
    Write-Host "py_compile failed." -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "py_compile passed." -ForegroundColor Green

Write-Step "Running smoke tests"
python -m unittest discover -s tests/smoke -p "test_*.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Smoke tests failed." -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Smoke tests passed." -ForegroundColor Green

Write-Step "Project health check completed"
Write-Host "Status: HEALTHY" -ForegroundColor Green
