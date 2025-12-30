#!/bin/bash
# Script to run E2E tests
# Requires environment to be set up first with setup_e2e_environment.sh

set -e  # Exit on any error

# Parse arguments
SPECIFIC_TEST=""
TEST_KEYWORD=""

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --test TEST_NAME    Run specific test (e.g., test_upload_album_with_files)"
    echo "  -k, --keyword KEYWORD   Run tests matching keyword (pytest -k option)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                           # Run all E2E tests"
    echo "  $0 -t test_upload_album_with_files          # Run single test"
    echo "  $0 -k upload                                 # Run tests matching 'upload'"
    echo ""
    echo "Note: Run setup_e2e_environment.sh first to set up the environment."
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
echo "E2E Test Execution"
echo "======================================================================"
echo ""

if [ -n "$SPECIFIC_TEST" ]; then
    echo "Running specific test: $SPECIFIC_TEST"
elif [ -n "$TEST_KEYWORD" ]; then
    echo "Running tests matching keyword: $TEST_KEYWORD"
else
    echo "Running all E2E tests"
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

print_step "Step 1: Starting Flask server in background"

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

print_step "Step 2: Running E2E tests with Selenium"
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

if [ $E2E_EXIT_CODE -eq 0 ]; then
    print_success "All E2E tests passed! ✓"
    exit 0
else
    print_error "Some E2E tests failed"
    exit 1
fi
