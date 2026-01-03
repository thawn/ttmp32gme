# Data Migration

This guide explains how to migrate your ttmp32gme configuration database and library folder from one computer to another.

## What to Migrate

ttmp32gme stores two types of data:

1. **Configuration Database** (`config.sqlite`) - Contains application settings, album metadata, and OID assignments
2. **Library Folder** - Contains audio files, GME files, cover images, and generated content

## Data Locations

### Default Locations

**Linux**:
- Database: `~/.ttmp32gme/config.sqlite`
- Library: `~/.ttmp32gme/library/`

**macOS**:
- Database: `~/Library/Application Support/ttmp32gme/config.sqlite`
- Library: `~/Library/Application Support/ttmp32gme/library/`

**Windows**:
- Database: `%APPDATA%\ttmp32gme\config.sqlite`
- Library: `%APPDATA%\ttmp32gme\library\`

### Custom Locations

If you started ttmp32gme with `--database` or `--library` flags, your data is in those custom locations instead.

## Migration Steps

### Option 1: Same-Platform Migration (Recommended)

Use this method when migrating between computers running the same operating system (Linux to Linux, macOS to macOS, Windows to Windows) or between Linux and macOS.

Migrate both database and library to preserve all data and settings.

**On the source computer**:

1. Stop ttmp32gme if running
2. Locate your data directory:
   - Linux: `~/.ttmp32gme/`
   - macOS: `~/Library/Application Support/ttmp32gme/`
   - Windows: `%APPDATA%\ttmp32gme\`
3. Copy the entire directory to a USB drive or network location

**On the destination computer**:

1. Install ttmp32gme (see [Installation](installation.md))
2. Stop ttmp32gme if it auto-started
3. Locate the data directory (same locations as above)
4. Copy the entire directory from your backup to this location
5. Start ttmp32gme - all albums, settings, and files will be available

### Option 2: Cross-Platform Migration (Windows to macOS/Linux)

Use this method **only** when migrating between Windows and another operating system (macOS or Linux). This process requires re-importing your audio files.

**Note**: For migrations between macOS and Linux, use **Option 1** instead.

**On the source computer (Windows)**:

1. Stop ttmp32gme if running
2. Locate your library folder: `%APPDATA%\ttmp32gme\library\`
3. Copy all album folders from the library to a USB drive or network location
4. Each album folder contains the original MP3 files and cover images

**On the destination computer (macOS/Linux)**:

1. Install ttmp32gme (see [Installation](installation.md))
2. Start ttmp32gme to create the initial configuration
3. For each album from your backup:
   - Navigate to the Upload page
   - Upload the MP3 files from the album folder
   - Upload the cover image (if present: `cover.jpg` or `cover.png`)
   - Configure album settings (title, artist, OID) to match your original setup
   - Click "Create GME" to generate the GME files

## Custom Paths

If using custom database or library paths with `--database` or `--library` flags:

1. Copy the files from your custom locations instead of default locations
2. Start ttmp32gme with the same flags on the new computer:
   ```bash
   ttmp32gme --database /path/to/config.sqlite --library /path/to/library
   ```

## Verification

After migration:

1. Start ttmp32gme
2. Check Library page - all albums should be visible
3. Check Config page - settings should match your old setup
4. Test printing a control sheet to verify OID codes are preserved

## Migrating from Perl Version

If you're migrating from the older Perl version of ttmp32gme (pre-v2.0), the Python version will automatically fix encoding issues when you first open the database.

**What happens automatically**:
- When you start ttmp32gme v2.0.1 or later with an old database, it detects the version
- Database is automatically upgraded to v2.0.1
- Text encoding is fixed for all album titles, artist names, and track information
- Non-UTF-8 characters (like German umlauts: ä, ö, ü) are converted to proper UTF-8

**Example**: If your Perl database had an album titled "Albert E erklärt den menschlichen Körper" that appeared as "Albert E erkl�rt den menschlichen K�rper" due to encoding issues, it will be automatically corrected.

**No action required** - the fix happens transparently when you first load your library.

## Troubleshooting

**Albums missing after migration**:
- Verify you copied the entire data directory including `config.sqlite`
- Refresh the Library page (F5)
- Check that the database file has read/write permissions

**Permission errors**:
- Ensure copied files have proper read/write permissions
- On Linux: `chmod -R u+rw ~/.ttmp32gme/`
- On macOS: `chmod -R u+rw ~/Library/Application\ Support/ttmp32gme/`

**Text encoding errors (garbled characters)**:
- This should be automatically fixed when upgrading from Perl to Python version
- Check that you're running v2.0.1 or later
- If issues persist, check the application logs for details

## Backup Recommendations

Regular backups prevent data loss:

- **Automatic**: Create a scheduled backup of the entire data directory
- **Before updates**: Backup before upgrading ttmp32gme
- **After changes**: Backup after creating new albums or changing settings

Example backup command (Linux):
```bash
# Create timestamped backup
tar -czf ttmp32gme-backup-$(date +%Y%m%d).tar.gz ~/.ttmp32gme/
```

Example backup command (macOS):
```bash
# Create timestamped backup
tar -czf ttmp32gme-backup-$(date +%Y%m%d).tar.gz ~/Library/Application\ Support/ttmp32gme/
```

Example backup command (Windows PowerShell):
```powershell
# Create timestamped backup
Compress-Archive -Path $env:APPDATA\ttmp32gme -DestinationPath "ttmp32gme-backup-$(Get-Date -Format 'yyyyMMdd').zip"
```

## See Also

- [Installation](installation.md) - Installing ttmp32gme on a new system
- [Usage Guide](usage.md) - Using ttmp32gme after migration
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
