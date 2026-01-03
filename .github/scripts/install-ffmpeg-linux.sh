#!/bin/bash
# Script to install ffmpeg on Linux with timeout and retry
# Usage: install-ffmpeg-linux.sh

set -e

TIMEOUT_SECONDS=60
URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
PATTERN="ffmpeg-*-amd64-static"

echo "Downloading and installing ffmpeg..."

# Try to download and install ffmpeg with timeout
if timeout "$TIMEOUT_SECONDS" wget -q "$URL" && \
   timeout "$TIMEOUT_SECONDS" tar -xf ffmpeg-release-amd64-static.tar.xz; then
  sudo mv ${PATTERN}/ffmpeg /usr/local/bin/
  sudo mv ${PATTERN}/ffprobe /usr/local/bin/
  rm -rf ${PATTERN}*
  echo "ffmpeg installed successfully on first attempt"
else
  echo "First attempt failed or timed out, retrying..."
  # Clean up any partial downloads
  rm -rf ${PATTERN}* 2>/dev/null || true
  # Retry with timeout
  if timeout "$TIMEOUT_SECONDS" wget -q "$URL" && \
     timeout "$TIMEOUT_SECONDS" tar -xf ffmpeg-release-amd64-static.tar.xz; then
    sudo mv ${PATTERN}/ffmpeg /usr/local/bin/
    sudo mv ${PATTERN}/ffprobe /usr/local/bin/
    rm -rf ${PATTERN}*
    echo "ffmpeg installed successfully on second attempt"
  else
    echo "ffmpeg installation failed after 2 attempts"
    exit 1
  fi
fi

# Verify installation
ffmpeg -version | head -n1
echo "ffmpeg installation complete"
