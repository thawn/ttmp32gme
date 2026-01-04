# Usage Guide

## Web Interface

Access at `http://localhost:10020` after starting ttmp32gme (or `http://localhost:8080` if using Docker/Podman).

**Pages**:
- **Upload** - Add MP3/OGG files and cover images
- **Library** - Manage albums, create GME files
- **Print** - Configure and print control sheets
- **Config** - Application settings

## Workflow

### 1. Upload Files

1. Go to Upload page
2. Add MP3/OGG files (one album at a time)
3. Optionally add cover image (JPEG/PNG)
4. Upload - metadata extracted automatically

### 2. Configure Album

On Library page:
1. Review/edit album info (title, artist, tracks)
2. Choose OID number (1-999, must be unique)
3. Select player mode: Music or Audiobook (TipToi)

### 3. Create GME

1. Click "Create GME" button
2. Wait for conversion (1-5 minutes)
3. GME file created in library

### 4. Print Control Sheets

1. Select albums (checkboxes)
2. Click "Print Selected"
3. Configure layout (gear icon)
4. Print at 100% scale, high quality
5. See [Print Configuration](print-configuration.md) for details

### 5. Copy to TipToi

1. Connect TipToi pen
2. Select albums in library
3. Click "Copy selected to TipToi"
4. Wait for completion

## Player Modes

**Music**: Play all tracks, then stop

**Audiobook (TipToi)**: Play all tracks, repeat from beginning when finished

## Command Line

```bash
ttmp32gme --port 8080              # Custom port
ttmp32gme --host 0.0.0.0           # Network access
ttmp32gme --library /path/to/lib   # Custom library
ttmp32gme -v                       # Increase verbosity (-v for INFO, -vv for DEBUG)
ttmp32gme --version                # Show version
```

## Tips

- Upload one album at a time
- Use unique OID numbers
- Include cover images
- Print at 1200 DPI
- Backup `~/.ttmp32gme/` directory (see [Migration Guide](migration.md))
