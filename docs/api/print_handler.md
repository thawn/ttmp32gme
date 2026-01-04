# print_handler Module

Print layout generation for ttmp32gme.

## Key Functions

**create_print_layout(album_ids, layout_config, db_handler)**: Generate HTML print layout

**format_tracks(album, oid_map, db_handler)**: Format track list with OID codes

**format_print_button(label, oid_code, size, db_handler)**: Create control button with OID

**create_pdf(html_content, output_path, config)**: Create PDF (platform-specific)

## Layout Presets

- **List**: Full details, 1-2 albums/page
- **Tiles**: Compact grid, 6-12 albums/page  
- **CD Booklet**: Standard CD case dimensions

## Usage

```python
from ttmp32gme.print_handler import create_print_layout

config = {
    "preset": "list",
    "columns": 2,
    "show_cover": True,
    "dpi": 1200,
    "pixels_per_dot": 2
}

html = create_print_layout([123, 456], config, db)
```

```{eval-rst}
.. automodule:: ttmp32gme.print_handler
   :members:
   :undoc-members:
   :show-inheritance:
```
