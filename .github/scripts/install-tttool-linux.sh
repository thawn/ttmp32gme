#!/bin/bash
# Script to install tttool on Linux
# Usage: install-tttool-linux.sh <target_dir>
# Example: install-tttool-linux.sh lib/linux
#          install-tttool-linux.sh (installs to /usr/local/bin for CI)

set -e

TARGET_DIR="${1:-}"
TTTOOL_VERSION="1.8.1"

echo "Installing tttool version $TTTOOL_VERSION for Linux"

# Create temp directory for extraction
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download and extract tttool
wget -q "https://github.com/entropia/tip-toi-reveng/releases/download/${TTTOOL_VERSION}/tttool-${TTTOOL_VERSION}.zip"
unzip -q "tttool-${TTTOOL_VERSION}.zip"

# Make binary executable
chmod +x tttool

if [ -n "$TARGET_DIR" ]; then
    # Install to specified directory (for build if needed)
    echo "Installing to $TARGET_DIR"
    mkdir -p "$TARGET_DIR"
    mv tttool "$TARGET_DIR/tttool"

    # Cleanup temp directory
    cd "$GITHUB_WORKSPACE"
    chmod -R u+w "$TEMP_DIR" || true
    rm -rf "$TEMP_DIR"

    # Verify
    "$TARGET_DIR/tttool" --help || {
        echo "Error: tttool installation failed"
        exit 1
    }
    echo "tttool installed successfully to $TARGET_DIR"
else
    # Install to /usr/local/bin (for CI)
    echo "Installing to /usr/local/bin"
    sudo mv tttool /usr/local/bin/

    # Cleanup temp directory
    cd "$GITHUB_WORKSPACE"
    chmod -R u+w "$TEMP_DIR" || true
    rm -rf "$TEMP_DIR"

    # Verify
    tttool --help || {
        echo "Error: tttool installation failed"
        exit 1
    }
    echo "tttool installed successfully to /usr/local/bin"
fi
