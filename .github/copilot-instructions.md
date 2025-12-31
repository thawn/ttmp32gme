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

The setup is performed for you by `.github/workflows/copilot-setup-steps.yml`

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

**Always run all necessary tests before finishing up.**

#### Unit Tests (Fast, no dependencies)

should always be run when any code was changed.

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_library_handler.py -v
```

#### Integration Tests

should always be run when the flask app was changed.

```bash
pytest tests/test_web_frontend.py -v
```

#### E2E Tests (Selenium)

should always be run if non-trivial changes were made to the frontend or backend. the necessary dependencies are already preinstalled in your environment.

```bash
# Run all E2E tests
./pytest tests/e2e/ -v

# Run specific test
pytest tests/e2e/test_upload_album_with_files.py -v

# Run tests matching keyword
pytest -k upload -v
```

#### Test Markers

- Skip E2E tests: `pytest -m "not e2e"`
- Skip slow tests: `pytest -m "not slow"`

#### Test Coverage

Aim for test coverage >75%.

### Building & Linting

Pre-commit hooks perform the following steps:

- trailing white spaces
- flake8
- black

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

### Database Access (CRITICAL)
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

## Common Tasks

### Adding a New Database Operation
1. Add method to `DBHandler` class in `src/ttmp32gme/db_handler.py`
2. Use `self.execute()`, `self.fetchone()`, `self.commit()` internally
3. Call from Flask route: `db.new_method()`

### Adding a New Route
1. Add route in `src/ttmp32gme/ttmp32gme.py`
2. Implement logic in `src/ttmp32gme/*_handler.py` files. Only call functions in `src/ttmp32gme/ttmp32gme.py`.
3. Validate input with Pydantic
4. Use `db` (DBHandler instance) for database operations
5. Return JSON for AJAX or render template for pages

### Fixing E2E Test Issues
1. attempt to fix the problem
2. Run the failing tests locally: `pytest tests/e2e/<failing tests>
3. Check server logs in `/tmp/server.log` for errors
4. Add debug statements to test for element visibility
5. repeat until the problem is solved and the tests are passing.

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
