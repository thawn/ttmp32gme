# Security

## SQL Injection Protection

This application implements comprehensive SQL injection protection using multiple layers of defense:

### 1. Input Validation with Pydantic Models

All user inputs and ID3 tag data are validated through Pydantic models before being processed:

- **AlbumUpdateModel**: Validates user-submitted album updates
- **ConfigUpdateModel**: Validates configuration changes
- **AlbumMetadataModel**: Validates album metadata from ID3 tags
- **TrackMetadataModel**: Validates track metadata from ID3 tags

### 2. SQL Pattern Detection

String inputs are automatically scanned for common SQL injection patterns:

- SQL keywords (SELECT, INSERT, UPDATE, DELETE, DROP, etc.)
- SQL comments (`--`, `/*`, `*/`)
- Statement separators (`;`)
- Boolean logic attacks (e.g., `OR 1=1`, `AND 1=1`)
- UNION-based attacks

Any input containing these patterns is rejected with a clear error message.

### 3. Table and Column Name Whitelisting

Database operations validate table and column names against strict whitelists:

**Valid Tables:**
- `gme_library`: Album library
- `tracks`: Track information
- `config`: Configuration settings
- `script_codes`: TipToi script codes

**Valid Columns (by table):**
- `gme_library`: oid, album_title, album_artist, album_year, num_tracks, picture_filename, gme_file, path, player_mode
- `tracks`: parent_oid, album, artist, disc, duration, genre, lyrics, title, track, filename, tt_script
- `config`: param, value
- `script_codes`: script, code

Any attempt to use invalid table or column names is rejected.

### 4. XSS Protection

HTML and script content is sanitized using the `bleach` library:

- **Default behavior**: All HTML tags are stripped from inputs
- **Lyrics field**: Basic formatting tags (`<b>`, `<i>`, `<u>`, `<br>`, `<p>`) are allowed
- **Script tags**: Always removed to prevent XSS attacks

### 5. Parameterized Queries

All SQL queries use parameterized statements (with `?` placeholders) to prevent SQL injection through data values.

## Testing

The security features are covered by comprehensive unit tests in `tests/unit/test_sql_injection_protection.py`:

- 39 test cases covering SQL injection attempts
- XSS attack prevention
- Table/column name validation
- ID3 tag data sanitization
- User input validation

All tests pass and demonstrate that the application is hardened against common attack vectors.

## Reporting Security Issues

If you discover a security vulnerability, please report it to the maintainers privately rather than opening a public issue. This allows the team to address the vulnerability before it can be exploited.

## Security Best Practices

When using ttmp32gme:

1. **Keep dependencies up to date**: Regularly update the application and its dependencies
2. **Use secure configurations**: Don't expose the web interface to untrusted networks
3. **Validate MP3 sources**: Only process MP3 files from trusted sources
4. **Review logs**: Check application logs for suspicious activity
5. **Backup data**: Regularly backup your library database

## Dependencies

Security-relevant dependencies:

- **bleach>=6.0.0**: HTML sanitization library (no known vulnerabilities)
- **pydantic>=2.0.0**: Data validation framework
- **flask>=3.0.0**: Web framework with built-in security features

All dependencies are regularly scanned for known vulnerabilities using the GitHub Advisory Database.
