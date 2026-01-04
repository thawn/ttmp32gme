# Troubleshooting

## Installation

**Python version error**: Use Python 3.11+ (`python3.11 -m pip install -e .` or `uv pip install -e .`)

**tttool not found**: Install tttool ([instructions](installation.md)), check PATH

**Port in use**: Use different port (`ttmp32gme --port 8080`)

**Permission errors**: Use virtual environment or `uv pip install --user -e .` or `pip install --user -e .`

## Upload Issues

- **Files won't upload**: Check file size (<500MB), format (MP3/OGG only)
- **Metadata missing**: Edit manually in Library page or re-tag files with Mp3tag

## Library Issues

- **Album missing**: Refresh page (F5)
- **GME creation fails**: Check tttool installed, disk space available
- **OID in use**: Choose different OID number (1-999)

## Print Issues

**OID codes not recognized**:
1. Print at 100% scale, no auto-scaling
2. Use 1200 DPI or higher
3. Test with [OID table](https://github.com/thawn/ttmp32gme/blob/master/src/assets/images/oid-table.png)
4. If test table fails, it's a printer issue
5. Try: increase pixels per dot (3 or 4), better paper, graphics mode

**Quality issues**: Clean print heads, replace ink/toner, use smooth white paper

## TipToi Pen

- **Not detected**: Check USB connection, reload library page
- **Copy fails**: Check pen storage space
- **No audio**: Verify GME file copied, OID numbers match

## Server Warnings

**"WARNING: This is a development server"**:

This warning appears when running with `-v` (verbose mode) and indicates Flask's built-in development server is in use. This is normal and acceptable for:
- Personal use on your local machine
- Development and testing

**Why the warning?**
- Flask's development server is single-threaded and not optimized for performance
- It lacks production-grade security features
- Not designed for handling many concurrent connections

**Should you worry?**
- **For local use**: No, it's perfectly fine
- **For Docker/network deployment**: The Docker image uses Waitress (a production WSGI server) automatically
- **For public internet exposure**: Don't expose directly; use a reverse proxy (nginx, Apache) or container orchestration

## Getting Help

Search [GitHub issues](https://github.com/thawn/ttmp32gme/issues) or create new issue with:
- OS and versions
- Error messages
- What you tried
- For print issues: printer model, whether test table works
