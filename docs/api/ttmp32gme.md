# ttmp32gme Module

Main Flask application module for ttmp32gme.

```{eval-rst}
.. automodule:: ttmp32gme.ttmp32gme
   :members:
   :undoc-members:
   :show-inheritance:
```

## Module Overview

The `ttmp32gme` module is the main entry point for the application. It sets up and runs the Flask web server that provides the user interface and API.

## Key Components

### Flask Application Setup

The module creates a Flask application with:
* Static files served from `../assets`
* Templates loaded from `../templates`
* Maximum upload size of 500 MB
* Configured logging

### Global State

The module maintains global state for:
* Database handler instance
* Application configuration
* Current album and file tracking
* Custom database and library paths

### Main Functions

#### get_db()

Get or create the database handler instance.

Returns the singleton DBHandler instance, creating it if necessary. Handles custom database paths if specified via command line.

**Returns**: DBHandler instance

#### fetch_config()

Fetch configuration from the database.

Loads configuration from the database and applies custom paths if specified via command line options.

**Returns**: Dictionary with configuration settings

#### main()

Main entry point for the application.

Parses command line arguments, initializes the application, and starts the Flask development server.

**Command Line Arguments**:
* `--port`, `-p`: Server port (default: 10020)
* `--host`: Server host (default: 127.0.0.1)
* `--database`: Custom database file path
* `--library`: Custom library directory
* `--debug`, `-d`: Enable debug mode
* `--version`, `-v`: Show version

## Routes

### Page Routes

**GET /**
* Upload page (home page)
* Template: `upload.html`

**GET /library**
* Library management page
* Template: `library.html`

**GET /print**
* Print layout configuration page
* Template: `print.html`

**GET /help**
* Help and documentation page
* Template: `help.html`

**GET /config**
* Configuration page
* Template: `config.html`

### API Routes

**POST /api/upload**
* Upload audio files and cover image
* Accepts: multipart/form-data
* Returns: JSON with upload status

**GET /api/albums**
* List all albums
* Returns: JSON array of album objects

**POST /api/create_gme**
* Create GME file for album
* Body: `{"uid": album_oid}`
* Returns: JSON with success status

**POST /api/copy_to_tiptoi**
* Copy GME files to TipToi pen
* Body: `{"uids": [oid1, oid2, ...]}`
* Returns: JSON with copy results

**POST /api/delete_album**
* Delete album from library
* Body: `{"uid": album_oid}`
* Returns: JSON with success status

**GET /api/config**
* Get current configuration
* Returns: JSON configuration object

**POST /api/config**
* Update configuration
* Body: Configuration fields
* Returns: JSON with updated config

**GET /api/tiptoi_status**
* Check TipToi pen connection
* Returns: JSON with connection status

**GET /images/<filename>**
* Serve OID code images
* Returns: Image file

## Usage Example

```python
# Run with default settings
python -m ttmp32gme.ttmp32gme

# Run with custom port
python -m ttmp32gme.ttmp32gme --port 8080

# Run with custom paths
python -m ttmp32gme.ttmp32gme \
    --database /path/to/db.sqlite \
    --library /path/to/library

# Run in debug mode
python -m ttmp32gme.ttmp32gme --debug
```

## Configuration

The module uses these configuration values:

* `host`: Server host address (default: 127.0.0.1)
* `port`: Server port (default: 10020)
* `library_path`: Directory for album storage
* `audio_format`: MP3 or OGG format
* `pen_language`: Language for TipToi pen
* `open_browser`: Auto-open browser on startup

## Dependencies

Required packages:
* Flask >= 3.0.0
* Werkzeug >= 3.0.0
* Pydantic >= 2.0.0
* Mutagen >= 1.47.0
* Pillow >= 10.0.0
* Packaging >= 23.0

External tools:
* tttool (required for GME creation)
* ffmpeg (optional for OGG support)

## See Also

* [db_handler](db_handler.md) - Database layer
* [tttool_handler](tttool_handler.md) - GME file creation
* [print_handler](print_handler.md) - Print layout generation
