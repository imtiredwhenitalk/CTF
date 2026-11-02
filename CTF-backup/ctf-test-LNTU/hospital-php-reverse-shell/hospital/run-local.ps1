# run-local.ps1 -- one-time PHP setup + run the "hospital" stand on localhost
# Run from PowerShell (not cmd.exe), from the project root.
#
# NOTE: kept ASCII-only on purpose. Windows PowerShell 5.1 (powershell.exe)
# reads .ps1 files using the system codepage unless the file has a UTF-8
# BOM; a non-ASCII (e.g. Cyrillic) script saved/transferred without a BOM
# can get misread and produce confusing parser errors like
# "Missing closing '}' in statement block" at an unrelated line.

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # speeds up Invoke-WebRequest a lot
$phpDir = "C:\php"
$zipPath = "$env:TEMP\php.zip"

# Primary link always points at the latest 8.3.x patch, no version pinning.
# Fallback is a specific version, in case the first is unavailable
# (update as needed from https://windows.php.net/download/).
$urls = @(
    "https://windows.php.net/downloads/releases/latest/php-8.3-nts-Win32-vs16-x64-latest.zip",
    "https://windows.php.net/downloads/releases/php-8.3.33-nts-Win32-vs16-x64.zip"
)

if (-not (Test-Path "$phpDir\php.exe")) {
    $downloaded = $false
    foreach ($url in $urls) {
        try {
            Write-Host "Downloading PHP from $url ..." -ForegroundColor Cyan
            Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing
            $downloaded = $true
            break
        } catch {
            Write-Host "Could not download from this link, trying the next one..." -ForegroundColor Yellow
        }
    }

    if (-not $downloaded) {
        Write-Host "`nCould not download PHP automatically. Download it manually from https://windows.php.net/download/ (Non Thread Safe, x64) and unzip it into $phpDir" -ForegroundColor Red
        exit 1
    }

    Write-Host "Extracting to $phpDir..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path $phpDir | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $phpDir -Force
    Remove-Item $zipPath
} else {
    Write-Host "PHP already present at $phpDir, skipping download." -ForegroundColor Yellow
}

# Add PHP to PATH for this terminal session only
$env:Path = "$phpDir;$env:Path"

Write-Host "`nPHP version:" -ForegroundColor Cyan
php -v

# Note: when running with the built-in PHP server (no Docker), the whole
# repo -- including data/flag.txt -- technically sits next to it on disk.
# For a real "outside the web root" isolation use Docker (docker-compose
# up), where the container's web root is restricted to app/public.
Write-Host "`nStarting server at http://localhost:8080 (docroot: app/public) ...`n" -ForegroundColor Green
php -S localhost:8080 -t app/public