# db_handler Module

Database layer for ttmp32gme providing thread-safe SQLite access.

```{eval-rst}
.. automodule:: ttmp32gme.db_handler
   :members:
   :undoc-members:
   :show-inheritance:
```

## Module Overview

The `db_handler` module provides the database layer for ttmp32gme. It includes:

* `DBHandler` class for all database operations
* Pydantic models for input validation
* Thread-safe SQLite connection management
* Album, track, and configuration data management

## Key Principles

**CRITICAL**: All database operations MUST go through DBHandler methods.

```python
# ✅ Correct
result = db.fetchone("SELECT * FROM albums WHERE oid = ?", (oid,))

# ❌ Wrong - Never use raw cursors
cursor = db.cursor()
cursor.execute("SELECT * FROM albums WHERE oid = ?", (oid,))
```

## DBHandler Class

The main database handler class providing all database operations.

### Initialization

```python
from ttmp32gme.db_handler import DBHandler

db = DBHandler("/path/to/database.sqlite")
db.connect()
```

### Core Methods

#### connect()

Establish connection to the SQLite database.

Sets `check_same_thread=False` for Flask's multi-threaded environment.

#### execute(query, params)

Execute SQL query with parameters.

**Parameters**:
* `query` (str): SQL query string
* `params` (tuple): Query parameters

**Returns**: Cursor object

#### fetchone(query, params)

Execute query and fetch one result.

**Parameters**:
* `query` (str): SQL query
* `params` (tuple): Query parameters

**Returns**: Single row as tuple or None

#### fetchall(query, params)

Execute query and fetch all results.

**Parameters**:
* `query` (str): SQL query
* `params` (tuple): Query parameters

**Returns**: List of rows as tuples

#### commit()

Commit current transaction.

### Album Operations

#### get_album(oid)

Get album by OID.

**Parameters**:
* `oid` (int): Album OID

**Returns**: Dictionary with album data

#### get_all_albums()

Get all albums in library.

**Returns**: List of album dictionaries

#### create_album(album_data)

Create new album.

**Parameters**:
* `album_data` (dict): Album information

**Returns**: Created album OID

#### update_album(oid, updates)

Update album information.

**Parameters**:
* `oid` (int): Album OID
* `updates` (dict): Fields to update

#### delete_album(oid)

Delete album from database.

**Parameters**:
* `oid` (int): Album OID to delete

### Track Operations

#### get_tracks(album_oid)

Get all tracks for an album.

**Parameters**:
* `album_oid` (int): Album OID

**Returns**: List of track dictionaries

#### create_track(track_data)

Create new track.

**Parameters**:
* `track_data` (dict): Track information

**Returns**: Created track ID

#### update_track(track_id, updates)

Update track information.

**Parameters**:
* `track_id` (int): Track ID
* `updates` (dict): Fields to update

### Configuration Operations

#### get_config()

Get all configuration settings.

**Returns**: Dictionary of config key-value pairs

#### get_config_value(key)

Get specific configuration value.

**Parameters**:
* `key` (str): Configuration key

**Returns**: Configuration value or None

#### set_config_value(key, value)

Set configuration value.

**Parameters**:
* `key` (str): Configuration key
* `value` (str): Configuration value

### Script Code Operations

#### get_script_code(script_name)

Get OID code for a script.

**Parameters**:
* `script_name` (str): Script name (e.g., "t0", "play")

**Returns**: OID code integer or None

#### set_script_code(script_name, code)

Set OID code for a script.

**Parameters**:
* `script_name` (str): Script name
* `code` (int): OID code (1001-14999)

#### get_all_script_codes()

Get all script code mappings.

**Returns**: Dictionary mapping script names to codes

## Pydantic Models

### AlbumUpdateModel

Validates album update data from frontend.

**Fields**:
* `oid` (Optional[int]): Album OID
* `uid` (Optional[int]): Album UID (alias for OID)
* `old_oid` (Optional[int]): Previous OID if changing
* `album_title` (Optional[str]): Album title (max 255 chars)
* `album_artist` (Optional[str]): Artist name (max 255 chars)
* `num_tracks` (Optional[int]): Number of tracks (0-999)
* `player_mode` (Optional[str]): "music" or "tiptoi"
* `cover` (Optional[str]): Cover image path

Allows dynamic track fields (track1_title, track2_title, etc.).

### ConfigUpdateModel

Validates configuration update data.

**Fields**:
* `host` (Optional[str]): Host address (alphanumeric)
* `port` (Optional[int]): Port number (1-65535)
* `open_browser` (Optional[bool]): Auto-open browser flag
* `audio_format` (Optional[str]): "mp3" or "ogg"
* `pen_language` (Optional[str]): Pen language (max 50 chars)
* `library_path` (Optional[str]): Library directory path (max 500 chars)

### LibraryActionModel

Validates library action data (delete, make_gme, etc.).

**Fields**:
* `uid` (int): Album OID/UID (required)
* `tiptoi_dir` (Optional[str]): TipToi mount point

### AlbumMetadataModel

Validates album-level metadata from audio files.

**Fields**:
* `oid` (int): Album OID (0-1000)
* `album_title` (str): Album title (required, max 255 chars)
* `album_artist` (Optional[str]): Artist (max 255 chars)
* `album_year` (Optional[str]): Year (max 10 chars)
* `num_tracks` (int): Track count (0-999)
* `picture_filename` (Optional[str]): Cover filename (max 255 chars)
* `path` (str): Album directory path (required, max 500 chars)

## Usage Examples

### Basic Database Operations

```python
from ttmp32gme.db_handler import DBHandler

# Initialize
db = DBHandler("/path/to/config.sqlite")
db.connect()

# Get all albums
albums = db.get_all_albums()

# Get specific album
album = db.get_album(123)

# Update album
db.update_album(123, {
    "album_title": "New Title",
    "album_artist": "New Artist"
})

# Get tracks
tracks = db.get_tracks(123)
```

### Using Pydantic Validation

```python
from ttmp32gme.db_handler import AlbumUpdateModel
from pydantic import ValidationError

# Validate input
try:
    validated = AlbumUpdateModel(**request_data)
    db.update_album(validated.oid, validated.model_dump(exclude_none=True))
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Configuration Management

```python
# Get all config
config = db.get_config()

# Get specific value
port = db.get_config_value("port")

# Set value
db.set_config_value("port", "8080")
```

## Database Schema

### albums Table

```sql
CREATE TABLE albums (
    oid INTEGER PRIMARY KEY,
    album_title TEXT NOT NULL,
    album_artist TEXT,
    album_year TEXT,
    num_tracks INTEGER,
    cover_image TEXT,
    path TEXT NOT NULL,
    player_mode TEXT DEFAULT 'music',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### tracks Table

```sql
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_oid INTEGER NOT NULL,
    track_number INTEGER NOT NULL,
    track_title TEXT,
    filename TEXT NOT NULL,
    FOREIGN KEY (album_oid) REFERENCES albums(oid)
);
```

### script_codes Table

```sql
CREATE TABLE script_codes (
    script TEXT PRIMARY KEY,
    code INTEGER UNIQUE NOT NULL
);
```

### config Table

```sql
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

## Thread Safety

The DBHandler uses `check_same_thread=False` to allow the SQLite connection to be used across multiple threads in Flask's environment. This is safe because:

* SQLite serializes writes internally
* Reads are safe to concurrent access
* Flask request handlers are isolated

## Best Practices

1. **Always use DBHandler methods** - Never use raw cursors
2. **Validate input** - Use Pydantic models for all external input
3. **Use parameters** - Never concatenate SQL queries
4. **Handle errors** - Catch and handle database exceptions
5. **Close connections** - Ensure connections are closed when done

## See Also

* [ttmp32gme](ttmp32gme.md) - Main application
* [Development Guide](../development.md) - Database conventions
