# Script to install Chrome and ChromeDriver on Windows
# Usage: install-chrome-windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "Installing Chrome and ChromeDriver for Windows"

# Install Chrome using Chocolatey
Write-Host "Installing Chrome via Chocolatey..."
choco install googlechrome -y --ignore-checksums

# Find Chrome installation (check multiple common paths)
$chromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)

$chromePath = $null
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        $chromePath = $path
        break
    }
}

if (-not $chromePath) {
    Write-Host "Error: Chrome installation not found"
    exit 1
}

# Get Chrome version and download matching ChromeDriver
$chromeVersion = (Get-Item $chromePath).VersionInfo.ProductVersion
$majorVersion = $chromeVersion.Split('.')[0]
Write-Host "Chrome version: $chromeVersion (found at: $chromePath)"

# Get ChromeDriver download URL for Windows
Write-Host "Downloading ChromeDriver..."
$json = Invoke-RestMethod -Uri "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
$driverUrl = ($json.channels.Stable.downloads.chromedriver | Where-Object { $_.platform -eq "win64" }).url

# Download and extract ChromeDriver
$tempDir = New-Item -ItemType Directory -Path (Join-Path $env:TEMP "chromedriver-temp-$(Get-Random)")
$zipPath = Join-Path $tempDir "chromedriver.zip"
Invoke-WebRequest -Uri $driverUrl -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force

# Move chromedriver to a location in PATH
$binDir = Join-Path $env:RUNNER_TEMP "bin"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null
Copy-Item -Path (Join-Path $tempDir "chromedriver-win64\chromedriver.exe") -Destination (Join-Path $binDir "chromedriver.exe") -Force
Add-Content -Path $env:GITHUB_PATH -Value $binDir

# Cleanup
Remove-Item -Recurse -Force $tempDir

Write-Host "ChromeDriver installed successfully"
