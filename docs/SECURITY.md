# SQL Injection Protection

## Security Requirements for Database Operations

All database operations in this project must follow these security guidelines to prevent SQL injection attacks.

### 1. Always Use Parameterized Queries

**Required:** All data values MUST use SQLite parameterized queries with `?` placeholders.

```python
# ✅ Correct - parameterized query
db.execute("SELECT * FROM tracks WHERE parent_oid=?", (oid,))
db.execute("UPDATE config SET value=? WHERE param=?", (value, param))

# ❌ Wrong - string concatenation
db.execute(f"SELECT * FROM tracks WHERE parent_oid={oid}")
db.execute("UPDATE config SET value='" + value + "' WHERE param='" + param + "'")
```

### 2. Validate Table Names

**Required:** Use only tables from the `VALID_TABLES` whitelist defined in `DBHandler`:

```python
VALID_TABLES = {"config", "gme_library", "script_codes", "tracks"}
```

When adding new tables, update this whitelist. The `_validate_table_name()` method will reject any table not in this set.

### 3. Validate Field Names

**Required:** All field names must be validated against the database schema before use in SQL queries.

The `DBHandler` class provides validation methods:
- `_validate_field_names(table, fields)` - Validates field names against schema
- `_populate_valid_columns()` - Caches valid column names from `PRAGMA table_info()`

When using `write_to_database()` or `update_table_entry()`, field validation is automatic. For custom queries with dynamic field names, validate explicitly.

### 4. Security Test Requirements

When adding new database operations, add tests in `tests/test_sql_injection.py` to verify:

1. Malicious field names are rejected
2. Malicious values are safely parameterized
3. Valid operations still work correctly

Example test structure:
```python
def test_new_operation_field_injection(temp_db):
    malicious_data = {"valid_field": "value", "'; DROP TABLE--": "attack"}
    with pytest.raises(ValueError, match="Invalid field names"):
        temp_db.new_operation(malicious_data)
```

### 5. Data Source Protections

All data sources are protected:
- **Web frontend:** Pydantic validation + field name validation
- **MP3/OGG ID3 tags:** Values parameterized automatically
- **File names/paths:** Sanitized via `cleanup_filename()` + parameterized

### Quick Reference

| Operation | Security Method | Location |
|-----------|----------------|----------|
| Table name validation | `_validate_table_name()` | `db_handler.py` |
| Field name validation | `_validate_field_names()` | `db_handler.py` |
| Value parameterization | `execute(query, params)` | All database calls |
| Security tests | Test suite | `tests/test_sql_injection.py` |

### Adding New Database Operations

When implementing new database operations:

1. Use `db.execute(query, params)` with parameterized queries for all values
2. Use tables from `VALID_TABLES` only (or update the whitelist)
3. For dynamic fields, use `write_to_database()` or `update_table_entry()` which include validation
4. Add security tests to verify injection protection
5. Run CodeQL scanner: `codeql_checker` tool available in development environment
