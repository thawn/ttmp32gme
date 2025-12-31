# API Reference

This section contains the auto-generated API documentation for ttmp32gme modules.

## Modules

The ttmp32gme package consists of several modules:

### Core Modules

```{toctree}
:maxdepth: 2

ttmp32gme
db_handler
tttool_handler
print_handler
file_handler
```

## Module Overview

### ttmp32gme

The main Flask application module that handles:
* Web server setup and configuration
* Route definitions (upload, library, print, config)
* Request/response handling
* File upload processing
* Template rendering

See [ttmp32gme module](ttmp32gme.md) for details.

### db_handler

Database layer providing thread-safe SQLite access:
* DBHandler class for all database operations
* Pydantic models for input validation
* Album, track, and configuration management
* Script code management for OID generation

See [db_handler module](db_handler.md) for details.

### tttool_handler

Interface to the tttool binary for GME operations:
* GME file creation from audio files
* OID code generation and management
* YAML configuration file generation
* TipToi pen detection and file copying
* Track sorting and organization

See [tttool_handler module](tttool_handler.md) for details.

### print_handler

Print layout generation:
* HTML layout generation for printing
* OID code image creation
* Track list formatting
* Control button creation
* PDF generation (platform-specific)

See [print_handler module](print_handler.md) for details.

### file_handler

File system operations:
* Album directory management
* Filename sanitization
* TipToi pen mount point detection
* Configuration file initialization
* Path management utilities

See [file_handler module](file_handler.md) for details.

## REST API Endpoints

ttmp32gme exposes several REST API endpoints for programmatic access:

### Album Management

**GET /api/albums**
* List all albums in library
* Returns: JSON array of album objects

**POST /api/albums**
* Create new album
* Body: Album metadata (title, artist, etc.)
* Returns: Created album object with OID

**PUT /api/albums/{oid}**
* Update album information
* Body: Fields to update
* Returns: Updated album object

**DELETE /api/albums/{oid}**
* Delete album from library
* Returns: Success status

### GME Operations

**POST /api/create_gme**
* Create GME file for album
* Body: `{"uid": album_oid}`
* Returns: Success status and GME file path

**POST /api/copy_to_tiptoi**
* Copy GME files to TipToi pen
* Body: `{"uids": [oid1, oid2, ...]}`
* Returns: Success status and copy results

### File Upload

**POST /api/upload**
* Upload audio files and cover image
* Body: Multipart form data with files
* Returns: Upload status and album information

### Configuration

**GET /api/config**
* Get current configuration
* Returns: Configuration object

**POST /api/config**
* Update configuration
* Body: Configuration fields to update
* Returns: Updated configuration

### System

**GET /api/tiptoi_status**
* Check if TipToi pen is connected
* Returns: Connection status and mount point

**GET /api/version**
* Get ttmp32gme version
* Returns: Version string

## Usage Examples

### Python Client Example

```python
import requests

# Base URL
base_url = "http://localhost:10020"

# Get all albums
response = requests.get(f"{base_url}/api/albums")
albums = response.json()

# Create GME for album
response = requests.post(
    f"{base_url}/api/create_gme",
    json={"uid": 123}
)
result = response.json()

# Update album
response = requests.put(
    f"{base_url}/api/albums/123",
    json={"album_title": "New Title"}
)
```

### JavaScript/jQuery Example

```javascript
// Get all albums
$.get('/api/albums', function(albums) {
    console.log('Albums:', albums);
});

// Create GME
$.ajax({
    url: '/api/create_gme',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({uid: 123}),
    success: function(result) {
        console.log('GME created:', result);
    }
});

// Update album
$.ajax({
    url: '/api/albums/123',
    method: 'PUT',
    contentType: 'application/json',
    data: JSON.stringify({album_title: 'New Title'}),
    success: function(album) {
        console.log('Updated:', album);
    }
});
```

### cURL Examples

```bash
# Get all albums
curl http://localhost:10020/api/albums

# Create GME
curl -X POST http://localhost:10020/api/create_gme \
    -H "Content-Type: application/json" \
    -d '{"uid": 123}'

# Update album
curl -X PUT http://localhost:10020/api/albums/123 \
    -H "Content-Type: application/json" \
    -d '{"album_title": "New Title"}'

# Upload files
curl -X POST http://localhost:10020/api/upload \
    -F "files=@track1.mp3" \
    -F "files=@track2.mp3" \
    -F "cover=@cover.jpg"
```

## Data Models

### Album Object

```json
{
    "oid": 123,
    "album_title": "Album Title",
    "album_artist": "Artist Name",
    "album_year": "2024",
    "num_tracks": 10,
    "cover_image": "cover.jpg",
    "path": "/path/to/album",
    "player_mode": "music",
    "created_at": "2024-01-01T00:00:00"
}
```

### Track Object

```json
{
    "id": 1,
    "album_oid": 123,
    "track_number": 1,
    "track_title": "Track Title",
    "filename": "track01.mp3"
}
```

### Config Object

```json
{
    "host": "127.0.0.1",
    "port": 10020,
    "library_path": "/home/user/.ttmp32gme/library",
    "audio_format": "mp3",
    "pen_language": "GERMAN"
}
```

## Error Responses

All API endpoints return errors in this format:

```json
{
    "success": false,
    "error": "Error message description"
}
```

Common HTTP status codes:
* `200 OK` - Success
* `400 Bad Request` - Invalid input
* `404 Not Found` - Resource not found
* `500 Internal Server Error` - Server error

## Rate Limiting

Currently, ttmp32gme does not implement rate limiting. However, GME creation operations are resource-intensive and should not be called too frequently.

## Authentication

The current version of ttmp32gme does not require authentication. It is designed for local use only. If you expose ttmp32gme to a network, consider:

* Using firewall rules to restrict access
* Running behind a reverse proxy with authentication
* Using SSH tunneling for remote access

## Next Steps

* Explore individual [module documentation](ttmp32gme.md)
* Check the [development guide](../development.md) for implementation details
* See [usage examples](../usage.md) for practical applications
