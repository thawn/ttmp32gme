# Contributing

Thank you for your interest in contributing to ttmp32gme! This guide provides information about how you can contribute to the project.

## Ways to Contribute

There are many ways to contribute to ttmp32gme:

* Report bugs
* Suggest new features
* Improve documentation
* Submit code fixes
* Add new features
* Help with testing
* Answer questions in issues

## Getting Started

### Prerequisites

* Python 3.11 or higher
* Git
* tttool (for full functionality)
* Familiarity with Flask and web development

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ttmp32gme.git
   cd ttmp32gme
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/thawn/ttmp32gme.git
   ```

4. **Install dependencies**:
   ```bash
   # Using uv (recommended)
   uv pip install -e ".[dev,test]"
   
   # Or using pip
   pip install -e ".[dev,test]"
   ```

5. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

6. **Verify setup**:
   ```bash
   pytest tests/unit/ -v
   ttmp32gme --version
   ```

## Development Workflow

### 1. Create a Branch

Create a branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
* `feature/` - New features
* `fix/` - Bug fixes
* `docs/` - Documentation changes
* `test/` - Test additions/fixes
* `refactor/` - Code refactoring

### 2. Make Your Changes

Follow these guidelines:

* Write clear, readable code
* Follow existing code style
* Add docstrings to functions/classes
* Include type hints where appropriate
* Keep changes focused and minimal
* Test your changes thoroughly

### 3. Run Pre-commit Hooks

Pre-commit hooks run automatically on commit, or manually:

```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black
pre-commit run flake8
```

Hooks check:
* Code formatting (Black)
* Import sorting (isort)
* Code linting (flake8)
* Trailing whitespace
* File endings
* YAML/JSON syntax

### 4. Write Tests

Add tests for your changes:

**Unit tests** (`tests/unit/`):
```python
def test_your_function():
    """Test description."""
    from ttmp32gme.module import your_function
    
    result = your_function(input_data)
    assert result == expected_output
```

**Integration tests** (`tests/test_web_frontend.py`):
```python
def test_your_route(client):
    """Test route description."""
    response = client.get('/your-route')
    assert response.status_code == 200
```

Run tests:
```bash
pytest tests/ -v
pytest tests/unit/test_your_test.py -v  # Specific test
```

### 5. Update Documentation

If your changes affect usage:

* Update relevant documentation in `docs/`
* Update docstrings
* Update README.md if needed
* Add examples if helpful

### 6. Commit Your Changes

Write clear commit messages:

```bash
git add .
git commit -m "Add feature: brief description

Detailed explanation of what was changed and why.
Include any relevant issue numbers.

Fixes #123"
```

Commit message format:
* First line: Brief summary (50 chars or less)
* Blank line
* Detailed description if needed
* Reference issues/PRs

### 7. Push and Create Pull Request

Push to your fork:
```bash
git push origin feature/your-feature-name
```

Create a pull request on GitHub:
1. Go to your fork on GitHub
2. Click "Pull Request"
3. Select your branch
4. Fill in the PR template
5. Submit

## Pull Request Guidelines

### PR Title

Format: `[Type] Brief description`

Types:
* `[Feature]` - New features
* `[Fix]` - Bug fixes
* `[Docs]` - Documentation changes
* `[Test]` - Test additions/changes
* `[Refactor]` - Code refactoring

Examples:
* `[Feature] Add OGG format support`
* `[Fix] Resolve upload timeout on large files`
* `[Docs] Add troubleshooting section`

### PR Description

Include:
* **Purpose**: What does this PR do?
* **Changes**: List of changes made
* **Testing**: How was this tested?
* **Screenshots**: If UI changes
* **Related Issues**: Link to issues

Template:
```markdown
## Purpose
Brief description of what this PR accomplishes.

## Changes
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Documentation updated

## Related Issues
Fixes #123
```

### PR Checklist

Before submitting:

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated if needed
- [ ] Pre-commit hooks pass
- [ ] No merge conflicts with main branch
- [ ] Commit messages are clear
- [ ] PR description is complete

## Code Review Process

1. **Automated checks run**: CI runs tests on your PR
2. **Review by maintainers**: Code is reviewed
3. **Feedback addressed**: Make requested changes
4. **Approval**: PR is approved
5. **Merge**: PR is merged to main

### Responding to Feedback

* Be receptive to feedback
* Ask questions if unclear
* Make requested changes
* Push updates to same branch
* Respond to comments

## Code Style Guidelines

### Python Style

Follow PEP 8 with Black formatting:

**Good**:
```python
def process_album(
    album_id: int,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Process album with given configuration.
    
    Args:
        album_id: Album identifier
        config: Configuration dictionary
        
    Returns:
        Processing result dictionary
    """
    result = {}
    # Implementation
    return result
```

**Avoid**:
```python
def processAlbum(albumId, config):
    # No docstring
    result = {}
    return result
```

### Database Operations

**Always use DBHandler methods**:

```python
# ✅ Correct
result = db.fetchone("SELECT * FROM albums WHERE oid = ?", (album_id,))

# ❌ Wrong
cursor = db.cursor()
cursor.execute("SELECT * FROM albums WHERE oid = ?", (album_id,))
```

### Input Validation

**Always use Pydantic models**:

```python
# ✅ Correct
from pydantic import ValidationError

try:
    validated = AlbumUpdateModel(**data)
    db.update_album(validated.model_dump())
except ValidationError as e:
    return jsonify({"error": str(e)}), 400

# ❌ Wrong
album_title = data.get('album_title')  # No validation
db.update_album(data)  # Unsanitized input
```

### Error Handling

**Handle errors appropriately**:

```python
# ✅ Correct
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    return {"success": False, "error": str(e)}

# ❌ Wrong
try:
    result = risky_operation()
except:  # Bare except
    pass  # Silent failure
```

## Testing Guidelines

### Test Coverage

Aim for >75% code coverage.

Check coverage:
```bash
pytest --cov=ttmp32gme --cov-report=term-missing
```

### Test Structure

Organize tests clearly:

```python
def test_function_name():
    """Test specific behavior."""
    # Arrange
    input_data = prepare_test_data()
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output
    assert result.status == "success"
```

### Test Fixtures

Use pytest fixtures for common setup:

```python
@pytest.fixture
def sample_album():
    """Provide sample album data."""
    return {
        "oid": 123,
        "title": "Test Album",
        "artist": "Test Artist"
    }

def test_with_fixture(sample_album):
    """Test using fixture."""
    assert sample_album["oid"] == 123
```

## Reporting Bugs

### Before Reporting

1. **Search existing issues**: Check if already reported
2. **Verify the bug**: Ensure it's reproducible
3. **Check latest version**: Bug may be fixed in newer version

### Bug Report Template

```markdown
**Description**
Clear description of the bug.

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What should happen.

**Actual Behavior**
What actually happens.

**Environment**
- OS: Ubuntu 22.04
- Python: 3.11.5
- ttmp32gme: 2.0.0
- Browser: Chrome 120

**Additional Context**
- Error messages
- Screenshots
- Log files
```

## Suggesting Features

### Feature Request Template

```markdown
**Feature Description**
What feature would you like added?

**Use Case**
Why is this feature needed? What problem does it solve?

**Proposed Solution**
How might this be implemented?

**Alternatives**
What alternatives have you considered?

**Additional Context**
Any other information.
```

## Documentation Contributions

Documentation is valuable! Help by:

* Fixing typos and grammar
* Adding examples
* Clarifying unclear sections
* Adding missing documentation
* Translating documentation

Documentation is in `docs/` using Markdown with MyST.

Build documentation locally:
```bash
cd docs/
sphinx-build -b html . _build/html
```

View at `docs/_build/html/index.html`

## Community Guidelines

* Be respectful and inclusive
* Be patient with newcomers
* Provide constructive feedback
* Assume good intentions
* Follow GitHub's Community Guidelines

## Getting Help

* **Questions**: Open a discussion or issue
* **Bugs**: Report via GitHub issues
* **Features**: Suggest via GitHub issues
* **Chat**: Check if project has chat channel

## Recognition

Contributors are recognized in:
* Git commit history
* GitHub contributors page
* Release notes (for significant contributions)

Thank you for contributing to ttmp32gme!

## Additional Resources

* [Development Guide](development.md) - Technical details
* [API Documentation](api/index.md) - API reference
* [GitHub Issues](https://github.com/thawn/ttmp32gme/issues) - Existing issues
* [GitHub Discussions](https://github.com/thawn/ttmp32gme/discussions) - Community discussion
