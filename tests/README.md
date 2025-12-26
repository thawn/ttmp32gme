# Python Integration Tests

This directory contains pytest-based integration tests for the ttmp32gme web frontend.

## Running Tests

```bash
# Install test dependencies (from project root)
pip install -r requirements-test.txt

# Run all tests
pytest tests/ -v

# Run tests with HTML report
pytest tests/ -v --html=report.html --self-contained-html
```

## Test Files

- `test_web_frontend.py` - Integration tests for web pages and assets
  - TestWebPages - Tests that web pages are accessible
  - TestStaticAssets - Tests that static assets (JS, CSS) load correctly
  - TestPageContent - Tests that pages contain expected content

## Test Behavior

These tests are designed to be flexible:
- When the ttmp32gme server is **running**, they perform full integration testing
- When the server is **not running**, tests gracefully skip with informative messages

To run the full integration test suite:
1. Start the ttmp32gme server: `cd src && perl ttmp32gme.pl`
2. In another terminal: `pytest tests/ -v`

## Environment Variables

- `TTMP32GME_URL` - Override the default server URL (default: `http://localhost:10020`)

Example:
```bash
TTMP32GME_URL=http://localhost:8080 pytest tests/ -v
```

## Test Framework

- **pytest** - Python testing framework
- **requests** - HTTP library for making requests to the web server
