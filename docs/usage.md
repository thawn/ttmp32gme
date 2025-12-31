# Usage Guide

This comprehensive guide covers all aspects of using ttmp32gme to create and manage your TipToi audio content.

## Web Interface Overview

The ttmp32gme web interface consists of four main pages:

* **Upload**: Add new audio files and cover images
* **Library**: Manage your album collection
* **Print**: Configure and print control sheets
* **Help**: Quick reference and troubleshooting tips
* **Config**: Configure application settings

## Upload Page

### Adding Audio Files

1. Navigate to the Upload page (the home page by default)
2. Click "Choose Files" or drag and drop MP3/OGG files
3. Select one or more audio files from a single album
4. Click "Upload" to begin the upload process

**Important**: Only upload files from one album at a time to maintain organization.

### Adding Cover Images

You can add a cover image along with your audio files:

1. Click "Choose Image" or drag and drop an image file
2. Supported formats: JPEG, PNG
3. The cover will be automatically associated with the album
4. Cover images enhance the printed control sheets

### What Happens During Upload

When you upload audio files:

1. **Metadata Extraction**: ID3 tags are read automatically
   - Album title
   - Artist name
   - Track titles
   - Track numbers
   - Year
   - Embedded cover art

2. **File Processing**: Files are copied to the library
3. **Album Creation**: A new album entry is created in the library
4. **Automatic Organization**: Files are organized by album

## Library Page

The Library page is where you manage all your albums.

### Album Information

Each album displays:

* Cover image (if available)
* Album title
* Artist name
* Number of tracks
* OID (Object Identification) number
* Status (configured, GME created, etc.)

### Editing Album Information

To edit an album:

1. Click the "Edit" button for the album
2. Modify any of the following:
   - Album title
   - Artist name
   - Track titles
   - OID number
   - Player mode (music/audiobook)
3. Click "Save Changes"

**OID Numbers**: Each album needs a unique OID between 1 and 999. This number links the printed control sheet to the GME file.

### Player Modes

ttmp32gme supports two player modes:

**Music Mode**:
* Supports shuffle and repeat
* Includes playback controls
* Best for music albums

**Audiobook Mode** (TipToi mode):
* Sequential playback
* Resume from last position
* No shuffle
* Best for audiobooks and stories

### Creating GME Files

Once your album is configured:

1. Ensure all information is correct
2. Click "Create GME" button
3. Wait for the process to complete (may take several minutes)
4. A success message will appear when complete

The GME creation process:
* Converts audio files to the proper format
* Generates OID codes
* Creates control scripts
* Packages everything into a GME file

### Managing Albums

**Delete an Album**:
1. Select the album using the checkbox
2. Click "Delete Selected"
3. Confirm the deletion

**Copy to TipToi**:
1. Connect your TipToi pen
2. Select albums using checkboxes
3. Click "Copy selected to TipToi"
4. Wait for the copy operation to complete

**Print Control Sheets**:
1. Select albums using checkboxes
2. Click "Print Selected"
3. The Print page will open with your selected albums

### Album Status Indicators

Albums can have different statuses:

* **New**: Recently uploaded, needs configuration
* **Configured**: Information entered, ready to create GME
* **GME Created**: GME file exists, ready to use
* **Error**: Problem during GME creation (check logs)

## Print Page

The Print page allows you to create printable control sheets with OID codes.

### Print Presets

ttmp32gme offers three print layout presets:

#### List Layout
* Detailed album information
* Full track listing
* Control buttons
* Cover image
* Best for: Few albums, maximum information

#### Tiles Layout
* Compact grid layout
* Minimal text
* Multiple albums per page
* Best for: Many albums, space efficiency

#### CD Booklet Layout
* Optimized for CD case inserts
* Standard CD booklet dimensions
* Professional appearance
* Best for: Physical CD cases

### Customizing Print Layout

Click the gear icon (⚙) to open print configuration:

**Display Options**:
* Show/hide cover images
* Show/hide album information
* Show/hide control buttons
* Show/hide track list

**Layout Options**:
* Number of columns (1-4)
* Album size (small, medium, large)
* Page margins

**OID Code Settings**:
* Print resolution (DPI): 600, 1200, or 2400
* Pixels per dot: 2, 3, or 4

See [Print Configuration](print-configuration.md) for detailed information.

### Printing Process

1. **Configure Layout**: Choose preset or customize settings
2. **Preview**: Review the layout on screen
3. **Print Settings**: Open browser print dialog (Ctrl+P or Cmd+P)
4. **Print Options**:
   - Scale: 100% (no auto-scaling!)
   - Quality: Highest available
   - Color: Depends on printer (try both)
5. **Print**: Click Print

**Alternative - Create PDF**:
* Click "Save as PDF" button
* Save the PDF file
* Print from a PDF viewer with full control over settings

### Print Quality Checklist

Before printing:

- [ ] Scale set to 100%
- [ ] No auto-scaling or fit-to-page
- [ ] Highest quality/resolution selected
- [ ] Paper size matches layout
- [ ] Test print completed successfully

## Config Page

Configure application settings:

**Server Settings**:
* Host address
* Port number
* Auto-open browser

**Audio Settings**:
* Audio format (MP3/OGG)
* Pen language

**Library Settings**:
* Library path location
* Database location

**Note**: Changing server settings requires restarting ttmp32gme.

## Keyboard Shortcuts

* `Ctrl/Cmd + P`: Open print dialog (on Print page)
* `Ctrl/Cmd + S`: Save (when editing)
* `Esc`: Close modals/dialogs

## Tips and Best Practices

### Organizing Your Library

* Use consistent naming conventions for albums and artists
* Include cover images for easier identification
* Keep track of OID numbers used
* Delete test albums to keep library clean

### Optimal Audio Settings

* **MP3**: 128-192 kbps is sufficient for TipToi
* **OGG**: Slightly smaller files, requires ffmpeg
* Higher bitrates don't improve TipToi audio quality
* Lower bitrates reduce file size and copy time

### Working with Multiple Albums

* Process albums one at a time
* Create GME files in batches during idle time
* Print multiple albums together to save paper
* Group related albums (e.g., series) with sequential OIDs

### Backup and Migration

Your library is stored in:
* **Linux/Mac**: `~/.ttmp32gme/`
* **Windows**: `%USERPROFILE%\.ttmp32gme\`

To backup:
1. Copy the entire `.ttmp32gme` directory
2. Includes both database and audio files

To migrate to another computer:
1. Install ttmp32gme on the new system
2. Stop ttmp32gme if running
3. Copy the `.ttmp32gme` directory
4. Start ttmp32gme

### TipToi Pen Management

* Always safely disconnect the pen after copying
* Don't remove pen during file transfer
* Regularly update pen firmware
* Keep pen charged for best OID recognition

## Advanced Usage

### Command Line Operations

Run ttmp32gme with custom settings:

```bash
# Custom port and host
ttmp32gme --host 0.0.0.0 --port 8080

# Custom library location
ttmp32gme --library /path/to/library

# Debug mode
ttmp32gme --debug
```

### Multiple Instances

Run multiple instances with different libraries:

```bash
# Instance 1 (music)
ttmp32gme --port 10020 --library ~/ttmp32gme-music

# Instance 2 (audiobooks)
ttmp32gme --port 10021 --library ~/ttmp32gme-audiobooks
```

### API Access

ttmp32gme exposes a REST API for automation. See the [API Reference](api/index.md) for details.

## Troubleshooting

For common issues and solutions, see the [Troubleshooting Guide](troubleshooting.md).

## Next Steps

* Learn about [print configuration](print-configuration.md) in detail
* Read the [troubleshooting guide](troubleshooting.md)
* Explore the [development guide](development.md) to contribute
