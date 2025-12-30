# E2E Test Scripts

This directory contains scripts for running End-to-End (E2E) tests for the ttmp32gme project.

## New Modular Approach (Recommended)

The E2E test execution has been split into two separate scripts for better control and efficiency:

### 1. `setup_e2e_environment.sh` - Environment Setup

Sets up all dependencies needed for E2E testing. Run this once before running tests.

**Usage:**
```bash
./setup_e2e_environment.sh [OPTIONS]
```

**Options:**
- `-b, --browser`: Install Chromium and ChromeDriver (required for E2E tests)
- `-h, --help`: Show help message

**Examples:**
```bash
# Install all dependencies including browser
./setup_e2e_environment.sh -b

# Install only Python dependencies (if browser already installed)
./setup_e2e_environment.sh
```

**What it installs:**
- System dependencies (wget, unzip, jq)
- Chromium and ChromeDriver (with `-b` flag)
- tttool (for GME file creation)
- ffmpeg (for audio processing)
- Python dependencies (via uv or pip)
- Runs unit tests to verify installation

### 2. `run_e2e_tests.sh` - Test Runner

Runs the E2E tests. Can be run repeatedly without re-installing dependencies.

**Usage:**
```bash
./run_e2e_tests.sh [OPTIONS]
```

**Options:**
- `-t, --test TEST_NAME`: Run a specific test
- `-k, --keyword KEYWORD`: Run tests matching a keyword
- `-h, --help`: Show help message

**Examples:**
```bash
# Run all E2E tests
./run_e2e_tests.sh

# Run a specific test
./run_e2e_tests.sh -t test_upload_album_with_files

# Run tests matching 'upload'
./run_e2e_tests.sh -k upload
```

**What it does:**
- Starts Flask server on port 10020
- Runs E2E tests with Selenium
- Stops the server after tests complete

## Legacy Script (Backward Compatibility)

### `run_e2e_tests_locally.sh`

The original monolithic script that combines setup and test execution. This is maintained for backward compatibility but is **deprecated** in favor of the split scripts above.

**Usage:**
```bash
./run_e2e_tests_locally.sh [OPTIONS]
```

**Options:**
- `-t, --test TEST_NAME`: Run a specific test
- `-k, --keyword KEYWORD`: Run tests matching a keyword
- `-s, --skip-setup`: Skip dependency installation
- `-h, --help`: Show help message

## Workflow

### First Time Setup:
```bash
# 1. Set up environment (includes browser)
./setup_e2e_environment.sh -b

# 2. Run tests
./run_e2e_tests.sh
```

### Subsequent Test Runs:
```bash
# Just run tests (no need to reinstall)
./run_e2e_tests.sh

# Or run specific test
./run_e2e_tests.sh -t test_navigation_links
```

### Iterative Test Development:
```bash
# Run specific test repeatedly while debugging
./run_e2e_tests.sh -t test_upload_album_with_files
```

## Benefits of Split Scripts

1. **Faster iteration**: Run tests multiple times without reinstalling dependencies
2. **Clearer separation**: Setup vs. test execution
3. **Better CI/CD**: Can cache setup step, run tests multiple times
4. **Selective installation**: Install browser only when needed
5. **Easier maintenance**: Modify setup or test runner independently

## Log Files

- `/tmp/e2e_installation.log`: Setup script output
- `/tmp/pip_install.log`: Python package installation log
- `/tmp/ttmp32gme_server.log`: Flask server output during tests

## Troubleshooting

### ChromeDriver Issues
If you encounter ChromeDriver problems, reinstall with:
```bash
./setup_e2e_environment.sh -b
```

### Server Port Conflicts
If port 10020 is in use, the test runner will automatically kill the existing process.

### Test Failures
Check the server log for errors:
```bash
cat /tmp/ttmp32gme_server.log
```
