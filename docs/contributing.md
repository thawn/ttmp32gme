# Contributing

## Quick Start

1. Fork and clone repository
2. Install: `uv pip install -e ".[dev,test]"`
3. Install pre-commit hooks: `pre-commit install`
4. Create branch: `git checkout -b feature/name`
5. Make changes, write tests
6. Run tests: `pytest tests/ -v`
7. Commit (hooks run automatically)
8. Push and create pull request

## Guidelines

**Code**:
- Follow existing style
- Add docstrings and type hints
- Use DBHandler for database ops
- Validate input with Pydantic

**Testing**:
- Add tests for new features
- Ensure existing tests pass
- Aim for >75% coverage

**Pull Requests**:
- Clear title: `[Feature] Description` or `[Fix] Description`
- Include: purpose, changes, testing done
- Keep changes focused and minimal

**Pre-commit hooks** check:
- Code formatting (Black)
- Import sorting (isort)
- Linting (flake8)
- Type checking (pyright strict mode)

Run manually: `pre-commit run --all-files`

## Reporting Issues

Include:
- OS and Python version
- Steps to reproduce
- Expected vs actual behavior
- Error messages

See [Development Guide](development.md) for architecture details.
