#!/bin/bash
# Script to install tttool on macOS
# Usage: install-tttool-macos.sh <target_dir>
# Example: install-tttool-macos.sh lib/mac
#          install-tttool-macos.sh (installs to /usr/local/bin for CI)

set -e

TARGET_DIR="${1:-}"
TTTOOL_VERSION="1.11"

echo "Installing tttool version $TTTOOL_VERSION for macOS"

# Create temp directory for extraction
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download and extract tttool
wget -q "https://github.com/entropia/tip-toi-reveng/releases/download/${TTTOOL_VERSION}/tttool-${TTTOOL_VERSION}.zip"
unzip -q "tttool-${TTTOOL_VERSION}.zip"
cd "tttool-${TTTOOL_VERSION}/osx"

# Make binary executable
chmod +x tttool

if [ -n "$TARGET_DIR" ]; then
    # Install to specified directory (for build)
    echo "Installing to $TARGET_DIR"
    mkdir -p "$GITHUB_WORKSPACE/$TARGET_DIR"
    mv tttool "$GITHUB_WORKSPACE/$TARGET_DIR/tttool"

    # Copy all .dylib files if they exist
    if ls *.dylib 1> /dev/null 2>&1; then
        mv *.dylib "$GITHUB_WORKSPACE/$TARGET_DIR/"
    fi

    # Cleanup temp directory
    cd "$GITHUB_WORKSPACE"
    chmod -R u+w "$TEMP_DIR" || true
    rm -rf "$TEMP_DIR"

    # Verify
    "$GITHUB_WORKSPACE/$TARGET_DIR/tttool" --help || {
        echo "Error: tttool installation failed"
        exit 1
    }
    echo "tttool installed successfully to $TARGET_DIR"
else
    # Install to /usr/local/bin (for CI)
    echo "Installing to /usr/local/bin"
    sudo mv tttool /usr/local/bin/tttool

    # Copy all .dylib files if they exist
    if ls *.dylib 1> /dev/null 2>&1; then
        sudo mv *.dylib /usr/local/bin/
    fi

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
