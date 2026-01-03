# Contributing to ttmp32gme

Thank you for your interest in contributing to ttmp32gme! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git

### Setting Up Your Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/thawn/ttmp32gme.git
   cd ttmp32gme
   ```

2. Install dependencies (recommended: use `uv`):
   ```bash
   # Install development dependencies including pre-commit hooks
   uv pip install -e ".[dev,test]"
   # OR using pip
   pip install -e ".[dev,test]"
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality and consistency. The hooks automatically run when you commit changes and will:

- Format Python code with **Black** (line length: 88)
- Sort imports with **isort** (Black-compatible profile)
- Lint code with **flake8** (with bugbear plugin)
- Remove trailing whitespace
- Fix end-of-file issues
- Check YAML, JSON, and TOML syntax

### Running Pre-commit Manually

You can run the pre-commit hooks manually on all files:

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Run specific hook
pre-commit run black
pre-commit run flake8
```

### Skipping Hooks (Not Recommended)

In rare cases where you need to skip pre-commit hooks:

```bash
git commit --no-verify -m "Your commit message"
```

**Note:** Skipping hooks is not recommended as it may lead to CI failures.

## Code Style

This project follows these coding conventions:

- **Python Style**: [PEP 8](https://pep8.org/) with Black formatting
- **Line Length**: 88 characters (Black default)
- **Import Sorting**: isort with Black profile
- **Type Hints**: Encouraged, especially with Pydantic models
- **Indentation**: 4 spaces (no tabs)

### PyInstaller Resource Paths

When adding new resource files (HTML, images, config files) that need to work in both development and PyInstaller builds:

1. **Add to PyInstaller spec file** (`ttmp32gme-{platform}.spec`):
   ```python
   datas = [
       (str(source_path / "myfile.ext"), "destination_dir"),
   ]
   ```

2. **Load using `get_resource_path()`** from `ttmp32gme.build.file_handler`:
   ```python
   from ttmp32gme.build.file_handler import get_resource_path

   my_file = get_resource_path("destination_dir/myfile.ext")
   with open(my_file) as f:
       content = f.read()
   ```

3. **DO NOT use** `Path(__file__).parent` or similar - these break in PyInstaller builds.

See the comprehensive documentation in `get_resource_path()` docstring for details.

## Testing

Before submitting a pull request, ensure all tests pass:

```bash
# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/test_web_frontend.py -v

# Run all tests (including E2E)
pytest tests/ -v

# Run with coverage
pytest --cov=ttmp32gme --cov-report=html
```

## Submitting Changes

1. Fork the repository
2. Create a new branch for your feature/fix: `git checkout -b feature-name`
3. Make your changes
4. Ensure pre-commit hooks pass
5. Run tests to verify your changes
6. Commit your changes (pre-commit hooks will run automatically)
7. Push to your fork: `git push origin feature-name`
8. Open a pull request

## Pull Request Guidelines

- Write clear, descriptive commit messages
- Include tests for new features or bug fixes
- Update documentation as needed
- Ensure all CI checks pass
- Keep changes focused and minimal

## Questions?

If you have questions or need help, please open an issue on GitHub.
