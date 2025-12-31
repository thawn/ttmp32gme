# API Reference

Auto-generated API documentation for ttmp32gme modules.

## Modules

```{toctree}
:maxdepth: 2

ttmp32gme
db_handler
tttool_handler
print_handler
file_handler
```

## REST API Endpoints

**Album Management**:
- `GET /api/albums` - List albums
- `POST /api/albums` - Create album
- `PUT /api/albums/{oid}` - Update album
- `DELETE /api/albums/{oid}` - Delete album

**GME Operations**:
- `POST /api/create_gme` - Create GME file
- `POST /api/copy_to_tiptoi` - Copy to pen

**File Upload**:
- `POST /api/upload` - Upload files

**Configuration**:
- `GET /api/config` - Get config
- `POST /api/config` - Update config

**System**:
- `GET /api/tiptoi_status` - Check pen connection
- `GET /api/version` - Get version

## Usage Examples

### Python

```python
import requests

base = "http://localhost:10020"

# List albums
albums = requests.get(f"{base}/api/albums").json()

# Create GME
result = requests.post(f"{base}/api/create_gme", json={"uid": 123}).json()

# Update album
requests.put(f"{base}/api/albums/123", json={"album_title": "New Title"})
```

### cURL

```bash
# List albums
curl http://localhost:10020/api/albums

# Create GME
curl -X POST http://localhost:10020/api/create_gme \
  -H "Content-Type: application/json" \
  -d '{"uid": 123}'

# Upload files
curl -X POST http://localhost:10020/api/upload \
  -F "files=@track1.mp3" \
  -F "cover=@cover.jpg"
```

## Data Models

**Album**: `{oid, album_title, album_artist, num_tracks, cover_image, player_mode}`

**Track**: `{id, album_oid, track_number, track_title, filename}`

**Config**: `{host, port, library_path, audio_format, pen_language}`

**Error**: `{success: false, error: "message"}`
