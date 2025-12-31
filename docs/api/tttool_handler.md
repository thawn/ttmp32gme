# tttool_handler Module

Interface to the tttool binary for GME file operations.

```{eval-rst}
.. automodule:: ttmp32gme.tttool_handler
   :members:
   :undoc-members:
   :show-inheritance:
```

## Module Overview

The `tttool_handler` module provides the interface to the tttool binary for creating and managing GME files. It handles:

* GME file creation from audio files
* OID code generation and management
* YAML configuration file generation
* TipToi pen detection and file operations
* Track sorting and organization

## Key Functions

### make_gme(album_id, db_handler, config)

Create GME file for an album.

Converts audio files to GME format using tttool. This is the main function for GME creation.

**Parameters**:
* `album_id` (int): Album OID
* `db_handler` (DBHandler): Database handler instance
* `config` (dict): Application configuration

**Returns**: Dictionary with success status and GME file path

**Process**:
1. Get album information from database
2. Generate YAML configuration file
3. Generate OID code mappings
4. Call tttool to assemble GME file
5. Store result and update database

**Example**:
```python
result = make_gme(123, db, config)
if result['success']:
    print(f"GME created: {result['gme_file']}")
```

### generate_codes_yaml(yaml_file, db_handler)

Generate script codes YAML file with OID code mappings.

Reads script names from the main YAML file and assigns OID codes to each script. Reuses existing codes from database when available, assigns new codes otherwise.

**Parameters**:
* `yaml_file` (Path): Path to main album YAML file
* `db_handler` (DBHandler): Database handler instance

**Returns**: Path to generated codes YAML file (.codes.yaml)

**Raises**:
* `RuntimeError`: If all script codes (1001-14999) are exhausted

**OID Code Allocation**:
* Range: 1001-14999 (reserved for script codes)
* Album OIDs: 1-999 (not in this range)
* Reuses existing codes when possible
* Assigns sequentially from 1001 upward

### create_oids(codes, size, db_handler)

Generate OID code images for printing.

Creates PNG images of OID patterns that can be read by the TipToi pen.

**Parameters**:
* `codes` (List[int]): List of OID codes to generate
* `size` (int): Image size in millimeters
* `db_handler` (DBHandler): Database handler instance

**Returns**: List of Path objects for created image files

**Image Properties**:
* Format: PNG with transparency
* Size: Configurable (typically 6mm or 24mm)
* Resolution: Matches print settings
* Location: Cached for reuse

**Example**:
```python
# Create OID images for track buttons
oid_files = create_oids([2001, 2002, 2003], 24, db)
for oid_file in oid_files:
    print(f"Created: {oid_file}")
```

### copy_gme(album_oid, tiptoi_dir, db_handler)

Copy GME file to TipToi pen.

Copies the GME file for an album to the connected TipToi pen.

**Parameters**:
* `album_oid` (int): Album OID
* `tiptoi_dir` (str): TipToi mount point directory
* `db_handler` (DBHandler): Database handler instance

**Returns**: Dictionary with success status

**Process**:
1. Verify GME file exists
2. Verify TipToi directory is accessible
3. Copy GME file to pen
4. Verify copy completed successfully

**Example**:
```python
tiptoi_dir = get_tiptoi_dir()
if tiptoi_dir:
    result = copy_gme(123, tiptoi_dir, db)
    print(f"Copy {'successful' if result['success'] else 'failed'}")
```

### delete_gme_tiptoi(album_oid, tiptoi_dir)

Delete GME file from TipToi pen.

**Parameters**:
* `album_oid` (int): Album OID
* `tiptoi_dir` (str): TipToi mount point

**Returns**: Dictionary with success status

### get_sorted_tracks(album)

Sort tracks by track number.

Returns track keys sorted by track number for proper ordering.

**Parameters**:
* `album` (dict): Album dictionary containing tracks

**Returns**: List of track keys sorted by track number

**Example**:
```python
album = db.get_album(123)
sorted_tracks = get_sorted_tracks(album)
for track_key in sorted_tracks:
    track = album[track_key]
    print(f"{track['track_number']}. {track['track_title']}")
```

## YAML Configuration

### Album YAML Structure

The main YAML file describes the album structure for tttool:

```yaml
product-id: 123
comment: Album Title - Artist Name
scripts:
  power_on:
    - $play:
  play:
    - P(track_1)
  track_1:
    - P(audio/track01)
  # ... more scripts
```

### Codes YAML Structure

The codes YAML maps script names to OID codes:

```yaml
power_on: 15000123
play: 2001
track_1: 2002
track_2: 2003
# ... more mappings
```

## OID Code Management

### Code Ranges

* **Product IDs (1-999)**: Album OIDs
* **Script Codes (1001-14999)**: Script actions
* **Reserved**: 0, 1000, 15000+

### Code Allocation

1. Check database for existing script code
2. If found, reuse existing code
3. If not found, allocate next available code
4. Store in database for future reuse
5. Generate codes YAML file

### Code Caching

Script codes are cached in the database to ensure:
* Consistency across reprints
* No duplicate codes
* Efficient code reuse

## TipToi Integration

### Pen Detection

The module can detect connected TipToi pens by checking common mount points:

* `/media/tiptoi/`
* `/media/$USER/tiptoi/`
* `/mnt/tiptoi/`
* Windows drive letters (D:, E:, etc.)

### File Naming

GME files follow this naming convention:
* Format: `OID_{oid:04d}.gme`
* Example: `OID_0123.gme` for album with OID 123

### Copy Process

1. Verify source GME exists
2. Check pen is mounted
3. Copy to pen's root directory
4. Verify copy succeeded
5. Return success status

## Audio Processing

### Supported Formats

Input formats:
* MP3 (direct support)
* OGG (requires ffmpeg conversion)

Output format:
* OGG (Vorbis codec)
* Optimized for TipToi pen

### Conversion Process

1. Check if conversion needed (MP3 → OGG)
2. Call ffmpeg if needed
3. Place converted files in album directory
4. tttool packages into GME file

## Error Handling

Common errors and handling:

**tttool Not Found**:
```python
try:
    result = make_gme(123, db, config)
except FileNotFoundError:
    print("tttool not installed")
```

**Invalid Audio Files**:
```python
if not result['success']:
    print(f"Error: {result['error']}")
```

**Code Exhaustion**:
```python
try:
    codes_yaml = generate_codes_yaml(yaml_file, db)
except RuntimeError as e:
    print(f"Out of codes: {e}")
```

## Performance Considerations

GME creation is resource-intensive:

* Takes 1-5 minutes per album
* CPU-intensive (audio encoding)
* Disk I/O intensive (large files)

Recommendations:
* Create GME files one at a time
* Show progress indicators
* Run in background if possible
* Cache OID images for reuse

## Usage Examples

### Complete GME Creation

```python
from ttmp32gme.tttool_handler import make_gme
from ttmp32gme.db_handler import DBHandler

# Initialize
db = DBHandler("/path/to/config.sqlite")
db.connect()
config = db.get_config()

# Create GME
result = make_gme(123, db, config)

if result['success']:
    print(f"Success! GME file: {result['gme_file']}")
else:
    print(f"Failed: {result['error']}")
```

### Copy to TipToi

```python
from ttmp32gme.tttool_handler import copy_gme
from ttmp32gme.build.file_handler import get_tiptoi_dir

# Detect pen
tiptoi_dir = get_tiptoi_dir()

if tiptoi_dir:
    # Copy album
    result = copy_gme(123, tiptoi_dir, db)
    if result['success']:
        print("Copied successfully!")
else:
    print("TipToi pen not found")
```

### Generate OID Images

```python
from ttmp32gme.tttool_handler import create_oids

# Create images for buttons
codes = [2001, 2002, 2003]  # play, pause, stop
images = create_oids(codes, 24, db)

for img in images:
    print(f"Created: {img}")
```

## Dependencies

Required:
* tttool (external binary)
* subprocess (Python standard library)

Optional:
* ffmpeg (for OGG conversion)

## See Also

* [print_handler](print_handler.md) - Uses OID images from this module
* [db_handler](db_handler.md) - Stores script code mappings
* [tttool documentation](https://tttool.readthedocs.io/)
