# Script to install ffmpeg on Windows with timeout and retry
# Usage: install-ffmpeg-windows.ps1

$ErrorActionPreference = "Stop"

$TIMEOUT_SECONDS = 120
$URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

Write-Host "Downloading and installing ffmpeg for Windows..."

# Function to install ffmpeg with timeout
function Install-Ffmpeg {
    param([int]$TimeoutSeconds = 120)

    $tempDir = New-Item -ItemType Directory -Path (Join-Path $env:TEMP "ffmpeg-temp-$(Get-Random)")
    $zipPath = Join-Path $tempDir "ffmpeg.zip"

    try {
        # Download with timeout
        Write-Host "Downloading ffmpeg..."
        $job = Start-Job -ScriptBlock {
            param($url, $zipPath)
            Invoke-WebRequest -Uri $url -OutFile $zipPath
        } -ArgumentList $URL, $zipPath

        if (Wait-Job -Job $job -Timeout $TimeoutSeconds) {
            Receive-Job -Job $job
            Remove-Job -Job $job -Force

            # Extract with timeout
            Write-Host "Extracting ffmpeg..."
            $extractJob = Start-Job -ScriptBlock {
                param($zipPath, $tempDir)
                Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force
            } -ArgumentList $zipPath, $tempDir

            if (Wait-Job -Job $extractJob -Timeout $TimeoutSeconds) {
                Receive-Job -Job $extractJob
                Remove-Job -Job $extractJob -Force

                # Find and move ffmpeg.exe to PATH
                $ffmpegDir = Get-ChildItem -Path $tempDir -Directory -Filter "ffmpeg-*" | Select-Object -First 1
                $ffmpegExe = Join-Path $ffmpegDir.FullName "bin/ffmpeg.exe"

                # Copy to a location in PATH (using GitHub Actions runner's bin directory)
                if ($env:GITHUB_PATH) {
                    # In GitHub Actions, add to GITHUB_PATH
                    $binDir = Join-Path $env:RUNNER_TEMP "bin"
                    New-Item -ItemType Directory -Force -Path $binDir | Out-Null
                    Copy-Item -Path $ffmpegExe -Destination (Join-Path $binDir "ffmpeg.exe") -Force
                    Add-Content -Path $env:GITHUB_PATH -Value $binDir
                    Write-Host "Added $binDir to PATH via GITHUB_PATH"
                } else {
                    # For local testing, copy to system PATH location
                    $systemBin = "C:\Windows\System32"
                    Copy-Item -Path $ffmpegExe -Destination (Join-Path $systemBin "ffmpeg.exe") -Force
                }

                return $true
            } else {
                Stop-Job -Job $extractJob
                Remove-Job -Job $extractJob -Force
                return $false
            }
        } else {
            Stop-Job -Job $job
            Remove-Job -Job $job -Force
            return $false
        }
    } finally {
        # Cleanup temp directory
        if (Test-Path $tempDir) {
            Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
        }
    }
}

# First attempt
Write-Host "Attempting to download ffmpeg (attempt 1)..."
if (Install-Ffmpeg -TimeoutSeconds $TIMEOUT_SECONDS) {
    Write-Host "ffmpeg installed successfully on first attempt"
} else {
    Write-Host "First attempt failed or timed out, retrying..."

    # Clean up any stale temp directories
    Get-ChildItem -Path $env:TEMP -Directory -Filter "ffmpeg-temp-*" -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    # Retry
    Write-Host "Attempting to download ffmpeg (attempt 2)..."
    if (Install-Ffmpeg -TimeoutSeconds $TIMEOUT_SECONDS) {
        Write-Host "ffmpeg installed successfully on second attempt"
    } else {
        Write-Host "ffmpeg installation failed after 2 attempts"
        exit 1
    }
}

# Verify installation
ffmpeg -version | Select-Object -First 1
Write-Host "ffmpeg installation complete"
