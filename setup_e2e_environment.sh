#!/bin/bash
# Script to set up E2E test environment
# This script installs all dependencies needed for E2E testing

set -e  # Exit on any error

# Parse arguments
INSTALL_BROWSER=false

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -b, --browser           Install Chromium and ChromeDriver"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      # Install Python dependencies only"
    echo "  $0 -b                   # Install all dependencies including browser"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--browser)
            INSTALL_BROWSER=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

echo "======================================================================"
echo "E2E Test Environment Setup"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}===> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Get repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# Create log file
INSTALL_LOG="/tmp/e2e_installation.log"
echo "Installation output will be written to: $INSTALL_LOG"
echo "=====================================================================" > "$INSTALL_LOG"
echo "E2E Test Environment Installation Log" >> "$INSTALL_LOG"
echo "Started: $(date)" >> "$INSTALL_LOG"
echo "=====================================================================" >> "$INSTALL_LOG"
echo "" >> "$INSTALL_LOG"

print_step "Step 1: Installing system dependencies"
if ! command -v wget &> /dev/null || ! command -v jq &> /dev/null; then
    echo "Installing required tools (wget, unzip, jq)..."
    echo "=> Installing wget, unzip, jq..." >> "$INSTALL_LOG"
    sudo apt-get update >> "$INSTALL_LOG" 2>&1 && sudo apt-get install -y wget unzip jq >> "$INSTALL_LOG" 2>&1
fi
print_success "System dependencies installed"

if [ "$INSTALL_BROWSER" = true ]; then
    print_step "Step 2: Installing Chromium and ChromeDriver"

    # Install ChromeDriver - use system package for simplicity and reliability
    echo "Installing ChromeDriver..."
    if ! command -v chromedriver &> /dev/null; then
        echo "=> Installing chromium-chromedriver..." >> "$INSTALL_LOG"
        sudo apt-get install -y chromium-chromedriver >> "$INSTALL_LOG" 2>&1 || {
            print_error "Failed to install ChromeDriver"
            echo "Failed to install ChromeDriver. Check $INSTALL_LOG for details." >> "$INSTALL_LOG"
            exit 1
        }
    fi
    chromedriver --version
    print_success "ChromeDriver installed"
else
    print_step "Step 2: Skipping Chromium/ChromeDriver installation (use -b flag to install)"
fi

print_step "Step 3: Installing tttool"
TTTOOL_VERSION="1.8.1"
echo "Installing tttool version $TTTOOL_VERSION"
echo "=> Downloading tttool ${TTTOOL_VERSION}..." >> "$INSTALL_LOG"

# Download tttool
wget -q "https://github.com/entropia/tip-toi-reveng/releases/download/${TTTOOL_VERSION}/tttool-${TTTOOL_VERSION}.zip"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TEMP_DIR" >> "$INSTALL_LOG"

# Extract to temp directory
cd "$TEMP_DIR"
echo "=> Extracting tttool..." >> "$INSTALL_LOG"
unzip -q "$REPO_ROOT/tttool-${TTTOOL_VERSION}.zip" >> "$INSTALL_LOG" 2>&1

# Move binary to system path
echo "=> Installing tttool to /usr/local/bin/..." >> "$INSTALL_LOG"
sudo mv tttool /usr/local/bin/ >> "$INSTALL_LOG" 2>&1
sudo chmod +x /usr/local/bin/tttool >> "$INSTALL_LOG" 2>&1

# Clean up
cd "$REPO_ROOT"
chmod -R u+w "$TEMP_DIR" 2>/dev/null || true
rm -rf "$TEMP_DIR"
rm "tttool-${TTTOOL_VERSION}.zip"

# Verify installation
if ! tttool --help > /dev/null 2>&1; then
    print_error "tttool installation failed"
    echo "tttool verification failed" >> "$INSTALL_LOG"
    exit 1
fi
print_success "tttool installed successfully"

print_step "Step 4: Installing ffmpeg"
if ! command -v ffmpeg &> /dev/null; then
    echo "=> Installing ffmpeg..." >> "$INSTALL_LOG"
    # Try with 60 second timeout
    if timeout 60 sudo apt-get install -y ffmpeg >> "$INSTALL_LOG" 2>&1; then
        print_success "ffmpeg installed on first attempt"
    else
        echo "=> First attempt failed or timed out, retrying..." >> "$INSTALL_LOG"
        echo "Retrying ffmpeg installation (timeout or failure on first attempt)..."
        # Retry with 60 second timeout
        if timeout 60 sudo apt-get install -y ffmpeg >> "$INSTALL_LOG" 2>&1; then
            print_success "ffmpeg installed on second attempt"
        else
            print_error "ffmpeg installation failed after 2 attempts"
            echo "ffmpeg installation failed after 2 attempts" >> "$INSTALL_LOG"
            exit 1
        fi
    fi
else
    print_success "ffmpeg already installed"
fi
ffmpeg -version | head -n1

print_step "Step 5: Installing Python dependencies"
PIP_LOG="/tmp/pip_install.log"
echo "Output will be written to: $PIP_LOG"

if command -v uv &> /dev/null; then
    echo "Using uv for package installation..."
    uv pip install --system -e ".[test]" > "$PIP_LOG" 2>&1
    INSTALL_EXIT=$?
else
    echo "uv not available, trying to install..."
    if curl -LsSf https://astral.sh/uv/install.sh 2>/dev/null | sh >> "$PIP_LOG" 2>&1; then
        # Add uv to PATH
        export PATH="$HOME/.cargo/bin:$PATH"
        export PATH="$HOME/.local/bin:$PATH"
        # Try to find uv
        if command -v uv &> /dev/null; then
            uv pip install --system -e ".[test]" >> "$PIP_LOG" 2>&1
            INSTALL_EXIT=$?
        else
            echo "uv installed but not found in PATH, falling back to pip..."
            pip install -e ".[test]" >> "$PIP_LOG" 2>&1
            INSTALL_EXIT=$?
        fi
    else
        echo "uv installation failed, falling back to pip..."
        pip install -e ".[test]" >> "$PIP_LOG" 2>&1
        INSTALL_EXIT=$?
    fi
fi

if [ $INSTALL_EXIT -ne 0 ]; then
    print_error "Python dependency installation failed. Check $PIP_LOG for details."
    tail -n 50 "$PIP_LOG"
    exit 1
fi
print_success "Python dependencies installed"

print_step "Step 6: Running unit tests to verify installation"
pytest tests/unit/ -v --tb=short
TEST_EXIT_CODE=$?
if [ $TEST_EXIT_CODE -ne 0 ]; then
    print_error "Unit tests failed with exit code $TEST_EXIT_CODE"
    echo ""
    echo "Setup completed with warnings. Some unit tests failed."
    echo "This may indicate an issue with the installation."
    exit 1
else
    print_success "Unit tests passed"
fi

echo ""
echo "======================================================================"
echo "Setup Complete!"
echo "======================================================================"
echo ""
print_success "E2E test environment is ready"
echo ""
echo "Next steps:"
echo "  Run E2E tests with: ./run_e2e_tests.sh"
echo ""
