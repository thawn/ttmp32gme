# Troubleshooting

This guide helps you resolve common issues when using ttmp32gme.

## Installation Issues

### Python Version Errors

**Problem**: Error about Python version when installing

**Solution**:
```bash
# Check your Python version
python --version

# Must be 3.11 or higher
# If you have multiple versions, use specific version:
python3.11 -m pip install -e .
```

### tttool Not Found

**Problem**: Error: "tttool command not found"

**Solutions**:

1. **Verify tttool is installed**:
   ```bash
   which tttool
   ```

2. **Install tttool**:
   - Ubuntu/Debian: See [installation guide](installation.md#installing-tttool)
   - macOS: `brew install tttool`
   - Windows: Download from [tttool releases](https://github.com/entropia/tip-toi-reveng/releases)

3. **Check PATH**:
   ```bash
   echo $PATH
   ```
   Ensure tttool installation directory is in PATH

4. **Manual path specification** (temporary workaround):
   Set environment variable:
   ```bash
   export TTTOOL_PATH=/path/to/tttool
   ```

### Port Already in Use

**Problem**: Error: "Address already in use" or "Port 10020 is already in use"

**Solutions**:

1. **Use a different port**:
   ```bash
   ttmp32gme --port 8080
   ```

2. **Find process using the port**:
   ```bash
   # Linux/Mac
   lsof -i :10020
   
   # Windows
   netstat -ano | findstr :10020
   ```

3. **Kill the process** (if it's an old ttmp32gme instance):
   ```bash
   # Linux/Mac (replace PID with actual process ID)
   kill -9 PID
   
   # Windows
   taskkill /PID PID /F
   ```

### Permission Denied Errors

**Problem**: Permission errors when installing or running

**Solutions**:

1. **Use user installation**:
   ```bash
   pip install --user -e .
   ```

2. **Use virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -e .
   ```

3. **Check file permissions**:
   ```bash
   # For library directory
   chmod -R u+w ~/.ttmp32gme
   ```

### Dependencies Installation Fails

**Problem**: Error installing Python dependencies

**Solutions**:

1. **Update pip**:
   ```bash
   pip install --upgrade pip
   ```

2. **Install build tools**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-dev build-essential
   
   # macOS (install Xcode Command Line Tools)
   xcode-select --install
   ```

3. **Try uv instead of pip**:
   ```bash
   pip install uv
   uv pip install -e .
   ```

## Upload Issues

### Files Won't Upload

**Problem**: Files don't upload or upload fails

**Solutions**:

1. **Check file size**: Maximum 500 MB total per upload
2. **Check file format**: MP3 and OGG supported (WAV, FLAC not supported)
3. **Check browser**: Try different browser
4. **Check network**: Ensure stable connection
5. **Check disk space**: Ensure enough space in library directory

### Upload Stalls or Freezes

**Problem**: Upload starts but never completes

**Solutions**:

1. **Check server logs**: Look for error messages
2. **Refresh page** and try again
3. **Upload fewer files** at once
4. **Check file corruption**: Try different files
5. **Restart ttmp32gme**: Stop and start the server

### Metadata Not Extracted

**Problem**: Album/track information is empty after upload

**Solutions**:

1. **Check ID3 tags**: Use tool like Mp3tag to verify tags exist
2. **Update mutagen**: `pip install --upgrade mutagen`
3. **Manual entry**: Edit information on Library page
4. **Re-tag files**: Use proper ID3 editor before uploading

### Cover Images Not Showing

**Problem**: Uploaded cover images don't appear

**Solutions**:

1. **Check image format**: JPEG and PNG supported
2. **Check image size**: Very large images may not load
3. **Resize image**: Try images under 2 MB
4. **Check file corruption**: Open image in image viewer first
5. **Re-upload**: Delete album and upload again

## Library Issues

### Album Not Appearing

**Problem**: Uploaded album doesn't show in library

**Solutions**:

1. **Refresh page**: Press F5 or reload
2. **Check upload completion**: Verify upload finished successfully
3. **Check database**: Ensure database file is writable
4. **Check logs**: Look for error messages in console

### Cannot Edit Album

**Problem**: Edit button doesn't work or changes don't save

**Solutions**:

1. **Check JavaScript errors**: Open browser console (F12)
2. **Clear browser cache**: Ctrl+Shift+Del
3. **Try different browser**: Test in another browser
4. **Check for special characters**: Avoid problematic characters in titles
5. **Manual database edit** (advanced): Use SQLite browser

### GME Creation Fails

**Problem**: "Create GME" fails with error

**Solutions**:

1. **Check tttool**: Verify `tttool --version` works
2. **Check audio files**: Ensure files are valid MP3/OGG
3. **Check disk space**: Ensure enough space for conversion
4. **Check OID number**: Must be unique (1-999)
5. **Check permissions**: Ensure library directory is writable
6. **View detailed error**: Check browser console and server logs

### OID Already in Use

**Problem**: Error: "OID number already in use"

**Solutions**:

1. **Choose different OID**: Use number not in use
2. **Delete old album**: If old album using OID is no longer needed
3. **Track OID usage**: Keep list of used OIDs
4. **Check for hidden albums**: May be albums not visible in UI

### Cannot Delete Album

**Problem**: Delete operation fails

**Solutions**:

1. **Check file permissions**: Ensure library directory is writable
2. **Close other programs**: Ensure no other program has files open
3. **Disconnect TipToi**: If pen has files open
4. **Restart server**: Stop and restart ttmp32gme
5. **Manual deletion** (last resort): Delete from library folder directly

## Print Issues

### OID Codes Not Recognized by Pen

See the detailed [Print Configuration Guide](print-configuration.md) for comprehensive troubleshooting.

**Quick checklist**:

- [ ] Printed at 100% scale (no auto-scaling)
- [ ] Used 1200 DPI or higher
- [ ] High quality print settings
- [ ] GME file copied to TipToi pen
- [ ] Pen firmware up to date
- [ ] Test OID table prints correctly

**Test with OID table**:

1. Download [test OID table](https://github.com/thawn/ttmp32gme/blob/master/src/assets/images/oid-table.png)
2. Print at same settings as control sheets
3. Point pen at patterns
4. Pen should respond with German message
5. If pen doesn't respond, it's a printer issue

### Print Quality Poor

**Problem**: Prints are blurry, faded, or incomplete

**Solutions**:

1. **Check printer status**:
   - Clean print heads
   - Replace low ink/toner
   - Run printer maintenance
   - Check for paper jams

2. **Adjust print settings**:
   - Use highest quality mode
   - Disable economy/draft mode
   - Enable graphics mode
   - Increase contrast

3. **Try different paper**:
   - Use smooth, white paper
   - Avoid recycled or textured paper
   - Try photo paper
   - Use heavier weight (80+ gsm)

4. **Adjust ttmp32gme settings**:
   - Increase pixels per dot (3 or 4)
   - Try higher resolution (2400 DPI)
   - Regenerate GME after changes

### Layout Problems

**Problem**: Print layout is cut off or incorrect

**Solutions**:

1. **Check margins**: Reduce margins in print dialog
2. **Check page size**: Ensure matches printer paper size
3. **Check scale**: Must be exactly 100%
4. **Try different preset**: List, Tiles, or CD Booklet
5. **Adjust custom settings**: Reduce columns or size

### PDF Creation Issues

**Problem**: "Save as PDF" doesn't work

**Solutions**:

1. **Check browser support**: Try different browser
2. **Use browser print-to-PDF**: As alternative
3. **Check disk space**: Ensure enough space to save
4. **Try different location**: Save to different folder
5. **Update browser**: Ensure latest version

## TipToi Pen Issues

### Pen Not Detected

**Problem**: "Copy to TipToi" button doesn't appear

**Solutions**:

1. **Check USB connection**: Try different cable/port
2. **Mount the pen**: Ensure pen appears as drive
3. **Reload library page**: Press F5
4. **Check mount point**: May need custom path
5. **Manual copy**: Copy GME files manually to pen

**Manual copy process**:
```bash
# Find pen mount point
df -h | grep -i tiptoi

# Copy GME file
cp ~/.ttmp32gme/library/album_name/*.gme /media/tiptoi/
```

### Copy to Pen Fails

**Problem**: Error when copying GME to pen

**Solutions**:

1. **Check pen storage**: Ensure enough space on pen
2. **Check USB connection**: Ensure stable connection
3. **Close other programs**: No other programs accessing pen
4. **Safely eject and reconnect**: Restart the pen
5. **Manual copy**: Copy files using file manager

### Pen Doesn't Play Audio

**Problem**: GME files on pen but no audio

**Solutions**:

1. **Verify file copy**: Check GME file is on pen
2. **Check file size**: Should not be 0 bytes
3. **Check OID match**: Print sheet OID must match GME file
4. **Regenerate GME**: Create GME again
5. **Check pen firmware**: Update if necessary
6. **Test with different album**: Verify pen works at all

### Pen Says "Install Audio File"

**Problem**: Pen recognizes code but says audio file not installed

**Meaning**: OID codes are working! But GME file missing or wrong.

**Solutions**:

1. **Copy GME to pen**: GME file not on pen yet
2. **Check filename**: Must match format (e.g., `OID_0123.gme`)
3. **Check OID number**: Must match between print and GME
4. **Reconnect pen**: Pen may need restart to see new files

## Browser Issues

### Interface Not Loading

**Problem**: Web interface doesn't load at http://localhost:10020

**Solutions**:

1. **Check server is running**: Verify ttmp32gme process
2. **Check port**: Try http://127.0.0.1:10020
3. **Try different browser**: Test Chrome, Firefox, Edge
4. **Check firewall**: May be blocking connection
5. **Check server logs**: Look for startup errors

### JavaScript Errors

**Problem**: Features not working, console shows errors

**Solutions**:

1. **Clear cache**: Ctrl+Shift+Del
2. **Disable extensions**: Try incognito/private mode
3. **Update browser**: Ensure latest version
4. **Try different browser**: Test functionality

### Slow Performance

**Problem**: Interface is slow or unresponsive

**Solutions**:

1. **Check CPU usage**: Server may be busy
2. **Reduce library size**: Archive old albums
3. **Close other tabs**: Free up browser memory
4. **Restart browser**: Clear memory
5. **Restart server**: Fresh start

## Server/Backend Issues

### Server Crashes

**Problem**: ttmp32gme stops running

**Solutions**:

1. **Check logs**: Look for error messages
2. **Check resources**: Disk space, memory
3. **Run in debug mode**: `ttmp32gme --debug`
4. **Update dependencies**: `pip install --upgrade -e .`
5. **Report bug**: With logs and reproduction steps

### Database Corruption

**Problem**: Database errors or corrupt data

**Solutions**:

1. **Backup first**: Copy `~/.ttmp32gme/`
2. **Try database repair**:
   ```bash
   sqlite3 ~/.ttmp32gme/config.sqlite "PRAGMA integrity_check;"
   ```
3. **Restore from backup**: If you have one
4. **Fresh start**: Delete database (loses configuration)
   ```bash
   mv ~/.ttmp32gme/config.sqlite ~/.ttmp32gme/config.sqlite.backup
   ```

### Library Path Issues

**Problem**: Can't find library or files

**Solutions**:

1. **Check library path**: In Config page
2. **Verify path exists**: Use file manager
3. **Check permissions**: Must be readable/writable
4. **Use absolute paths**: Avoid relative paths
5. **Specify custom path**: `ttmp32gme --library /path/to/library`

## Performance Issues

### Large Library Slow

**Problem**: Many albums causing slowness

**Solutions**:

1. **Archive old albums**: Move to separate location
2. **Delete unused albums**: Clean up test albums
3. **Optimize database**:
   ```bash
   sqlite3 ~/.ttmp32gme/config.sqlite "VACUUM;"
   ```
4. **Use pagination**: Future feature

### GME Creation Slow

**Problem**: Creating GME files takes very long

**Expected behavior**: GME creation can take 1-5 minutes per album depending on:
- Number of tracks
- File sizes
- Audio format conversion needed
- CPU speed

**To improve**:
1. Use MP3 files (OGG requires conversion)
2. Use lower bitrate source files
3. Create GME files in batch overnight
4. Close other applications during creation

## Getting More Help

If you can't resolve your issue:

### 1. Search Existing Issues

Check [GitHub Issues](https://github.com/thawn/ttmp32gme/issues) for:
- Similar problems
- Known bugs
- Workarounds

### 2. Check External Resources

- [tttool manual](https://tttool.readthedocs.io/)
- [tttool printing wiki](https://github.com/entropia/tip-toi-reveng/wiki/Printing)
- [tttool issues](https://github.com/entropia/tip-toi-reveng/issues)

### 3. Report a Bug

When reporting issues, include:

**System Information**:
- OS and version
- Python version
- ttmp32gme version
- Browser and version

**Problem Details**:
- What you were trying to do
- What happened
- What you expected
- Error messages (complete text)
- Screenshots if relevant

**For Print Issues**:
- Printer model
- Print settings used
- Whether test OID table works
- What pen says (if anything)

**Logs**:
```bash
# Run with debug logging
ttmp32gme --debug 2>&1 | tee ttmp32gme.log
```

Include relevant parts of log file.

### 4. Ask for Help

Create a new issue at:
https://github.com/thawn/ttmp32gme/issues/new

Be specific and include all information listed above.

## Preventive Measures

Avoid issues by:

- Keep backups of `~/.ttmp32gme/`
- Update ttmp32gme regularly
- Update tttool regularly
- Update printer drivers
- Test new albums before batch processing
- Document your print settings that work
- Keep TipToi firmware updated

## Next Steps

- Review [Usage Guide](usage.md) for proper usage
- Check [Print Configuration](print-configuration.md) for print help
- Read [Development Guide](development.md) to contribute fixes
