# file_handler Module

File system operations for ttmp32gme.

```{eval-rst}
.. automodule:: ttmp32gme.build.file_handler
   :members:
   :undoc-members:
   :show-inheritance:
```

## Key Functions

**make_new_album_dir(library_path, album_title, album_artist)**: Create album directory

**remove_album(album_path)**: Delete album and contents

**cleanup_filename(filename)**: Sanitize filename (remove special chars, replace spaces)

**get_tiptoi_dir()**: Detect TipToi mount point (searches common locations)

**check_config_file()**: Initialize config database (`~/.ttmp32gme/config.sqlite`)

**get_default_library_path()**: Get default library location (`~/.ttmp32gme/library`)

**get_oid_cache()**: Get OID image cache directory

**open_browser(url)**: Open URL in system browser

## Usage

```python
from ttmp32gme.build.file_handler import make_new_album_dir, get_tiptoi_dir

# Create album
album_dir = make_new_album_dir("/path/to/library", "Album", "Artist")

# Detect TipToi
tiptoi = get_tiptoi_dir()
if tiptoi:
    print(f"Found at: {tiptoi}")
```
