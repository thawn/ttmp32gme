# ttmp32gme Documentation

This directory contains the Sphinx documentation for ttmp32gme.

## Building Documentation

### Prerequisites

Install Sphinx and dependencies:

```bash
pip install sphinx sphinx-rtd-theme myst-parser sphinx-autodoc-typehints
```

### Build HTML Documentation

```bash
# From the docs/ directory
sphinx-build -b html . _build/html

# Or use make (if available)
make html
```

### View Documentation

After building, open `_build/html/index.html` in your web browser.

## Documentation Structure

```
docs/
├── conf.py                     # Sphinx configuration
├── index.md                    # Main documentation index
├── getting-started.md          # Getting started guide
├── installation.md             # Installation instructions
├── usage.md                    # Usage guide
├── print-configuration.md      # Print configuration guide
├── troubleshooting.md          # Troubleshooting guide
├── development.md              # Development guide
├── contributing.md             # Contributing guide
├── api/                        # API reference
│   ├── index.md               # API overview
│   ├── ttmp32gme.md           # Main application module
│   ├── db_handler.md          # Database layer
│   ├── tttool_handler.md      # TipToi GME operations
│   ├── print_handler.md       # Print layout generation
│   └── file_handler.md        # File operations
└── _build/                     # Built documentation (not in git)
    └── html/                   # HTML output
```

## Documentation Format

Documentation is written in Markdown using the [MyST parser](https://myst-parser.readthedocs.io/), which allows:

* Standard Markdown syntax
* Sphinx directives via `{directive}` syntax
* Cross-references to other documents
* Code blocks with syntax highlighting
* Automatically generated API documentation

## API Documentation

API documentation is generated from Python docstrings using Sphinx's `autodoc` extension. To update API docs:

1. Add/update docstrings in Python source files
2. Rebuild documentation
3. API reference is automatically updated

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of the function.
    
    Longer description with more details about what the function does,
    how it works, and any important notes.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something is invalid
        RuntimeError: When something fails
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

## Building for Different Formats

Sphinx can build documentation in multiple formats:

```bash
# HTML (default, recommended)
sphinx-build -b html . _build/html

# PDF (requires LaTeX)
sphinx-build -b latex . _build/latex
cd _build/latex && make

# ePub
sphinx-build -b epub . _build/epub

# Plain text
sphinx-build -b text . _build/text
```

## Updating Documentation

When updating documentation:

1. Edit relevant `.md` files
2. Rebuild documentation: `sphinx-build -b html . _build/html`
3. Review changes in browser
4. Commit updated documentation files (not `_build/`)

## Common Issues

### Warnings About Missing References

If you see warnings like "reference target not found":

1. Check that the referenced file exists
2. Verify the anchor/heading exists in that file
3. Use correct MyST syntax for cross-references

### Module Import Errors

If API documentation fails to generate:

1. Ensure ttmp32gme package is installed: `pip install -e .`
2. Check that Python can import the modules
3. Verify `sys.path` is set correctly in `conf.py`

### Theme Not Found

If the RTD theme is not found:

```bash
pip install sphinx-rtd-theme
```

## Contributing to Documentation

When contributing documentation:

1. Follow the existing style and structure
2. Keep language clear and concise
3. Include examples where helpful
4. Test that documentation builds without errors
5. Check for broken links and references

See [Contributing Guide](contributing.md) for more details.

## Resources

* [Sphinx Documentation](https://www.sphinx-doc.org/)
* [MyST Parser Documentation](https://myst-parser.readthedocs.io/)
* [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io/)
* [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
