# Building Executables

This guide explains how to build standalone executables for Windows and macOS.

## Prerequisites

- Python 3.11 or later
- PyInstaller 6.0 or later
- Git

## Setup

```bash
# Clone the repository
git clone https://github.com/thawn/ttmp32gme.git
cd ttmp32gme

# Install build dependencies
pip install -e ".[build]"
```

## Building for Windows

On a Windows machine:

```bash
# Build the executable
pyinstaller ttmp32gme-windows.spec --clean

# The executable will be in dist/ttmp32gme/
# Create a ZIP for distribution
cd dist
Compress-Archive -Path ttmp32gme -DestinationPath ttmp32gme-windows.zip
```

The resulting `ttmp32gme-windows.zip` contains:
- `ttmp32gme.exe` - Main executable
- `lib/win/tttool.exe` - TipToi tool binary
- `lib/win/ffmpeg.exe` - FFmpeg for audio conversion
- All Python dependencies and application files

## Building for macOS

On a macOS machine:

```bash
# Build the executable
pyinstaller ttmp32gme-macos.spec --clean

# The app bundle will be in dist/ttmp32gme.app/
# Create a ZIP for distribution
cd dist
zip -r ttmp32gme-macos.zip ttmp32gme.app
```

The resulting `ttmp32gme-macos.zip` contains:
- `ttmp32gme.app` - macOS application bundle
- `lib/mac/tttool` - TipToi tool binary
- `lib/mac/ffmpeg` - FFmpeg for audio conversion
- Required dynamic libraries (.dylib files)
- All Python dependencies and application files

## CI/CD Build Process

The build process is automated via GitHub Actions:

1. **Trigger**: Builds are triggered automatically when a new release is published
2. **Parallel builds**: Windows and macOS builds run in parallel on their respective platforms
3. **Artifacts**: Built executables are automatically uploaded as release assets

To trigger a manual build:

```bash
# Create and push a git tag
git tag v2.0.0
git push origin v2.0.0

# Create a release on GitHub
gh release create v2.0.0 --title "Release v2.0.0" --notes "Release notes here"
```

The CI workflow will automatically build and upload executables to the release.

## Testing Built Executables

### Windows

```batch
# Extract and run
ttmp32gme.exe --help
ttmp32gme.exe --port 10020
```

### macOS

```bash
# Extract and run
./ttmp32gme.app/Contents/MacOS/ttmp32gme --help
./ttmp32gme.app/Contents/MacOS/ttmp32gme --port 10020
```

Or double-click the app bundle in Finder.

## Troubleshooting

### "Module not found" errors

The spec files include a `hiddenimports` list. If you add new dependencies, add them to this list.

### Missing data files

Data files (templates, assets, config) are specified in the `datas` list in the spec files. Add new data files there.

### Bundled binaries not found

The `get_executable_path()` function in `src/ttmp32gme/build/file_handler.py` checks for bundled binaries first. Ensure the lib/ directory structure is correct in the spec file.

### macOS Gatekeeper issues

Users may need to right-click → Open the app the first time to bypass Gatekeeper. For distribution, you can:
- Sign the app with an Apple Developer certificate
- Notarize the app with Apple

## File Structure

```
dist/
├── ttmp32gme/  (or ttmp32gme.app on macOS)
    ├── ttmp32gme (or .exe on Windows)
    ├── lib/
    │   ├── mac/ or win/
    │   │   ├── tttool
    │   │   ├── ffmpeg
    │   │   └── *.dylib (macOS only)
    ├── templates/
    ├── assets/
    ├── _internal/  (PyInstaller runtime files)
    └── ...
```

## Notes

- **Chrome/Chromium**: Not bundled. Users must install Chrome or Chromium separately for PDF generation.
- **Size**: Windows executable ~50-80 MB, macOS ~60-90 MB (compressed)
- **Python runtime**: Fully embedded, no Python installation required
