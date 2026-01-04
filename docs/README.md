# ttmp32gme Documentation

Sphinx documentation for ttmp32gme.

## Building

```bash
uv pip install sphinx sphinx-rtd-theme myst-parser sphinx-autodoc-typehints
# Or: pip install sphinx sphinx-rtd-theme myst-parser sphinx-autodoc-typehints
cd docs/
make html
# Output: _build/html/index.html
```

## Structure

```
docs/
├── conf.py              # Sphinx configuration
├── index.md             # Main index
├── getting-started.md   # Quick start
├── installation.md      # Installation
├── usage.md             # Usage guide
├── print-configuration.md  # Print settings
├── troubleshooting.md   # Common issues
├── development.md       # Dev guide
├── contributing.md      # Contributing
└── api/                 # API reference
    ├── index.md
    ├── ttmp32gme.md
    ├── db_handler.md
    ├── tttool_handler.md
    ├── print_handler.md
    └── file_handler.md
```

## Format

Markdown with MyST parser for Sphinx directives.

## API Documentation

Auto-generated from docstrings using `sphinx.ext.autodoc`.

**Docstring format** (Google style):
```python
def function(param: str) -> bool:
    """Brief description.

    Args:
        param: Description

    Returns:
        Description
    """
```

## Building Other Formats

```bash
sphinx-build -b latex . _build/latex   # PDF
sphinx-build -b epub . _build/epub     # ePub
```

See [Sphinx docs](https://www.sphinx-doc.org/) for more.
