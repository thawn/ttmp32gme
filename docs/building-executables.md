# Building Executables

This guide explains how to build standalone executables for Windows and macOS.

## CI/CD Build Process (Automated)

The build process is automated via GitHub Actions:

1. **Triggers**: Builds run automatically on:
   - Pull requests changing source code, specs, or dependencies
   - New release publications
   - Manual workflow dispatch
2. **Dependency Download**: tttool v1.8.1 and ffmpeg are downloaded during build
3. **Parallel builds**: Windows and macOS builds run simultaneously
4. **Artifacts**: Built executables uploaded as workflow artifacts (30-day retention) or release assets

**To trigger a manual build**:
```bash
git tag v2.0.0
git push origin v2.0.0
gh release create v2.0.0 --title "Release v2.0.0" --notes "Release notes"
```

## Prerequisites

- Python 3.11 or later
- PyInstaller 6.0 or later
- Git
- Internet connection (to download tttool and ffmpeg)

## Setup

```bash
git clone https://github.com/thawn/ttmp32gme.git && cd ttmp32gme
uv pip install -e ".[build]"  # or: pip install -e ".[build]"
```

## Building for Windows

On Windows:

```bash
# Download tttool
$TTTOOL_VERSION = "1.8.1"
New-Item -ItemType Directory -Force -Path lib/win
Invoke-WebRequest -Uri "https://github.com/entropia/tip-toi-reveng/releases/download/${TTTOOL_VERSION}/tttool-${TTTOOL_VERSION}.zip" -OutFile tttool.zip
Expand-Archive -Path tttool.zip -DestinationPath .
Move-Item -Path tttool.exe -Destination lib/win/tttool.exe -Force
Remove-Item tttool.zip

# Download ffmpeg
Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile ffmpeg.zip
Expand-Archive -Path ffmpeg.zip -DestinationPath .
$ffmpegDir = Get-ChildItem -Directory -Filter "ffmpeg-*" | Select-Object -First 1
Move-Item -Path "$($ffmpegDir.FullName)/bin/ffmpeg.exe" -Destination lib/win/ffmpeg.exe -Force
Remove-Item -Recurse -Force $ffmpegDir
Remove-Item ffmpeg.zip

# Build
pyinstaller ttmp32gme-windows.spec --clean
cd dist
Compress-Archive -Path ttmp32gme -DestinationPath ttmp32gme-windows.zip
```

Output: `ttmp32gme-windows.zip` contains `ttmp32gme.exe` with bundled tttool, ffmpeg, and dependencies.

## Building for macOS

On macOS:

```bash
# Download tttool
TTTOOL_VERSION="1.8.1"
mkdir -p lib/mac
wget "https://github.com/entropia/tip-toi-reveng/releases/download/${TTTOOL_VERSION}/tttool-${TTTOOL_VERSION}.zip"
unzip "tttool-${TTTOOL_VERSION}.zip"
chmod +x tttool && mv tttool lib/mac/tttool
rm "tttool-${TTTOOL_VERSION}.zip"

# Download ffmpeg
wget "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip" -O ffmpeg.zip
unzip ffmpeg.zip
chmod +x ffmpeg && mv ffmpeg lib/mac/ffmpeg
rm ffmpeg.zip

# Build
pyinstaller ttmp32gme-macos.spec --clean
cd dist
zip -r ttmp32gme-macos.zip ttmp32gme.app
```

Output: `ttmp32gme-macos.zip` contains `ttmp32gme.app` bundle with tttool, ffmpeg, and dependencies.

## Testing Built Executables

**Windows**:
```batch
ttmp32gme.exe --help
ttmp32gme.exe --port 10020
```

**macOS**:
```bash
./ttmp32gme.app/Contents/MacOS/ttmp32gme --help
./ttmp32gme.app/Contents/MacOS/ttmp32gme --port 10020
```

Or double-click the app bundle in Finder.

## Troubleshooting

**"Module not found" errors**: Add dependencies to `hiddenimports` list in spec files

**Missing data files**: Add files to `datas` list in spec files

**Bundled binaries not found**: Verify `lib/` directory structure in spec files

**macOS Gatekeeper issues**: Users must right-click → Open first time. For distribution, sign and notarize with Apple Developer certificate.

## Notes

- **Chrome/Chromium**: Not bundled - users install separately for PDF generation
- **Size**: Windows ~50-80 MB, macOS ~60-90 MB (compressed)
- **Python runtime**: Fully embedded, no Python installation required
