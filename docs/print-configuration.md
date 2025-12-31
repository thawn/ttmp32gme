# Print Configuration

This guide covers everything you need to know about configuring and printing control sheets for your TipToi pen.

## Understanding OID Codes

OID (Optical Identification) codes are the patterns of tiny dots that the TipToi pen reads. These codes:

* Are unique identifiers for objects on printed sheets
* Link to specific audio files and actions
* Must be printed with sufficient quality to be recognized
* Are sensitive to printer resolution and quality

## Print Configuration Options

### Resolution Settings

**Print Resolution (DPI)**

The DPI (dots per inch) setting determines the quality of the printed codes:

* **1200 DPI** (Recommended): Best results with most printers
* **2400 DPI**: For high-end printers, may improve recognition
* **600 DPI**: Minimum recommended, may work with some printers

Higher resolution produces more accurate OID codes but:
* Requires printer support
* Increases print time
* May not be available on all printers

### Pixels Per Dot

This setting controls how many printer dots are used for each OID code dot:

* **2 pixels**: Default, follows Nyquist-Shannon sampling theorem
* **3 pixels**: Try if codes aren't recognized at 2 pixels
* **4 pixels**: Larger codes, use if 2 or 3 don't work

Why this matters:
* Too few pixels: Codes may be too fine for the printer
* Too many pixels: Codes become larger but may work better
* The optimal value depends on your specific printer

### Layout Presets

#### List Layout

**Best for**: Detailed information, few albums

Features:
* Full album information (title, artist, year)
* Complete track listing with titles
* All control buttons
* Large cover images
* Spacious layout

When to use:
* Small album collections
* When you need to see all details
* For reference sheets

#### Tiles Layout

**Best for**: Multiple albums, compact display

Features:
* Grid-based layout
* Minimal text (just title)
* Essential controls only
* Multiple albums per page
* Space-efficient

When to use:
* Large album collections
* Quick selection sheets
* Wall mounting
* Limited paper

#### CD Booklet Layout

**Best for**: Physical CD case inserts

Features:
* Standard CD booklet dimensions (12cm × 12cm)
* Professional appearance
* Fits standard jewel cases
* Album art prominent
* Track listing included

When to use:
* Creating physical CD collections
* Gift sets
* Professional presentations
* Archive purposes

### Custom Layout Options

You can customize any layout by adjusting:

**Display Components**:
* Cover image (show/hide)
* Album information (title, artist, year)
* Control buttons (play, pause, stop, etc.)
* Track list

**Layout Grid**:
* Number of columns: 1-4
* Album size: Small, Medium, Large
* Spacing between albums

**Page Settings**:
* Margins (top, bottom, left, right)
* Page orientation (portrait/landscape)
* Paper size

## Control Buttons Explained

Each control sheet includes buttons that control playback:

### Basic Controls

* **Power On**: Activates the album
* **Play**: Start playback from first track
* **Pause**: Pause playback
* **Stop**: Stop playback and reset

### Navigation Controls

* **Next Track**: Skip to next track
* **Previous Track**: Go back to previous track
* **First Track**: Jump to first track
* **Last Track**: Jump to last track

### Playback Modes

* **Shuffle**: Randomize track order (music mode)
* **Repeat**: Loop album or track (music mode)
* **Sequential**: Play in order (audiobook mode)

### Track Selection

* **Individual Track Buttons**: Jump directly to a specific track
* **Track Numbers**: OID codes for each track

## Print Process Step-by-Step

### 1. Select Albums

On the Library page:
1. Check boxes next to albums to print
2. Click "Print Selected"
3. Print page opens with selected albums

### 2. Choose Layout

Click gear icon (⚙) to configure:
1. Select a preset (List, Tiles, or CD Booklet)
2. Or customize settings manually
3. Preview changes in real-time

### 3. Configure OID Settings

Set resolution and pixel settings:
1. Start with 1200 DPI, 2 pixels per dot
2. Adjust if needed based on results
3. Higher settings if pen doesn't recognize codes

### 4. Browser Print Dialog

Open print dialog (Ctrl+P or Cmd+P):

**Critical Settings**:
* **Scale**: Must be 100% (NO auto-scaling!)
* **Margins**: Minimal or None
* **Quality**: Highest available
* **Color Management**: Disabled or minimal

**Printer-Specific**:
* Resolution: Maximum available (1200+ DPI)
* Quality: Best/High quality
* Paper: Use good quality paper
* Mode: Graphics/Image mode (not Text mode)

### 5. Print or Save PDF

**Option A - Direct Print**:
* Click Print in dialog
* Wait for printing to complete

**Option B - Save as PDF**:
* Click "Save as PDF" button in ttmp32gme
* Save to your computer
* Print PDF with dedicated PDF viewer
* Allows better control over settings

## Printer Compatibility

### Recommended Printers

OID codes work best with:
* Laser printers (generally better than inkjet)
* High-resolution printers (1200 DPI+)
* Printers with good driver support
* Professional/office grade printers

### Known Issues by Platform

**Windows**:
* Chrome/Firefox: May not print at sufficient resolution
* Microsoft Edge: Usually works well
* Opera: Sometimes works
* **Solution**: Use "Save as PDF" and print from Acrobat/Edge

**macOS**:
* Chrome: Works well
* Firefox: Works well
* Safari: Generally works
* **Solution**: Direct printing usually works

**Linux**:
* Firefox: Best results
* Chrome: Usually works
* **Solution**: Test both browsers if issues occur

## Troubleshooting Print Issues

### OID Codes Not Recognized

**Step 1 - Verify Basic Printing**:

Test with the [OID table](https://github.com/thawn/ttmp32gme/blob/master/src/assets/images/oid-table.png):
1. Download and print the test table
2. Point pen at patterns
3. Pen should say "Bitte installieren Sie erst die Audiodatei" or similar

If pen doesn't react to test table:
* Problem is with printer/settings, not software
* Try different printer
* Try different settings

**Step 2 - Check Print Settings**:

Verify:
- [ ] Printed at 100% scale
- [ ] No auto-scaling enabled
- [ ] Using highest quality setting
- [ ] Resolution at 1200 DPI or higher
- [ ] Not using "fit to page"

**Step 3 - Adjust OID Settings**:

In ttmp32gme print config:
1. Increase pixels per dot (try 3, then 4)
2. Try different resolution (2400 DPI if supported)
3. Regenerate GME if you changed settings

**Step 4 - Try Different Paper**:

* Use high-quality, smooth paper
* Avoid recycled or rough paper
* Plain white works best
* Glossy paper sometimes helps

**Step 5 - Adjust Printer Settings**:

* **Mode**: Switch to Graphics/Image mode
* **Color**: Try black-and-white vs. color
* **Contrast**: Slightly increase if available
* **Dithering**: Disable if option exists

### Print Quality Issues

**Codes Too Light**:
* Increase print density/toner darkness
* Use fresh ink/toner cartridge
* Check printer maintenance status

**Codes Blurry**:
* Clean print heads
* Use slower print speed
* Enable high-quality mode
* Check paper alignment

**Codes Cut Off**:
* Reduce margins in print dialog
* Check page size matches layout
* Verify printer paper size setting
* Adjust scale if necessary (but stay close to 100%)

**Inconsistent Recognition**:
* Some codes work, others don't
* Usually indicates borderline print quality
* Try increasing pixels per dot
* Use better quality paper
* Check for printer driver updates

## Advanced Techniques

### Creating Custom Layouts

Edit print configuration to create layouts for specific needs:

**Wall Chart**:
* Tiles layout
* 3-4 columns
* Large size
* Cover images prominent

**Reference Card**:
* List layout
* 2 columns
* Small/medium size
* All information visible

**Quick Access Sheet**:
* Custom layout
* Only control buttons
* No track list
* Maximum albums per page

### Batch Printing

Print multiple albums efficiently:

1. Select all albums to print
2. Configure layout once
3. Print all at once
4. Cut/organize later

### Creating Insert Cards

For CD cases or custom containers:

1. Use CD Booklet preset
2. Adjust size to container
3. Print on cardstock
4. Cut to size
5. Insert in case

### Testing New Printers

When trying a new printer:

1. Start with one test album
2. Use List layout for easy testing
3. Try default settings (1200 DPI, 2 pixels)
4. Test each button area
5. Document what works
6. Adjust settings if needed

## Paper Recommendations

### Paper Type

* **Plain Copy Paper**: 80-100 gsm, works for most
* **Photo Paper**: Glossy can work well
* **Cardstock**: 200+ gsm for durability
* **Label Paper**: Use for stickers

### Paper Quality

Better quality generally helps:
* Smoother surface
* Consistent white
* Good opacity
* Doesn't jam

Avoid:
* Recycled paper (inconsistent surface)
* Very thin paper
* Textured paper
* Off-white or colored

## PDF Creation

### When to Use PDFs

Create PDFs when:
* Direct printing doesn't work
* Need to print elsewhere
* Want to archive layouts
* Sharing with others
* Better print control needed

### PDF Best Practices

1. **Save as PDF** from ttmp32gme (not browser print-to-PDF)
2. Open with dedicated PDF viewer (Acrobat, Foxit, etc.)
3. Print from PDF viewer with full quality
4. Verify PDF settings: no compression, full resolution
5. Archive PDFs with GME files for future reprints

## Summary Checklist

Before printing:

- [ ] Albums selected in library
- [ ] Layout configured (preset or custom)
- [ ] Resolution set (1200 DPI recommended)
- [ ] Pixels per dot set (2 recommended)
- [ ] Browser print dialog opened
- [ ] Scale set to 100%
- [ ] Quality set to highest
- [ ] Test page printed successfully
- [ ] OID codes recognized by pen
- [ ] Ready for final print

## Getting Help

If you continue to have print issues:

1. Read the [Troubleshooting Guide](troubleshooting.md)
2. Check the [tttool printing wiki](https://github.com/entropia/tip-toi-reveng/wiki/Printing)
3. Search [GitHub issues](https://github.com/thawn/ttmp32gme/issues)
4. Report issue with:
   - Printer model
   - Settings used
   - What pen says (if anything)
   - Whether test table works

## Next Steps

* Review [Usage Guide](usage.md) for general usage
* Check [Troubleshooting](troubleshooting.md) for common issues
* Explore [Development Guide](development.md) to contribute
