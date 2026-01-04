# Script to install tttool on Windows
# Usage: install-tttool-windows.ps1 <target_dir>
# Example: install-tttool-windows.ps1 lib/win
#          install-tttool-windows.ps1 (installs to PATH for CI)

param(
    [string]$TargetDir = ""
)

$ErrorActionPreference = "Stop"

$TTTOOL_VERSION = "1.8.1"
Write-Host "Installing tttool version $TTTOOL_VERSION for Windows"

# Create temp directory for extraction
$tempDir = New-Item -ItemType Directory -Path (Join-Path $env:TEMP "tttool-temp-$(Get-Random)")
$zipPath = Join-Path $tempDir "tttool.zip"

try {
    # Download tttool
    $url = "https://github.com/entropia/tip-toi-reveng/releases/download/${TTTOOL_VERSION}/tttool-${TTTOOL_VERSION}.zip"
    Write-Host "Downloading from $url"
    Invoke-WebRequest -Uri $url -OutFile $zipPath

    # Extract to temp directory
    Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force

    # Find tttool.exe (may be in subdirectory)
    $tttoolExe = Get-ChildItem -Path $tempDir -Filter "tttool.exe" -Recurse | Select-Object -First 1
    if (-not $tttoolExe) {
        Write-Host "Error: tttool.exe not found in archive"
        exit 1
    }

    if ($TargetDir) {
        # Install to specified directory (for build)
        Write-Host "Installing to $TargetDir"
        New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
        $targetPath = Join-Path $TargetDir "tttool.exe"
        Copy-Item -Path $tttoolExe.FullName -Destination $targetPath -Force

        # Verify
        & $targetPath --help
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: tttool verification failed"
            exit 1
        }
        Write-Host "tttool installed successfully to $targetPath"
    } else {
        # Install to PATH (for CI)
        $binDir = Join-Path $env:RUNNER_TEMP "bin"
        New-Item -ItemType Directory -Force -Path $binDir | Out-Null
        $targetPath = Join-Path $binDir "tttool.exe"
        Copy-Item -Path $tttoolExe.FullName -Destination $targetPath -Force
        Add-Content -Path $env:GITHUB_PATH -Value $binDir

        # Verify
        & $targetPath --help
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: tttool verification failed"
            exit 1
        }
        Write-Host "tttool installed successfully to PATH"
    }
} finally {
    # Cleanup
    if (Test-Path $tempDir) {
        Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
    }
}
