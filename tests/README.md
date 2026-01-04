# Python Integration Tests

This directory contains pytest-based integration tests for the ttmp32gme web frontend.

## Running Tests

```bash
# Install test dependencies (from project root)
uv pip install -e ".[test]"  # Recommended; or: pip install -e ".[test]"

# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run E2E tests (requires Chrome/Chromium and ChromeDriver)
pytest tests/e2e/ -v

# Run tests with HTML report
pytest tests/ -v --html=report.html --self-contained-html
```

## Test Files

### Unit Tests (`tests/unit/`)
- `test_db_handler.py` - Tests for database operations and metadata extraction (including OGG file support)
- `test_file_handler.py` - Tests for file handling utilities
- `test_tttool_handler.py` - Tests for TipToi tool integration
- `test_print_handler.py` - Tests for print layout generation
- `test_custom_paths.py` - Tests for custom database and library paths
- `test_create_library_integration.py` - Integration tests for library creation

### Integration Tests
- `test_web_frontend.py` - Integration tests for web pages and assets
  - TestWebPages - Tests that web pages are accessible
  - TestStaticAssets - Tests that static assets (JS, CSS) load correctly
  - TestPageContent - Tests that pages contain expected content

### E2E Tests (`tests/e2e/`)
- `test_comprehensive.py` - Comprehensive end-to-end tests with real audio files
  - File upload with MP3 files and ID3 metadata
  - Cover image extraction and upload
  - GME file creation
  - Web interface navigation and configuration
- `test_upload_ogg_files.py` - End-to-end tests for OGG Vorbis file upload
  - OGG file conversion using ffmpeg
  - OGG Vorbis tag extraction
  - Mixed MP3 and OGG file uploads
- `test_web_interface.py` - Basic web interface tests
- `test_download_gme.py` - GME file download tests
- `test_tttool_handler.py` - TipToi tool integration tests

## OGG File Support

The application supports both MP3 and OGG Vorbis audio files:
- **MP3**: ID3 tags are read using mutagen's EasyID3 interface
- **OGG**: Vorbis comments are read using mutagen's OggVorbis support
- **Conversion**: MP3 files can be converted to OGG format for TipToi playback using ffmpeg

The E2E tests include:
- `ogg_audio_files_context()` fixture that creates test OGG files from MP3 using ffmpeg
- Tag extraction verification for OGG files
- Unit tests in `test_db_handler.py` verify metadata extraction from OGG files

## Test Behavior

These tests are designed to be flexible:
- When the ttmp32gme server is **running**, they perform full integration testing
- When the server is **not running**, tests gracefully skip with informative messages
- E2E tests use the `clean_server` fixture to start isolated server instances

To run the full integration test suite:
1. Start the ttmp32gme server: `python -m ttmp32gme.ttmp32gme`
2. In another terminal: `pytest tests/ -v`

For E2E tests, the `clean_server` fixture automatically starts/stops a test server with isolated database and library.

## Environment Variables

- `TTMP32GME_URL` - Override the default server URL (default: `http://localhost:10020`)

Example:
```bash
TTMP32GME_URL=http://localhost:8080 pytest tests/ -v
```

## Test Framework

- **pytest** - Python testing framework
- **requests** - HTTP library for making requests to the web server
- **selenium** - Web browser automation for E2E tests
- **mutagen** - Audio metadata library (supports MP3, OGG, and other formats)
- **ffmpeg** - Audio conversion tool (required for OGG conversion in E2E tests)
