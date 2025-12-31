# ttmp32gme Module

Main Flask application for ttmp32gme.

```{eval-rst}
.. automodule:: ttmp32gme.ttmp32gme
   :members:
   :undoc-members:
   :show-inheritance:
```

## Overview

Flask web server providing UI and REST API for ttmp32gme.

## Key Functions

**get_db()**: Get/create DBHandler singleton

**fetch_config()**: Load configuration from database

**main()**: Entry point - parses args, starts server

## Routes

**Pages**: `/` (upload), `/library`, `/print`, `/help`, `/config`

**API**: `/api/upload`, `/api/albums`, `/api/create_gme`, `/api/copy_to_tiptoi`, `/api/delete_album`, `/api/config`, `/api/tiptoi_status`

**Assets**: `/images/<filename>` - Serve OID images

## Command Line

```bash
python -m ttmp32gme.ttmp32gme [OPTIONS]

Options:
  --port, -p PORT         Server port (default: 10020)
  --host HOST            Server host (default: 127.0.0.1)
  --database DATABASE    Custom database path
  --library LIBRARY      Custom library path
  --debug, -d            Debug mode
  --version, -v          Show version
```

## Configuration

- `host`: Server address (127.0.0.1)
- `port`: Server port (10020)
- `library_path`: Album storage directory
- `audio_format`: MP3 or OGG
- `pen_language`: TipToi language
