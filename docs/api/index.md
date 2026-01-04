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

## HTTP API Endpoints

**Pages**:
- `GET /` - Upload page
- `POST /` - Upload files
- `GET /library` - Library page
- `POST /library` - Library actions (create GME, copy to TipToi, delete album)
- `GET /print` - Print page
- `POST /print` - Print actions
- `GET /pdf` - Generate PDF
- `GET /config` - Config page
- `POST /config` - Update config
- `GET /help` - Help page
- `GET /logs` - View logs
- `POST /logs/level` - Set log level

**Resources**:
- `GET /images/<filename>` - Serve OID images
- `GET /download_gme/<oid>` - Download GME file
- `GET /download_oid_images` - Download OID pattern test sheet

## Usage Examples

### Python

```python
import requests

base = "http://localhost:10020"

# Create GME file
result = requests.post(f"{base}/library",
                      data={"action": "create_gme", "uid": "123"}).json()

# Update config
requests.post(f"{base}/config",
             data={"audio_format": "mp3", "pen_language": "GERMAN"})

# Download GME
response = requests.get(f"{base}/download_gme/123")
with open("album.gme", "wb") as f:
    f.write(response.content)
```

### cURL

```bash
# Create GME
curl -X POST http://localhost:10020/library \
  -d "action=create_gme" \
  -d "uid=123"

# Upload files
curl -X POST http://localhost:10020/ \
  -F "files=@track1.mp3" \
  -F "cover=@cover.jpg"

# Download GME
curl -O http://localhost:10020/download_gme/123
```

## Data Models

**Album**: `{oid, album_title, album_artist, num_tracks, cover_image, player_mode}`

**Track**: `{id, album_oid, track_number, track_title, filename}`

**Config**: `{host, port, library_path, audio_format, pen_language}`
