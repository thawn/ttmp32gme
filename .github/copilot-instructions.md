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
- **Documentation**: Sphinx-based documentation in `docs/` folder with API reference. Concise and user-centric.

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

### Changing the database schema

Whenever the database schema is changed, or options are added/removed in the `config` table:

- increase the database version in the `config` table to the version of the next release (assume the next feature release)
- make sure DBHandler.update_db updates old versions of the database the first time they are opened

### Building & Linting

Pre-commit hooks perform the following steps:

- trailing white spaces
- flake8
- black

**No build step required** - Python source runs directly.

### Documentation

Keep documentation concise and target audience-centric. Whenever new features are implemented or the API of existing features changes, check if the documentation needs to be updated.

#### Documentation Structure
- User guides: `docs/*.md` (except for `docs/Contributing.md`, `docs/Development.md`) getting-started, installation, usage, etc. Target audience: users
- API reference: `docs/Contributing.md`, `docs/Development.md`, `docs/api/*.md` module documentation. Target audience: developers.
- Configuration: `docs/conf.py`
- Built output: `docs/_build/html/`

#### Building documentation

Documentation is built using Sphinx:

```bash
# Install documentation dependencies
uv pip install sphinx sphinx-rtd-theme myst-parser sphinx-autodoc-typehints

# Build HTML documentation
cd docs/
sphinx-build -b html . _build/html

# View documentation
# Open docs/_build/html/index.html in browser
```
Whenever you make changes to any file in the docs/ directory, verify that the documentation still builds without warnings or errors (warnings are treated as errors in the CI workflow that builds documentation).


## Code Patterns & Conventions

### Database Access (CRITICAL)
All database operations MUST go through DBHandler methods (except in unit tests).

### PyInstaller Resource Paths (CRITICAL)
When adding resource files (HTML, images, config) that need to work in both development and PyInstaller builds:

**DO**: Use `get_resource_path()` from `ttmp32gme.build.file_handler`
```python
from ttmp32gme.build.file_handler import get_resource_path

# Load a resource file
resource = get_resource_path("upload.html")
with open(resource) as f:
    content = f.read()
```

**DON'T**: Use `Path(__file__).parent` or similar - breaks in PyInstaller
```python
# ❌ WRONG - breaks in PyInstaller
resource = Path(__file__).parent / "upload.html"
```

**Adding new resources**:
1. Add to PyInstaller spec file's `datas` list
2. Load with `get_resource_path("relative/path")`
3. See `get_resource_path()` docstring for comprehensive guide

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
2. Run only the failing tests locally: `pytest tests/e2e/<failing tests>
3. Check server logs in `/tmp/server.log` for errors
4. Add debug statements to test for element visibility
5. repeat until the problem is solved and the tests are passing.
6. only after the failing tests are passing, run other tests.

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
