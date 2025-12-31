# print_handler Module

Print layout generation module for ttmp32gme.

```{eval-rst}
.. automodule:: ttmp32gme.print_handler
   :members:
   :undoc-members:
   :show-inheritance:
```

## Module Overview

The `print_handler` module generates printable layouts with OID codes for TipToi control sheets. It handles:

* HTML layout generation for printing
* OID code image creation and embedding
* Track list formatting with playback buttons
* Control button generation
* PDF creation (platform-specific)

## Key Functions

### create_print_layout(album_ids, layout_config, db_handler)

Generate HTML print layout for selected albums.

Creates the complete HTML page with embedded OID codes for printing.

**Parameters**:
* `album_ids` (List[int]): List of album OIDs to include
* `layout_config` (dict): Layout configuration (preset, columns, size, etc.)
* `db_handler` (DBHandler): Database handler instance

**Returns**: HTML string ready for printing

**Layout Configuration**:
```python
{
    "preset": "list",  # or "tiles", "cd-booklet"
    "columns": 2,
    "show_cover": True,
    "show_info": True,
    "show_controls": True,
    "show_tracks": True,
    "album_size": "medium",  # or "small", "large"
    "dpi": 1200,
    "pixels_per_dot": 2
}
```

**Example**:
```python
layout = create_print_layout(
    album_ids=[123, 456],
    layout_config={
        "preset": "list",
        "columns": 2,
        "show_cover": True,
        "dpi": 1200
    },
    db_handler=db
)
```

### format_tracks(album, oid_map, db_handler)

Format track list with OID codes for printing.

Creates HTML for the track list with embedded OID code images for each track.

**Parameters**:
* `album` (dict): Album dictionary with track information
* `oid_map` (dict): Mapping of script names to OID codes
* `db_handler` (DBHandler): Database handler instance

**Returns**: HTML string with formatted track list

**OID Map Structure**:
```python
{
    "t0": {"code": 2001},
    "t1": {"code": 2002},
    "t2": {"code": 2003},
    # ...
}
```

**Example**:
```python
album = db.get_album(123)
oid_map = get_oid_mappings(album)
tracks_html = format_tracks(album, oid_map, db)
```

### format_print_button(label, oid_code, size, db_handler)

Create HTML for a printable control button with OID code.

Generates a button with label and embedded OID code image.

**Parameters**:
* `label` (str): Button label text (e.g., "Play", "Pause")
* `oid_code` (int): OID code for this button
* `size` (int): Button size in millimeters
* `db_handler` (DBHandler): Database handler instance

**Returns**: HTML string for button

**Button Types**:
* Play/Pause/Stop
* Next/Previous track
* Shuffle/Repeat
* Volume controls
* Power on/off

**Example**:
```python
play_button = format_print_button(
    label="▶ Play",
    oid_code=2001,
    size=24,
    db_handler=db
)
```

### create_pdf(html_content, output_path, config)

Create PDF from HTML content (platform-specific).

Generates a PDF file from the print layout HTML. Implementation varies by platform.

**Parameters**:
* `html_content` (str): HTML content to convert
* `output_path` (Path): Output PDF file path
* `config` (dict): Configuration with print settings

**Returns**: Path to created PDF file

**Platform Support**:
* **Windows**: Uses built-in PDF generation
* **macOS**: Uses WebKit for PDF generation
* **Linux**: Requires wkhtmltopdf or similar tool

**Example**:
```python
pdf_path = create_pdf(
    html_content=layout_html,
    output_path=Path("/tmp/album.pdf"),
    config=config
)
```

## Layout Presets

### List Preset

Detailed layout with full information:

**Features**:
* Large album covers
* Complete album information
* Full track listing
* All control buttons
* 1-2 albums per page

**Best for**:
* Small collections
* Reference sheets
* Maximum information density

### Tiles Preset

Compact grid layout:

**Features**:
* Small album covers
* Minimal text (title only)
* Essential controls only
* 6-12 albums per page

**Best for**:
* Large collections
* Quick selection sheets
* Space efficiency

### CD Booklet Preset

Optimized for CD case inserts:

**Features**:
* Standard CD dimensions (12cm × 12cm)
* Album art prominent
* Track listing
* Folds to fit jewel cases

**Best for**:
* Physical CD collections
* Professional presentation
* Archive purposes

## OID Code Integration

### Code Placement

OID codes are embedded at specific locations:

1. **Album activation**: Top-left or center
2. **Control buttons**: Arranged in grid
3. **Track buttons**: Next to each track
4. **Navigation**: Bottom or side

### Image Generation

OID images are generated dynamically:

1. Request OID code from tttool_handler
2. Cache image for reuse
3. Embed in HTML at correct size
4. Scale for print resolution

### Resolution Handling

**DPI Settings**:
* 600 DPI: Minimum, may work
* 1200 DPI: Recommended
* 2400 DPI: High quality, if supported

**Pixels Per Dot**:
* 2 pixels: Standard (Nyquist theorem)
* 3 pixels: Better recognition
* 4 pixels: Maximum reliability

## HTML Generation

### Template Structure

```html
<div class="album">
  <div class="album-header">
    <img src="cover.jpg" class="cover-image">
    <div class="album-info">
      <h2>Album Title</h2>
      <p>Artist Name</p>
    </div>
  </div>
  
  <div class="album-controls">
    <!-- Control buttons with OID codes -->
  </div>
  
  <div class="track-list">
    <!-- Track items with OID codes -->
  </div>
</div>
```

### CSS Styling

Print-specific styles:

```css
@media print {
  .album {
    page-break-inside: avoid;
  }
  
  .oid-image {
    image-rendering: pixelated;
    image-rendering: crisp-edges;
  }
}
```

### Responsive Layout

Layouts adapt to:
* Different column counts
* Various album sizes
* Different paper sizes
* Orientation (portrait/landscape)

## PDF Generation

### Windows

Uses COM interface to Internet Explorer/Edge:

```python
def create_pdf_windows(html, output):
    # Use IE/Edge COM interface
    # Convert HTML to PDF
    pass
```

### macOS

Uses WebKit framework:

```python
def create_pdf_macos(html, output):
    # Use WebKit WKWebView
    # Render and save as PDF
    pass
```

### Linux

Requires external tool:

```python
def create_pdf_linux(html, output):
    # Use wkhtmltopdf or similar
    subprocess.run(['wkhtmltopdf', html, output])
```

## Usage Examples

### Generate Print Layout

```python
from ttmp32gme.print_handler import create_print_layout

# Configuration
config = {
    "preset": "list",
    "columns": 2,
    "show_cover": True,
    "show_info": True,
    "show_controls": True,
    "show_tracks": True,
    "dpi": 1200,
    "pixels_per_dot": 2
}

# Generate layout
html = create_print_layout(
    album_ids=[123, 456, 789],
    layout_config=config,
    db_handler=db
)

# Save or serve HTML
with open('print.html', 'w') as f:
    f.write(html)
```

### Custom Control Buttons

```python
from ttmp32gme.print_handler import format_print_button

# Create custom buttons
buttons = []

# Play button
buttons.append(format_print_button("▶ Play", 2001, 24, db))

# Pause button  
buttons.append(format_print_button("⏸ Pause", 2002, 24, db))

# Stop button
buttons.append(format_print_button("⏹ Stop", 2003, 24, db))

# Combine into HTML
controls_html = '<div class="controls">' + ''.join(buttons) + '</div>'
```

### Generate PDF

```python
from ttmp32gme.print_handler import create_pdf
from pathlib import Path

# Create layout
html = create_print_layout([123], config, db)

# Generate PDF
pdf_path = create_pdf(
    html_content=html,
    output_path=Path("/tmp/album_123.pdf"),
    config=config
)

print(f"PDF created: {pdf_path}")
```

## Print Quality Optimization

### Image Settings

```python
oid_settings = {
    "dpi": 1200,
    "pixels_per_dot": 2,
    "image_format": "PNG",
    "compression": None  # No compression for OID codes
}
```

### CSS Optimization

```css
.oid-image {
  /* Prevent interpolation */
  image-rendering: -moz-crisp-edges;
  image-rendering: -webkit-optimize-contrast;
  image-rendering: pixelated;
  
  /* Exact sizing */
  width: 24mm;
  height: 24mm;
}
```

### Browser Print Settings

Recommended:
* Scale: 100% (no auto-scaling)
* Margins: Minimal
* Background graphics: Enabled
* Headers/footers: Disabled

## Performance Considerations

### Caching

* OID images cached to disk
* Reused across prints
* Cleared when codes change

### Large Layouts

* Generate in chunks if many albums
* Use progressive loading
* Optimize image sizes

### Memory Usage

* Stream HTML output if possible
* Clear caches periodically
* Monitor image generation

## See Also

* [tttool_handler](tttool_handler.md) - OID code generation
* [Print Configuration Guide](../print-configuration.md) - User guide
* [Usage Guide](../usage.md) - Printing workflows
