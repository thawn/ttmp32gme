# SQL Injection Protection

All database operations must prevent SQL injection attacks.

## Requirements

### 1. Parameterized Queries (Required)

Use SQLite parameterized queries with `?` placeholders for all data values.

```python
# ✅ Correct
db.execute("SELECT * FROM tracks WHERE parent_oid=?", (oid,))

# ❌ Wrong
db.execute(f"SELECT * FROM tracks WHERE parent_oid={oid}")
```

### 2. Validate Table Names (Required)

Use only whitelisted tables from `DBHandler.VALID_TABLES`:

```python
VALID_TABLES = {"config", "gme_library", "script_codes", "tracks"}
```

`_validate_table_name()` rejects invalid tables.

### 3. Validate Field Names (Required)

Field names validated against database schema before use.

**Methods**:
* `_validate_field_names(table, fields)` - Validates against schema
* `_populate_valid_columns()` - Caches valid columns from `PRAGMA table_info()`

`write_to_database()` and `update_table_entry()` validate automatically.

### 4. Security Tests (Required)

Add tests in `tests/test_sql_injection.py` for new database operations:

```python
def test_new_operation_field_injection(temp_db):
    malicious_data = {"valid_field": "value", "'; DROP TABLE--": "attack"}
    with pytest.raises(ValueError, match="Invalid field names"):
        temp_db.new_operation(malicious_data)
```

### 5. Data Source Protections

All inputs protected:
* **Web frontend**: Pydantic validation + field validation
* **MP3 ID3 tags**: Values parameterized automatically
* **File names**: Sanitized via `cleanup_filename()` + parameterized

## Quick Reference

| Security Method | Location |
|----------------|----------|
| Table validation | `DBHandler._validate_table_name()` |
| Field validation | `DBHandler._validate_field_names()` |
| Value parameterization | `db.execute(query, params)` |
| Security tests | `tests/test_sql_injection.py` |

## Checklist for New Database Operations

1. ✅ Use `db.execute(query, params)` with parameterized queries
2. ✅ Use tables from `VALID_TABLES` (or update whitelist)
3. ✅ Use `write_to_database()` or `update_table_entry()` for dynamic fields
4. ✅ Add security tests
5. ✅ Run CodeQL scanner before commit
