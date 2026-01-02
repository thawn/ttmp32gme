# Building Executables

This guide explains how to build standalone executables for Windows and macOS.

## Prerequisites

- Python 3.11 or later
- PyInstaller 6.0 or later
- Git
- Internet connection (to download tttool and ffmpeg)

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
# Download dependencies
# tttool
$TTTOOL_VERSION = "1.8.1"
New-Item -ItemType Directory -Force -Path lib/win
Invoke-WebRequest -Uri "https://github.com/entropia/tip-toi-reveng/releases/download/${TTTOOL_VERSION}/tttool-${TTTOOL_VERSION}.zip" -OutFile tttool.zip
Expand-Archive -Path tttool.zip -DestinationPath .
Move-Item -Path tttool.exe -Destination lib/win/tttool.exe -Force
Remove-Item tttool.zip

# ffmpeg
Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile ffmpeg.zip
Expand-Archive -Path ffmpeg.zip -DestinationPath .
$ffmpegDir = Get-ChildItem -Directory -Filter "ffmpeg-*" | Select-Object -First 1
Move-Item -Path "$($ffmpegDir.FullName)/bin/ffmpeg.exe" -Destination lib/win/ffmpeg.exe -Force
Remove-Item -Recurse -Force $ffmpegDir
Remove-Item ffmpeg.zip

# Build the executable
pyinstaller ttmp32gme-windows.spec --clean

# The executable will be in dist/ttmp32gme/
# Create a ZIP for distribution
cd dist
Compress-Archive -Path ttmp32gme -DestinationPath ttmp32gme-windows.zip
```

The resulting `ttmp32gme-windows.zip` contains:
- `ttmp32gme.exe` - Main executable
- `lib/win/tttool.exe` - TipToi tool binary (downloaded during build)
- `lib/win/ffmpeg.exe` - FFmpeg for audio conversion (downloaded during build)
- All Python dependencies and application files

## Building for macOS

On a macOS machine:

```bash
# Download dependencies
# tttool
TTTOOL_VERSION="1.8.1"
mkdir -p lib/mac
wget "https://github.com/entropia/tip-toi-reveng/releases/download/${TTTOOL_VERSION}/tttool-${TTTOOL_VERSION}.zip"
unzip "tttool-${TTTOOL_VERSION}.zip"
chmod +x tttool
mv tttool lib/mac/tttool
rm "tttool-${TTTOOL_VERSION}.zip"

# ffmpeg
wget "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip" -O ffmpeg.zip
unzip ffmpeg.zip
chmod +x ffmpeg
mv ffmpeg lib/mac/ffmpeg
rm ffmpeg.zip

# Build the executable
pyinstaller ttmp32gme-macos.spec --clean

# The app bundle will be in dist/ttmp32gme.app/
# Create a ZIP for distribution
cd dist
zip -r ttmp32gme-macos.zip ttmp32gme.app
```

The resulting `ttmp32gme-macos.zip` contains:
- `ttmp32gme.app` - macOS application bundle
- `lib/mac/tttool` - TipToi tool binary (downloaded during build)
- `lib/mac/ffmpeg` - FFmpeg for audio conversion (downloaded during build)
- All Python dependencies and application files

## CI/CD Build Process

The build process is automated via GitHub Actions:

1. **Triggers**: Builds are triggered automatically:
   - On pull requests that change source code, specs, or dependencies
   - When a new release is published
   - Manually via workflow dispatch
2. **Dependency Download**: tttool and ffmpeg are downloaded dynamically during the build:
   - tttool v1.8.1 from GitHub releases
   - ffmpeg from official sources (Windows: gyan.dev, macOS: evermeet.cx)
3. **Parallel builds**: Windows and macOS builds run in parallel on their respective platforms
4. **Artifacts**: Built executables are automatically uploaded:
   - As workflow artifacts for pull requests (retained for 30 days)
   - As release assets when a release is published

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
