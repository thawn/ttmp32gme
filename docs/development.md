# Development Guide

This guide is for developers who want to contribute to ttmp32gme or understand its internals.

## Architecture Overview

ttmp32gme is a Flask-based web application with a Python backend that interfaces with tttool for GME file creation.

### Technology Stack

**Backend**:
* Python 3.11+ (Flask 3.0+)
* SQLite database
* Pydantic for validation
* Mutagen for audio metadata

**Frontend**:
* HTML5/CSS3
* JavaScript (jQuery)
* Bootstrap 3 for UI components
* Jinja2 templates

**External Tools**:
* tttool (GME file creation)
* ffmpeg (optional, OGG support)

### Project Structure

```
ttmp32gme/
├── src/
│   ├── ttmp32gme/
│   │   ├── __init__.py
│   │   ├── ttmp32gme.py          # Main Flask application
│   │   ├── db_handler.py         # Database layer
│   │   ├── tttool_handler.py     # tttool interface
│   │   ├── print_handler.py      # Print layout generation
│   │   ├── build/
│   │   │   └── file_handler.py   # File operations
│   │   └── config.sqlite         # Default database
│   ├── templates/                # Jinja2 templates
│   ├── *.html                    # Page templates
│   └── assets/                   # Static files (CSS, JS, images)
├── tests/
│   ├── unit/                     # Unit tests
│   ├── e2e/                      # End-to-end tests
│   └── test_web_frontend.py      # Integration tests
├── docs/                         # Documentation
├── resources/                    # Additional resources
└── pyproject.toml               # Project configuration
```

## Getting Started

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/thawn/ttmp32gme.git
   cd ttmp32gme
   ```

2. **Install in development mode**:
   ```bash
   # Using uv (recommended)
   uv pip install -e ".[test,dev]"
   
   # Or using pip
   pip install -e ".[test,dev]"
   ```

3. **Install tttool** (see [Installation Guide](installation.md#installing-tttool))

4. **Verify setup**:
   ```bash
   python -m ttmp32gme.ttmp32gme --version
   ```

### Running in Development Mode

Start the server with debug enabled:

```bash
ttmp32gme --debug
```

Or with auto-reload:
```bash
export FLASK_ENV=development
python -m ttmp32gme.ttmp32gme
```

Access at: http://localhost:10020

## Code Structure

### Main Application (ttmp32gme.py)

The main Flask application handles:
* Route definitions
* Request/response handling
* File uploads
* Template rendering

**Key routes**:
* `/`: Upload page
* `/library`: Library management
* `/print`: Print layout page
* `/api/*`: REST API endpoints

**Example route**:
```python
@app.route('/api/create_gme', methods=['POST'])
def api_create_gme():
    """Create GME file for an album."""
    data = request.get_json()
    
    # Validate input
    validated = LibraryActionModel(**data)
    
    # Create GME
    result = make_gme(validated.uid, db, config)
    
    return jsonify({"success": True, "result": result})
```

### Database Layer (db_handler.py)

The `DBHandler` class provides a thread-safe SQLite interface:

**Critical**: All database operations MUST go through DBHandler methods.

**Key principles**:
* Singleton pattern for database connection
* Thread-safe with `check_same_thread=False`
* Pydantic models for input validation
* No raw cursors outside DBHandler (except in tests)

**Database operations**:
```python
# ❌ NEVER do this
cursor = db.cursor()
cursor.execute("SELECT ...")

# ✅ ALWAYS do this
result = db.fetchone("SELECT ...")  # or db.fetchall()
```

**Pydantic validation**:
```python
from pydantic import ValidationError

try:
    validated = AlbumUpdateModel(**data)
    db.update_album(validated.model_dump(exclude_none=True))
except ValidationError as e:
    return jsonify({"success": False, "error": str(e)}), 400
```

### TtTool Handler (tttool_handler.py)

Interfaces with the tttool binary for GME operations:

**Key functions**:
* `make_gme()`: Create GME file from audio files
* `generate_codes_yaml()`: Generate OID code mappings
* `create_oids()`: Generate OID code images
* `copy_gme()`: Copy GME to TipToi pen
* `get_sorted_tracks()`: Sort tracks by number

**Example**:
```python
def make_gme(album_id: int, db_handler: DBHandler, config: dict) -> dict:
    """Create GME file for album."""
    # Get album info
    album = db_handler.get_album(album_id)
    
    # Generate YAML config
    yaml_file = create_yaml_config(album)
    
    # Call tttool
    result = subprocess.run(
        ['tttool', 'assemble', yaml_file],
        capture_output=True
    )
    
    return {"success": result.returncode == 0}
```

### Print Handler (print_handler.py)

Generates printable layouts with OID codes:

**Key functions**:
* `create_print_layout()`: Generate HTML for printing
* `format_tracks()`: Format track list with OID codes
* `format_print_button()`: Create control buttons
* `create_pdf()`: Generate PDF (platform-specific)

**Layout generation**:
```python
def create_print_layout(
    album_ids: List[int],
    layout: str,
    db_handler: DBHandler
) -> str:
    """Generate print layout HTML."""
    albums = [db_handler.get_album(aid) for aid in album_ids]
    
    return render_template(
        'print.html',
        albums=albums,
        layout=layout
    )
```

### File Handler (build/file_handler.py)

Manages file system operations:

**Key functions**:
* `make_new_album_dir()`: Create album directory
* `remove_album()`: Delete album files
* `cleanup_filename()`: Sanitize filenames
* `get_tiptoi_dir()`: Detect TipToi mount point
* `check_config_file()`: Initialize config database

## Database Schema

### Tables

**albums**:
```sql
CREATE TABLE albums (
    oid INTEGER PRIMARY KEY,
    album_title TEXT,
    album_artist TEXT,
    album_year TEXT,
    num_tracks INTEGER,
    cover_image TEXT,
    path TEXT,
    player_mode TEXT,
    created_at TIMESTAMP
);
```

**tracks**:
```sql
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_oid INTEGER,
    track_number INTEGER,
    track_title TEXT,
    filename TEXT,
    FOREIGN KEY (album_oid) REFERENCES albums(oid)
);
```

**script_codes**:
```sql
CREATE TABLE script_codes (
    script TEXT PRIMARY KEY,
    code INTEGER UNIQUE
);
```

**config**:
```sql
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

## Testing

### Test Structure

ttmp32gme has three types of tests:

**Unit Tests** (`tests/unit/`):
* Fast, isolated tests
* No external dependencies
* Test individual functions

**Integration Tests** (`tests/test_web_frontend.py`):
* Test Flask routes
* Test database operations
* Test full request/response cycle

**E2E Tests** (`tests/e2e/`):
* Full browser automation with Selenium
* Test complete workflows
* Slow but comprehensive

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/test_web_frontend.py -v

# E2E tests
pytest tests/e2e/ -v

# With coverage
pytest tests/ -v --cov=ttmp32gme --cov-report=html

# Skip slow tests
pytest tests/ -v -m "not slow"

# Skip E2E tests
pytest tests/ -v -m "not e2e"
```

### Writing Tests

**Unit test example**:
```python
def test_cleanup_filename():
    """Test filename sanitization."""
    from ttmp32gme.build.file_handler import cleanup_filename
    
    result = cleanup_filename("Test Album! @#$")
    assert result == "Test_Album"
```

**Integration test example**:
```python
def test_library_page(client):
    """Test library page loads."""
    response = client.get('/library')
    assert response.status_code == 200
    assert b'Library' in response.data
```

**E2E test example**:
```python
@pytest.mark.e2e
def test_upload_album(driver, test_audio_files):
    """Test complete upload workflow."""
    driver.get("http://localhost:10020")
    
    # Upload files
    upload_input = driver.find_element(By.ID, "file-upload")
    upload_input.send_keys(test_audio_files[0])
    
    # Submit
    driver.find_element(By.ID, "submit-btn").click()
    
    # Verify success
    assert "Upload successful" in driver.page_source
```

### Test Fixtures

Use context managers for test file management:
```python
with test_audio_files_context() as test_files:
    # Files created automatically
    driver.find_element(...).send_keys(test_files[0])
    # Files cleaned up automatically on exit
```

### Test Coverage Target

Aim for test coverage >75%.

Check coverage:
```bash
pytest tests/ --cov=ttmp32gme --cov-report=term-missing
```

## Code Style

### Python Style

Follow PEP 8 with these conventions:

* **Indentation**: 4 spaces
* **Line length**: 88 characters (Black default)
* **Imports**: Organized by standard lib, third-party, local
* **Docstrings**: Google style
* **Type hints**: Encouraged, especially with Pydantic

**Example**:
```python
def create_gme(
    album_id: int,
    db_handler: DBHandler,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Create GME file for an album.
    
    Args:
        album_id: Album OID identifier
        db_handler: Database handler instance
        config: Application configuration
        
    Returns:
        Dictionary with success status and result data
        
    Raises:
        ValueError: If album_id not found
        RuntimeError: If GME creation fails
    """
    # Implementation
    pass
```

### JavaScript Style

* Use consistent indentation (2 or 4 spaces)
* Use semicolons
* Use descriptive variable names
* Comment complex logic

### Linting Tools (Optional)

```bash
# Install linters
pip install black flake8 isort

# Format code
black src/

# Check style
flake8 src/

# Sort imports
isort src/
```

## API Reference

See [API Documentation](api/index.md) for detailed API reference.

## Common Development Tasks

### Adding a New Route

1. Add route in `ttmp32gme.py`:
```python
@app.route('/api/new_endpoint', methods=['POST'])
def api_new_endpoint():
    data = request.get_json()
    # Validate, process, return response
    return jsonify({"success": True})
```

2. Add validation model in `db_handler.py` if needed
3. Add tests in `tests/test_web_frontend.py`
4. Update API documentation

### Adding a Database Operation

1. Add method to `DBHandler` class:
```python
def new_operation(self, param: str) -> Any:
    """New database operation."""
    result = self.fetchone("SELECT ...", (param,))
    return result
```

2. Use `self.execute()`, `self.fetchone()`, etc. internally
3. Add tests in `tests/unit/test_db_handler.py`

### Adding Input Validation

1. Create Pydantic model in `db_handler.py`:
```python
class NewInputModel(BaseModel):
    """Validates new input."""
    field1: str = Field(..., max_length=255)
    field2: int = Field(..., ge=0, le=100)
```

2. Use in route:
```python
try:
    validated = NewInputModel(**data)
    # Use validated.field1, validated.field2
except ValidationError as e:
    return jsonify({"error": str(e)}), 400
```

### Adding a Template

1. Create template in `src/templates/` or `src/`
2. Use Jinja2 syntax
3. Extend base template if applicable
4. Add route to render template

### Modifying Print Layout

1. Edit `print_handler.py` for layout generation logic
2. Edit `src/templates/print.html` for HTML structure
3. Edit `src/assets/css/print.css` for styling
4. Test with various layouts and browsers

## Debugging

### Debug Mode

Run with debug logging:
```bash
ttmp32gme --debug
```

Or set Flask debug mode:
```bash
export FLASK_DEBUG=1
ttmp32gme
```

### Browser Console

Open browser developer tools (F12) to:
* See JavaScript errors
* Inspect network requests
* Debug AJAX calls
* Test DOM manipulation

### Python Debugger

Use pdb for debugging:
```python
import pdb; pdb.set_trace()
```

Or use IDE debugger (PyCharm, VS Code).

### Logging

Add logging to your code:
```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

## Contributing

See [Contributing Guide](contributing.md) for:
* How to submit changes
* Code review process
* Pull request guidelines
* Reporting bugs

## Continuous Integration

GitHub Actions runs tests automatically:

**Workflows**:
* `python-tests.yml`: Unit and integration tests (Python 3.11, 3.12, 3.13)
* `javascript-tests.yml`: Frontend tests (Node 18.x, 20.x)
* `e2e-tests.yml`: End-to-end tests (manual trigger)

Tests must pass before merging.

## Release Process

1. Update version in `src/ttmp32gme/_version.py`
2. Update CHANGELOG (if exists)
3. Create git tag: `git tag v2.0.0`
4. Push tag: `git push origin v2.0.0`
5. GitHub Actions creates release
6. Update documentation if needed

## Resources

* [Flask Documentation](https://flask.palletsprojects.com/)
* [Pydantic Documentation](https://docs.pydantic.dev/)
* [tttool Documentation](https://tttool.readthedocs.io/)
* [SQLite Documentation](https://www.sqlite.org/docs.html)

## Next Steps

* Review [API Documentation](api/index.md)
* Read [Contributing Guide](contributing.md)
* Check [GitHub Issues](https://github.com/thawn/ttmp32gme/issues)
* Join discussions on GitHub
