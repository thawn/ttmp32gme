#!/bin/bash
# Script to run E2E tests locally, replicating CI pipeline steps

set -e  # Exit on any error

# Parse arguments
SPECIFIC_TEST=""
SKIP_SETUP=false

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --test TEST_NAME    Run specific test (e.g., test_upload_album_with_files)"
    echo "  -k, --keyword KEYWORD   Run tests matching keyword (pytest -k option)"
    echo "  -s, --skip-setup        Skip dependency installation (use when already set up)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                           # Run all tests"
    echo "  $0 -t test_upload_album_with_files          # Run single test"
    echo "  $0 -k upload                                 # Run tests matching 'upload'"
    echo "  $0 -s -t test_navigation_links              # Run test, skip setup"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        -k|--keyword)
            TEST_KEYWORD="$2"
            shift 2
            ;;
        -s|--skip-setup)
            SKIP_SETUP=true
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
echo "Local E2E Test Execution Script"
echo "======================================================================"
echo ""

if [ -n "$SPECIFIC_TEST" ]; then
    echo "Running specific test: $SPECIFIC_TEST"
elif [ -n "$TEST_KEYWORD" ]; then
    echo "Running tests matching keyword: $TEST_KEYWORD"
fi
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

if [ "$SKIP_SETUP" = true ]; then
    print_step "Skipping dependency installation (--skip-setup flag)"
else
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

print_step "Step 2: Installing Chrome and ChromeDriver"
if ! command -v google-chrome &> /dev/null; then
    echo "Installing Chrome..."
    echo "=> Downloading Chrome..." >> "$INSTALL_LOG"
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    echo "=> Installing Chrome package..." >> "$INSTALL_LOG"
    sudo apt install -y ./google-chrome-stable_current_amd64.deb >> "$INSTALL_LOG" 2>&1
    rm google-chrome-stable_current_amd64.deb
fi
google-chrome --version
print_success "Chrome installed"

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
    sudo apt-get install -y ffmpeg >> "$INSTALL_LOG" 2>&1
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
fi  # End of SKIP_SETUP block

if [ "$SKIP_SETUP" = false ]; then
    print_step "Step 6: Running unit tests (including tttool tests)"
    pytest tests/unit/ -v --tb=short
    TEST_EXIT_CODE=$?
    if [ $TEST_EXIT_CODE -ne 0 ]; then
        print_error "Unit tests failed with exit code $TEST_EXIT_CODE"
    else
        print_success "Unit tests passed"
    fi
else
    print_step "Step 6: Skipping unit tests (--skip-setup flag)"
    TEST_EXIT_CODE=0
fi

print_step "Step 7: Starting Flask server in background"

# Check if server is already running from previous run and kill it
if lsof -i:10020 > /dev/null 2>&1; then
    echo "Port 10020 is already in use. Killing existing processes..."
    OLD_PID=$(lsof -t -i:10020)
    if [ -n "$OLD_PID" ]; then
        kill $OLD_PID 2>/dev/null || true
        sleep 2
        # Force kill if still running
        if kill -0 $OLD_PID 2>/dev/null; then
            kill -9 $OLD_PID 2>/dev/null || true
        fi
        print_success "Killed existing server (PID: $OLD_PID)"
    fi
fi

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
# Build pytest command
PYTEST_CMD="pytest tests/e2e/ -v --tb=short"

if [ -n "$SPECIFIC_TEST" ]; then
    PYTEST_CMD="$PYTEST_CMD -k $SPECIFIC_TEST"
    echo "Running specific test: $SPECIFIC_TEST"
elif [ -n "$TEST_KEYWORD" ]; then
    PYTEST_CMD="$PYTEST_CMD -k $TEST_KEYWORD"
    echo "Running tests matching: $TEST_KEYWORD"
fi

# Run E2E tests
eval $PYTEST_CMD
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
