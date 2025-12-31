# Copilot Coding Agent Instructions for ttmp32gme

## Repository Overview

**ttmp32gme** is a cross-platform tool that converts MP3/audio files into TipToi GME (Game Music Engine) files playable on the TipToi pen. It generates printable control sheets with OID codes for music/audiobook playback control.

### Key Stats
- **Languages**: Python (backend), JavaScript (frontend), Shell scripts (testing)
- **Size**: ~500 files, primarily Python source in `src/ttmp32gme/`
- **Framework**: Flask 3.0+ web application with Jinja2 templates
- **Database**: SQLite with custom DBHandler class
- **Python Version**: 3.11+ required
- **Testing**: 80+ tests (unit, integration, E2E with Selenium); coverage target 75%+
- **Documentation**: Sphinx-based documentation in `docs/` folder with API reference

### Architecture
- **Backend**: Python Flask application migrated from Perl
- **Database Layer**: Unified DBHandler class (`src/ttmp32gme/db_handler.py`)
  - All database operations go through DBHandler singleton
  - Thread-safe SQLite with `check_same_thread=False`
  - Never use raw cursors outside DBHandler - always use `db.execute()`, `db.fetchone()`, etc.
- **Validation**: Pydantic models in `db_handler.py` validate all frontend input
- **Dependencies**: tttool (external binary), ffmpeg (optional for OGG)

## Development Workflow

### Bootstrap & Setup

```bash
# Clone repository
git clone https://github.com/thawn/ttmp32gme.git && cd ttmp32gme

# Install Python dependencies (recommended: use uv)
uv pip install -e ".[test]"
# OR
pip install -e ".[test]"

# Install external dependencies
# - tttool: https://github.com/entropia/tip-toi-reveng#installation
# - ffmpeg: sudo apt-get install ffmpeg (Ubuntu) or brew install ffmpeg (macOS)
```

**Verification**: `python -m ttmp32gme.ttmp32gme --help` should show usage info.

### Running the Application

```bash
# Start server (default: localhost:10020)
python -m ttmp32gme.ttmp32gme

# Or use entry point
ttmp32gme

# Custom host/port
ttmp32gme --host 0.0.0.0 --port 8080

# Access UI at http://localhost:10020
```

**Verification**: `curl http://localhost:10020/` should return HTML.

### Testing

#### Test Coverage

Aim for test coverage >75%.

#### Unit Tests (Fast, no dependencies)
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_library_handler.py -v
```

#### Integration Tests
```bash
pytest tests/test_web_frontend.py -v
```

#### E2E Tests (Selenium)
```bash
# Run all E2E tests
./pytest tests/e2e/ -v

# Run specific test
pytest tests/e2e/test_upload_album_with_files.py -v

# Run tests matching keyword
pytest -k upload -v
```

**E2E Test Markers**:
- Skip E2E tests: `pytest -m "not e2e"`
- Skip slow tests: `pytest -m "not slow"`

### Building & Linting

**No formal linting configured** - follow existing code style:
- 4-space indentation
- Type hints encouraged (especially with Pydantic)
- Descriptive variable names

**No build step required** - Python source runs directly.

### Building Documentation

Documentation is built using Sphinx:

```bash
# Install documentation dependencies
pip install sphinx sphinx-rtd-theme myst-parser sphinx-autodoc-typehints

# Build HTML documentation
cd docs/
sphinx-build -b html . _build/html

# View documentation
# Open docs/_build/html/index.html in browser
```

**Documentation Structure**:
- User guides: `docs/*.md` (getting-started, installation, usage, etc.)
- API reference: `docs/api/*.md` (module documentation)
- Configuration: `docs/conf.py`
- Built output: `docs/_build/html/`

## Code Patterns & Conventions

### Code Organization (CRITICAL)
**Keep ttmp32gme.py clean** - implement business logic in handler files:
- `ttmp32gme.py` should contain only Flask routes and app configuration
- Implement helper functions and business logic in the appropriate handler:
  - `db_handler.py` - Database operations, Pydantic models
  - `tttool_handler.py` - GME generation, OID code management
  - `print_handler.py` - Print layouts, PDF generation
  - `build/file_handler.py` - File system utilities

❌ **NEVER do this** in ttmp32gme.py:
```python
@app.route('/process')
def process():
    # Complex business logic here
    result = some_complex_calculation()
    # More business logic
    return result
```

✅ **ALWAYS do this**:
```python
# In handler file (e.g., tttool_handler.py)
def process_data(data):
    # Complex business logic here
    return result

# In ttmp32gme.py
@app.route('/process')
def process():
    data = request.get_json()
    result = process_data(data)
    return jsonify(result)
```

### Database Access (CRITICAL)
❌ **NEVER do this**:
```python
cursor = db.cursor()
cursor.execute("SELECT ...")
```

✅ **ALWAYS do this**:
```python
result = db.fetchone("SELECT ...")  # or db.fetchall()
```
All database operations MUST go through DBHandler methods (except in unit tests).

### Input Validation
All frontend input MUST be validated with Pydantic models in `db_handler.py`:
```python
from pydantic import ValidationError

try:
    validated = AlbumUpdateModel(**data)
    db.update_album(validated.model_dump(exclude_none=True))
except ValidationError as e:
    return jsonify({"success": False, "error": str(e)}), 400
```

### Test Fixtures
Use context managers for test file management:
```python
with test_audio_files_context() as test_files:
    # Files created automatically
    driver.find_element(...).send_keys(test_files[0])
    # Files cleaned up automatically on exit
```

### Tests

- Tests use pytest framework with fixtures for setup/teardown. E2E tests use Selenium WebDriver (Chrome).
- Write tests to be strict and fail early on errors.

### Threading
SQLite connection uses `check_same_thread=False` for Flask's multi-threaded environment. DBHandler is safe to use across request threads.

## Common Tasks

### Code Organization Best Practices

**Keep ttmp32gme.py Clean**:
- The main `ttmp32gme.py` file should primarily contain Flask routes and application setup
- Implement business logic and helper functions in the respective handler files:
  - `db_handler.py` - Database operations and data models
  - `tttool_handler.py` - GME/OID code generation and tttool interactions
  - `print_handler.py` - Print layout and PDF generation
  - `build/file_handler.py` - File system operations and utilities
- Keep route handlers in `ttmp32gme.py` focused on request/response handling, validation, and calling handler functions

**Testing Requirements**:
- When adding new functions to handler files, **always add corresponding unit tests** in `tests/unit/test_<handler_name>.py`
- When adding new frontend features, **always add corresponding E2E tests** in `tests/e2e/`
- Run the E2E tests after implementation to ensure everything works correctly
- Follow existing test patterns and use appropriate fixtures

### Adding a New Database Operation
1. Add method to `DBHandler` class in `src/ttmp32gme/db_handler.py`
2. Use `self.execute()`, `self.fetchone()`, `self.commit()` internally
3. Call from Flask route: `db.new_method()`
4. **Add unit tests** in `tests/unit/test_db_handler.py`

### Adding Input Validation
1. Create/extend Pydantic model in `db_handler.py`
2. Add field constraints (`Field()`, regex patterns, value ranges)
3. Validate in Flask route before calling DBHandler
4. **Add unit tests** to verify validation logic

### Adding a New Route
1. Add route in `src/ttmp32gme/ttmp32gme.py`
2. Validate input with Pydantic
3. Use `db` (DBHandler instance) for database operations
4. Return JSON for AJAX or render template for pages
5. **Add integration tests** in `tests/test_web_frontend.py` for API routes
6. **Add E2E tests** in `tests/e2e/` for user-facing features

### Fixing E2E Test Issues
1. Before re-running specific test, start the server manually:
```bash
 ./ttmp32gme > /tmp/server.log 2>&1 & sleep(2)  # Start server in background
```
2. Check server logs in `/tmp/server.log` for errors
3. Add debug statements to test for element visibility
4. Use explicit waits: `WebDriverWait(driver, 5).until(...)`

## File Locations

- **Source**: `src/ttmp32gme/` (main application)
- **Templates**: `resources/` (Jinja2 HTML templates)
- **Tests**: `tests/unit/`, `tests/e2e/`, `tests/test_web_frontend.py`
- **Static files**: `resources/assets/` (CSS, JS, images)
- **Config**: `pyproject.toml` (dependencies, pytest config)
- **Documentation**: `docs/` (Sphinx documentation)

## Quick Reference Commands

```bash
# Install dependencies
uv pip install -e ".[test]"

# Run app
python -m ttmp32gme.ttmp32gme

# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run E2E tests (takes about 1-2 minutes)
pytest tests/e2e/ -v

# Build documentation
cd docs/ && sphinx-build -b html . _build/html
```

## CI/CD

GitHub Actions workflows run automatically on PRs:
- **python-tests.yml**: Unit and integration tests (Python 3.11, 3.12, 3.13)
- **javascript-tests.yml**: Frontend Jest tests (Node 18.x, 20.x)
- **e2e-tests.yml**: Full E2E suite (manual trigger or workflow_dispatch)

Tests must pass before merging.
