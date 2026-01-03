#!/bin/bash
# Script to install ffmpeg on macOS with timeout and retry
# Usage: install-ffmpeg-macos.sh <target_dir>
# Example: install-ffmpeg-macos.sh lib/mac

set -e

TARGET_DIR="${1:-lib/mac}"
TIMEOUT_SECONDS=60
URL="https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip"

echo "Downloading and installing ffmpeg for macOS..."

# Function to run command with timeout using Python
run_with_timeout() {
  local timeout=$1
  shift
  python3 -c "
import subprocess
import sys

timeout = $timeout
cmd = \"\"\"$*\"\"\"

try:
    result = subprocess.run(
        cmd,
        shell=True,
        timeout=timeout,
        capture_output=False
    )
    sys.exit(result.returncode)
except subprocess.TimeoutExpired:
    sys.exit(124)
"
}

# Function to attempt download and extraction
attempt_install() {
  local TEMP_DIR=$(mktemp -d)
  cd "$TEMP_DIR"

  if run_with_timeout "$TIMEOUT_SECONDS" wget -q "$URL" -O ffmpeg.zip && \
     run_with_timeout "$TIMEOUT_SECONDS" unzip -q ffmpeg.zip; then
    chmod +x ffmpeg
    mv ffmpeg "$GITHUB_WORKSPACE/$TARGET_DIR/ffmpeg"
    cd "$GITHUB_WORKSPACE"
    chmod -R u+w "$TEMP_DIR" || true
    rm -rf "$TEMP_DIR"
    return 0
  else
    cd "$GITHUB_WORKSPACE"
    chmod -R u+w "$TEMP_DIR" || true
    rm -rf "$TEMP_DIR"
    return 1
  fi
}

# First attempt
if attempt_install; then
  echo "ffmpeg downloaded successfully on first attempt"
else
  echo "First attempt failed or timed out, retrying..."
  # Retry
  if attempt_install; then
    echo "ffmpeg downloaded successfully on second attempt"
  else
    echo "ffmpeg installation failed after 2 attempts"
    exit 1
  fi
fi

# Verify installation
"$GITHUB_WORKSPACE/$TARGET_DIR/ffmpeg" -version | head -n1
echo "ffmpeg installation complete"
