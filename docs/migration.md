# Data Migration

This guide explains how to migrate your ttmp32gme data between computers.

## Data Locations

### Default Locations

**Linux**: `~/.ttmp32gme/`

**macOS**: `~/Library/Application Support/ttmp32gme/`

**Windows**: `%APPDATA%\ttmp32gme\`

### Custom Locations

If you started ttmp32gme with `--database` or `--library` flags, your data is in those custom locations.

## Migration Steps

### Same-Platform Migration (Recommended)

Use this method when migrating between computers running the same OS (or between Linux and macOS).

**Steps**:
1. Stop ttmp32gme on source computer
2. Copy entire data directory to USB/network location
3. Install ttmp32gme on destination computer
4. Stop ttmp32gme if auto-started
5. Copy data directory to destination location
6. Start ttmp32gme - all data will be available

### Cross-Platform Migration (Windows ↔ macOS/Linux)

Use this method **only** when migrating between Windows and another OS.

**Note**: For macOS ↔ Linux migrations, use Same-Platform method instead.

**Steps**:
1. Stop ttmp32gme on source computer
2. Copy all album folders from library directory
3. Install ttmp32gme on destination computer
4. Re-upload MP3 files and cover images for each album
5. Configure album settings to match original setup
6. Create GME files

## Custom Paths

If using custom database or library paths with `--database` or `--library` flags, copy files from custom locations and start ttmp32gme with the same flags on the new computer.

## Verification

After migration:
1. Start ttmp32gme
2. Check Library page - all albums should be visible
3. Check Config page - settings should match
4. Test printing a control sheet

## Migrating from Perl Version

**⚠️ WARNING**: The automatic database upgrade may cause problems. **It is highly recommended to make a backup before upgrading.**

If you're migrating from the older Perl version of ttmp32gme (pre-v2.0), the Python version will automatically fix encoding issues when you first open the database.

**What happens automatically**:
- When you start ttmp32gme v2.0.1 or later with an old database, it detects the version
- Database is automatically upgraded to v2.0.1
- Text encoding is fixed for all album titles, artist names, and track information
- Non-UTF-8 characters (like German umlauts: ä, ö, ü) are converted to proper UTF-8

**Example**: If your Perl database had an album titled "Albert E erklärt den menschlichen Körper" that appeared as "Albert E erkl�rt den menschlichen K�rper" due to encoding issues, it will be automatically corrected.

**Recommendation**: Create a backup before upgrading to avoid data loss in case of issues.

## Troubleshooting

**Albums missing**: Verify you copied entire data directory, refresh page (F5), check file permissions

**Permission errors**: Ensure proper read/write permissions
- Linux: `chmod -R u+rw ~/.ttmp32gme/`
- macOS: `chmod -R u+rw ~/Library/Application\ Support/ttmp32gme/`

**Text encoding errors**: Should be automatically fixed when upgrading from Perl version. Check you're running v2.0.1 or later.

## Backup Recommendations

Create regular backups to prevent data loss:
- Before updates
- After creating new albums
- Use scheduled/automated backups

**Example commands**:

Linux:
```bash
tar -czf ttmp32gme-backup-$(date +%Y%m%d).tar.gz ~/.ttmp32gme/
```

macOS:
```bash
tar -czf ttmp32gme-backup-$(date +%Y%m%d).tar.gz ~/Library/Application\ Support/ttmp32gme/
```

Windows (PowerShell):
```powershell
Compress-Archive -Path $env:APPDATA\ttmp32gme -DestinationPath "ttmp32gme-backup-$(Get-Date -Format 'yyyyMMdd').zip"
```

## See Also

- [Installation](installation.md) - Installing ttmp32gme on a new system
- [Usage Guide](usage.md) - Using ttmp32gme after migration
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
