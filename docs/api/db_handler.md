# db_handler Module

Database layer for ttmp32gme with thread-safe SQLite access.

```{eval-rst}
.. automodule:: ttmp32gme.db_handler
   :members:
   :undoc-members:
   :show-inheritance:
```

## DBHandler Class

**CRITICAL**: All database operations MUST go through DBHandler methods.

```python
result = db.fetchone("SELECT ...")  # ✓
cursor = db.cursor()  # ✗ Never use raw cursors
```

### Core Methods

- `connect()` - Establish database connection
- `execute(query, params)` - Execute SQL
- `fetchone(query, params)` - Fetch one result
- `fetchall(query, params)` - Fetch all results
- `commit()` - Commit transaction

### Album Operations

- `get_album(oid)` - Get album by OID
- `get_all_albums()` - List all albums
- `create_album(data)` - Create new album
- `update_album(oid, updates)` - Update album
- `delete_album(oid)` - Delete album

### Track Operations

- `get_tracks(album_oid)` - Get tracks for album
- `create_track(data)` - Create track
- `update_track(track_id, updates)` - Update track

### Config Operations

- `get_config()` - Get all config
- `get_config_value(key)` - Get specific value
- `set_config_value(key, value)` - Set value

## Pydantic Models

**AlbumUpdateModel**: Validates album updates (oid, title, artist, tracks, mode)

**ConfigUpdateModel**: Validates config (host, port, audio_format, library_path)

**LibraryActionModel**: Validates actions (uid, tiptoi_dir)

**AlbumMetadataModel**: Validates metadata from audio files

## Usage

```python
from ttmp32gme.db_handler import DBHandler, AlbumUpdateModel
from pydantic import ValidationError

db = DBHandler("/path/to/db.sqlite")

# Validate and update
try:
    validated = AlbumUpdateModel(**data)
    db.update_album(validated.oid, validated.model_dump(exclude_none=True))
except ValidationError as e:
    print(f"Error: {e}")
```
