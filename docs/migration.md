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

### Option 1: Complete Migration (Recommended)

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

### Option 2: Database Only Migration

Migrate only the configuration database to preserve settings and album metadata. You'll need to regenerate GME files.

**On the source computer**:

1. Stop ttmp32gme if running
2. Copy `config.sqlite` from the data directory to a USB drive or network location

**On the destination computer**:

1. Install ttmp32gme
2. Stop ttmp32gme if running
3. Copy `config.sqlite` to the data directory
4. Start ttmp32gme
5. Regenerate GME files by clicking "Create GME" for each album in the Library page

**Note**: Audio files and cover images are stored in the library folder. If you only migrate the database, you'll need to re-upload these files or manually copy the library folder.

### Option 3: Library Only Migration

Migrate the library folder while keeping default settings on the new computer.

**On the source computer**:

1. Stop ttmp32gme if running
2. Copy the entire `library/` folder to a USB drive or network location

**On the destination computer**:

1. Install ttmp32gme
2. Stop ttmp32gme if running
3. Copy the `library/` folder to the data directory
4. Start ttmp32gme
5. Albums will appear in the Library page with their existing GME files

**Note**: Settings, OID assignments, and metadata are stored in the database. If you only migrate the library, you'll need to reconfigure settings in the Config page.

## Cross-Platform Migration

When migrating between different operating systems (e.g., Windows to Linux):

1. Follow **Option 1** steps above
2. After copying, update the library path in Config page if needed:
   - Open Config page in ttmp32gme
   - Update "Library Path" to match the new system's path format
   - Save configuration

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
5. If GME files were not migrated, click "Create GME" to regenerate them

## Troubleshooting

**Albums missing after migration**:
- Verify you copied the `config.sqlite` file
- Refresh the Library page (F5)
- Check that the database file has read/write permissions

**GME files missing**:
- If you only migrated the database, regenerate GME files using "Create GME" button
- Verify the library folder was copied completely

**Path errors**:
- Update library path in Config page to match the new system
- Ensure the library folder exists and is accessible

**Permission errors**:
- Ensure copied files have proper read/write permissions
- On Linux: `chmod -R u+rw ~/.ttmp32gme/`
- On macOS: `chmod -R u+rw ~/Library/Application\ Support/ttmp32gme/`

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
