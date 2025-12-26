#!/bin/bash
# Script to run E2E tests locally, replicating CI pipeline steps

set -e  # Exit on any error

echo "======================================================================"
echo "Local E2E Test Execution Script"
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

print_step "Step 1: Installing system dependencies"
if ! command -v wget &> /dev/null || ! command -v jq &> /dev/null; then
    echo "Installing required tools (wget, unzip, jq)..."
    sudo apt-get update && sudo apt-get install -y wget unzip jq
fi
print_success "System dependencies installed"

print_step "Step 2: Installing Chrome and ChromeDriver"
if ! command -v google-chrome &> /dev/null; then
    echo "Installing Chrome..."
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt install -y ./google-chrome-stable_current_amd64.deb
    rm google-chrome-stable_current_amd64.deb
fi
google-chrome --version
print_success "Chrome installed"

# Install ChromeDriver - use system package for simplicity and reliability
echo "Installing ChromeDriver..."
if ! command -v chromedriver &> /dev/null; then
    sudo apt-get install -y chromium-chromedriver || {
        print_error "Failed to install ChromeDriver"
        exit 1
    }
fi
chromedriver --version
print_success "ChromeDriver installed"

print_step "Step 3: Installing tttool"
TTTOOL_VERSION="1.8.1"
echo "Installing tttool version $TTTOOL_VERSION"

# Download tttool
wget -q "https://github.com/entropia/tip-toi-reveng/releases/download/${TTTOOL_VERSION}/tttool-${TTTOOL_VERSION}.zip"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TEMP_DIR"

# Extract to temp directory
cd "$TEMP_DIR"
unzip -q "$REPO_ROOT/tttool-${TTTOOL_VERSION}.zip"

# Move binary to system path
sudo mv tttool /usr/local/bin/
sudo chmod +x /usr/local/bin/tttool

# Clean up
cd "$REPO_ROOT"
chmod -R u+w "$TEMP_DIR" 2>/dev/null || true
rm -rf "$TEMP_DIR"
rm "tttool-${TTTOOL_VERSION}.zip"

# Verify installation
if ! tttool --help > /dev/null 2>&1; then
    print_error "tttool installation failed"
    exit 1
fi
print_success "tttool installed successfully"

print_step "Step 4: Installing ffmpeg"
if ! command -v ffmpeg &> /dev/null; then
    sudo apt-get install -y ffmpeg
fi
ffmpeg -version | head -n1
print_success "ffmpeg installed"

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

print_step "Step 6: Running unit tests (including tttool tests)"
pytest tests/unit/ -v --tb=short
TEST_EXIT_CODE=$?
if [ $TEST_EXIT_CODE -ne 0 ]; then
    print_error "Unit tests failed with exit code $TEST_EXIT_CODE"
else
    print_success "Unit tests passed"
fi

print_step "Step 7: Starting Flask server in background"
python -m ttmp32gme.ttmp32gme --port 10020 > /tmp/ttmp32gme_server.log 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server to start
sleep 5

# Check if server is still running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    print_error "Server failed to start"
    cat /tmp/ttmp32gme_server.log
    exit 1
fi

# Check if server responds
if ! curl -s http://localhost:10020/ > /dev/null; then
    print_error "Server is not responding"
    kill $SERVER_PID 2>/dev/null || true
    cat /tmp/ttmp32gme_server.log
    exit 1
fi

print_success "Server started successfully on http://localhost:10020"

print_step "Step 8: Running E2E tests with Selenium"
# Run E2E tests
pytest tests/e2e/ -v --tb=short -m "e2e"
E2E_EXIT_CODE=$?

# Stop server
print_step "Stopping Flask server"
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true
print_success "Server stopped"

echo ""
echo "======================================================================"
echo "Test Execution Summary"
echo "======================================================================"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ] && [ $E2E_EXIT_CODE -eq 0 ]; then
    print_success "All tests passed! ✓"
    echo ""
    echo "Unit tests: PASSED"
    echo "E2E tests:  PASSED"
    exit 0
else
    print_error "Some tests failed"
    echo ""
    echo "Unit tests: $([ $TEST_EXIT_CODE -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
    echo "E2E tests:  $([ $E2E_EXIT_CODE -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
    exit 1
fi
