# file_handler Module

File system operations module for ttmp32gme.

```{eval-rst}
.. automodule:: ttmp32gme.build.file_handler
   :members:
   :undoc-members:
   :show-inheritance:
```

## Module Overview

The `file_handler` module provides file system operations for ttmp32gme. It handles:

* Album directory management
* Filename sanitization and cleanup
* TipToi pen mount point detection
* Configuration file initialization
* Path management utilities
* Browser launching

## Key Functions

### make_new_album_dir(library_path, album_title, album_artist)

Create a new album directory in the library.

Sanitizes the album and artist names and creates a uniquely named directory.

**Parameters**:
* `library_path` (str): Root library directory path
* `album_title` (str): Album title
* `album_artist` (str): Artist name

**Returns**: Path object for created directory

**Naming Convention**:
* Format: `{artist}_{album}_{timestamp}`
* Example: `Artist_Name_Album_Title_20240101_120000`

**Example**:
```python
album_dir = make_new_album_dir(
    library_path="/home/user/.ttmp32gme/library",
    album_title="My Album",
    album_artist="My Artist"
)
print(f"Created: {album_dir}")
```

### remove_album(album_path)

Remove album directory and all contents.

Safely deletes an album directory including all audio files and metadata.

**Parameters**:
* `album_path` (str): Path to album directory

**Returns**: Boolean indicating success

**Safety**:
* Validates path is within library
* Checks for empty directory
* Handles file locks gracefully

**Example**:
```python
success = remove_album("/path/to/album/dir")
if success:
    print("Album removed successfully")
```

### cleanup_filename(filename)

Sanitize filename for safe file system use.

Removes or replaces problematic characters in filenames.

**Parameters**:
* `filename` (str): Original filename

**Returns**: Cleaned filename string

**Transformations**:
* Remove special characters: `!@#$%^&*()+=[]{}|;:'",<>?/\`
* Replace spaces with underscores
* Remove leading/trailing whitespace
* Preserve file extensions
* Limit length if necessary

**Example**:
```python
clean = cleanup_filename("Track #1: Title (Remix).mp3")
# Result: "Track_1_Title_Remix.mp3"
```

### get_tiptoi_dir()

Detect TipToi pen mount point.

Searches common mount locations for a connected TipToi pen.

**Returns**: Path to TipToi mount point or None if not found

**Search Locations**:
* Linux: `/media/*/tiptoi/`, `/mnt/tiptoi/`
* macOS: `/Volumes/tiptoi/`
* Windows: `D:\`, `E:\`, `F:\`, etc.

**Detection**:
* Checks for writable directory
* Verifies has "GME" folder or recognizable structure
* Returns first valid mount point found

**Example**:
```python
tiptoi = get_tiptoi_dir()
if tiptoi:
    print(f"TipToi found at: {tiptoi}")
else:
    print("TipToi not connected")
```

### check_config_file()

Initialize configuration database file.

Creates the configuration database if it doesn't exist, copying from defaults.

**Returns**: Path to configuration file

**Locations**:
* Linux/macOS: `~/.ttmp32gme/config.sqlite`
* Windows: `%USERPROFILE%\.ttmp32gme\config.sqlite`

**Initialization**:
* Creates parent directory if needed
* Copies default config from package
* Sets appropriate permissions

**Example**:
```python
config_file = check_config_file()
print(f"Config: {config_file}")
```

### get_default_library_path()

Get default library path for the platform.

**Returns**: Path object for default library location

**Default Paths**:
* Linux/macOS: `~/.ttmp32gme/library`
* Windows: `%USERPROFILE%\.ttmp32gme\library`

**Example**:
```python
library = get_default_library_path()
print(f"Library: {library}")
```

### get_executable_path()

Get path to the running executable or script.

Useful for locating resources relative to the application.

**Returns**: Path to executable or script directory

**Use Cases**:
* Finding bundled resources
* Locating configuration templates
* Determining installation directory

### get_oid_cache()

Get path to OID image cache directory.

OID code images are cached to avoid regeneration.

**Returns**: Path to cache directory

**Cache Structure**:
```
~/.ttmp32gme/cache/oids/
├── oid_2001.png
├── oid_2002.png
└── oid_2003.png
```

**Example**:
```python
cache_dir = get_oid_cache()
oid_file = cache_dir / f"oid_{code}.png"
```

### open_browser(url)

Open URL in system default browser.

**Parameters**:
* `url` (str): URL to open

**Returns**: Boolean indicating success

**Behavior**:
* Uses system default browser
* Non-blocking (doesn't wait for browser)
* Handles errors gracefully

**Example**:
```python
open_browser("http://localhost:10020")
```

### make_temp_album_dir()

Create temporary directory for album processing.

Used for temporary storage during upload and conversion.

**Returns**: Path to temporary directory

**Cleanup**:
* Caller responsible for cleanup
* Use with context manager if possible

**Example**:
```python
temp_dir = make_temp_album_dir()
try:
    # Process files in temp_dir
    pass
finally:
    shutil.rmtree(temp_dir)
```

## Path Utilities

### Path Validation

Functions validate paths for security:

```python
def is_safe_path(path, base_dir):
    """Check if path is within base directory."""
    resolved = Path(path).resolve()
    base = Path(base_dir).resolve()
    return str(resolved).startswith(str(base))
```

### Path Normalization

```python
def normalize_path(path):
    """Normalize path for platform."""
    path = Path(path).expanduser()
    path = path.resolve()
    return path
```

## File Operations

### Safe Copy

```python
def safe_copy(src, dst):
    """Copy file with error handling."""
    try:
        shutil.copy2(src, dst)
        return True
    except (IOError, OSError) as e:
        logger.error(f"Copy failed: {e}")
        return False
```

### Safe Move

```python
def safe_move(src, dst):
    """Move file with error handling."""
    try:
        shutil.move(src, dst)
        return True
    except (IOError, OSError) as e:
        logger.error(f"Move failed: {e}")
        return False
```

## Directory Management

### Album Structure

Albums are organized hierarchically:

```
library/
└── Artist_Name_Album_Title_20240101_120000/
    ├── audio/
    │   ├── track01.mp3
    │   ├── track02.mp3
    │   └── ...
    ├── cover.jpg
    ├── album.yaml
    └── OID_0123.gme
```

### Cleanup Operations

```python
def cleanup_old_albums(library_path, days=30):
    """Remove albums older than specified days."""
    cutoff = datetime.now() - timedelta(days=days)
    for album_dir in Path(library_path).iterdir():
        if album_dir.is_dir():
            mtime = datetime.fromtimestamp(album_dir.stat().st_mtime)
            if mtime < cutoff:
                remove_album(str(album_dir))
```

## Platform-Specific Handling

### Windows

```python
def get_windows_mount_points():
    """Get list of drive letters."""
    import string
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives
```

### Linux

```python
def get_linux_mount_points():
    """Get list of mount points."""
    mount_points = []
    with open('/proc/mounts', 'r') as f:
        for line in f:
            parts = line.split()
            mount_points.append(parts[1])
    return mount_points
```

### macOS

```python
def get_macos_volumes():
    """Get list of volumes."""
    volumes_dir = Path('/Volumes')
    return [str(v) for v in volumes_dir.iterdir() if v.is_dir()]
```

## Usage Examples

### Complete Album Setup

```python
from ttmp32gme.build.file_handler import (
    make_new_album_dir,
    cleanup_filename,
    get_default_library_path
)

# Create album directory
library = get_default_library_path()
album_dir = make_new_album_dir(
    library_path=str(library),
    album_title="My Album",
    album_artist="My Artist"
)

# Process files
for original_file in uploaded_files:
    clean_name = cleanup_filename(original_file.name)
    target = album_dir / "audio" / clean_name
    original_file.save(str(target))
```

### TipToi Detection and Copy

```python
from ttmp32gme.build.file_handler import get_tiptoi_dir
import shutil

# Find TipToi
tiptoi = get_tiptoi_dir()

if tiptoi:
    # Copy GME file
    gme_file = Path(album_dir) / "OID_0123.gme"
    target = Path(tiptoi) / gme_file.name
    
    shutil.copy2(gme_file, target)
    print(f"Copied to {target}")
else:
    print("TipToi not found")
```

### Configuration Setup

```python
from ttmp32gme.build.file_handler import (
    check_config_file,
    get_default_library_path
)

# Initialize config
config_file = check_config_file()

# Get library path
library = get_default_library_path()

# Ensure library exists
library.mkdir(parents=True, exist_ok=True)
```

## Error Handling

### File System Errors

```python
try:
    album_dir = make_new_album_dir(library, title, artist)
except OSError as e:
    logger.error(f"Failed to create album: {e}")
    # Handle error (show message, retry, etc.)
```

### Permission Errors

```python
try:
    remove_album(album_path)
except PermissionError:
    logger.error("Permission denied")
    # Notify user of permission issue
```

## Security Considerations

### Path Traversal Prevention

```python
def validate_album_path(path, library_root):
    """Ensure path is within library."""
    path = Path(path).resolve()
    root = Path(library_root).resolve()
    
    if not str(path).startswith(str(root)):
        raise ValueError("Invalid path")
```

### Filename Sanitization

Always sanitize user-provided filenames:

```python
filename = cleanup_filename(user_input)
```

Never use raw user input in file paths.

## See Also

* [db_handler](db_handler.md) - Database operations
* [tttool_handler](tttool_handler.md) - Uses file operations
* [Development Guide](../development.md) - File structure conventions
