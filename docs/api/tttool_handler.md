# tttool_handler Module

Interface to tttool for GME file operations.

```{eval-rst}
.. automodule:: ttmp32gme.tttool_handler
   :members:
   :undoc-members:
   :show-inheritance:
```

## Key Functions

**make_gme(album_id, db_handler, config)**: Create GME file from audio files

**generate_codes_yaml(yaml_file, db_handler)**: Generate OID code mappings (1001-14999)

**create_oids(codes, size, db_handler)**: Generate OID code PNG images

**copy_gme(album_oid, tiptoi_dir, db_handler)**: Copy GME to TipToi pen

**delete_gme_tiptoi(album_oid, tiptoi_dir)**: Delete GME from pen

**get_sorted_tracks(album)**: Sort tracks by track number

## OID Code Ranges

- **1-999**: Album OIDs (product IDs)
- **1001-14999**: Script codes (play, pause, tracks, etc.)
- Codes cached in database for reuse

## Usage

```python
from ttmp32gme.tttool_handler import make_gme, copy_gme, create_oids

# Create GME
result = make_gme(123, db, config)
if result['success']:
    print(f"GME: {result['gme_file']}")

# Copy to TipToi
tiptoi_dir = get_tiptoi_dir()
if tiptoi_dir:
    copy_gme(123, tiptoi_dir, db)

# Generate OID images
images = create_oids([2001, 2002], 24, db)
```

GME creation takes 1-5 minutes depending on album size and format.
