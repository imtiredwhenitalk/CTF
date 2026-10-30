# run-local.ps1 — одноразовий сетап PHP + запуск стенду gasstation на localhost
# Запускати з PowerShell (не cmd.exe), з папки проєкту (gasstation/)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # сильно прискорює Invoke-WebRequest
$phpDir = "C:\php"
$zipPath = "$env:TEMP\php.zip"

# Основне посилання — завжди вказує на актуальний патч 8.3.x, без прив'язки до номера версії.
# Резервне — на випадок, якщо перше недоступне (конкретна версія, оновити за потреби з https://windows.php.net/download/).
$urls = @(
    "https://windows.php.net/downloads/releases/latest/php-8.3-nts-Win32-vs16-x64-latest.zip",
    "https://windows.php.net/downloads/releases/php-8.3.33-nts-Win32-vs16-x64.zip"
)

if (-not (Test-Path "$phpDir\php.exe")) {
    $downloaded = $false
    foreach ($url in $urls) {
        try {
            Write-Host "Завантажую PHP з $url ..." -ForegroundColor Cyan
            Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing
            $downloaded = $true
            break
        } catch {
            Write-Host "Не вдалося завантажити з цього посилання, пробую наступне..." -ForegroundColor Yellow
        }
    }

    if (-not $downloaded) {
        Write-Host "`nНе вдалося автоматично завантажити PHP. Завантаж вручну з https://windows.php.net/download/ (Non Thread Safe, x64) і розпакуй у $phpDir" -ForegroundColor Red
        exit 1
    }

    Write-Host "Розпаковую у $phpDir..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path $phpDir | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $phpDir -Force
    Remove-Item $zipPath
} else {
    Write-Host "PHP вже є у $phpDir, пропускаю завантаження." -ForegroundColor Yellow
}

# Додаємо PHP у PATH лише для цієї сесії термінала
$env:Path = "$phpDir;$env:Path"

Write-Host "`nВерсія PHP:" -ForegroundColor Cyan
php -v

Write-Host "`nЗапускаю сервер на http://localhost:8080 ...`n" -ForegroundColor Green
php -S localhost:8080
