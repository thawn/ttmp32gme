# Development Guide

## Architecture

Flask web application (Python 3.11+) with SQLite database. Uses tttool for GME creation.

**Key Modules**:
- `ttmp32gme.py` - Flask app, routes
- `db_handler.py` - Database (SQLite, Pydantic validation)
- `tttool_handler.py` - GME/OID code generation
- `print_handler.py` - Print layouts
- `build/file_handler.py` - File operations

## Setup

```bash
git clone https://github.com/thawn/ttmp32gme.git
cd ttmp32gme
uv pip install -e ".[test,dev]"  # Recommended; or: pip install ...
pre-commit install
```

Run: `ttmp32gme -vv` (for debug output)

**Development Server**: By default, ttmp32gme uses Waitress (production WSGI server). Use `--dev` flag to enable Flask's development server with auto-reload for rapid iteration during development:

```bash
ttmp32gme --dev -vv  # Flask dev server with auto-reload
```

## Code Quality

**Pre-commit hooks** automatically run:
- Black (code formatting)
- isort (import sorting)
- flake8 (linting)
- pyright (strict mode type checking)

Run manually: `pre-commit run --all-files`

**Type Checking**: Source code uses strict pyright mode.
```bash
pyright src/ttmp32gme  # Check types
```

## Testing

```bash
pytest tests/unit/ -v        # Unit tests
pytest tests/e2e/ -v         # E2E tests
pytest --cov=ttmp32gme       # With coverage
```

## Code Patterns

**Database**: Always use `DBHandler` methods, never raw cursors.
```python
result = db.fetchone("SELECT ...")  # ✓
cursor = db.cursor()  # ✗
```

**Validation**: Use Pydantic models for all input.
```python
validated = AlbumUpdateModel(**data)
```

## Contributing

See [Contributing Guide](contributing.md) for PR guidelines and workflow.
