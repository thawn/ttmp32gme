# Installation

## Windows and macOS

Download pre-built executables from [releases page](https://github.com/thawn/ttmp32gme/releases), extract, and run. Open `http://localhost:10020` in browser.

**Requirements**:
- Chrome or Chromium browser (for PDF generation) - [Download Chrome](https://www.google.com/chrome/)

**Installation steps**:
1. Download the appropriate ZIP file for your platform:
   - `ttmp32gme-windows.zip` for Windows
   - `ttmp32gme-macos.zip` for macOS
2. Extract the ZIP file to a location of your choice
3. Run the executable:
   - Windows: Double-click `ttmp32gme.exe` or run from command prompt
   - macOS: Right-click `ttmp32gme.app` → Open (first time only to bypass Gatekeeper)
4. Open your browser to `http://localhost:10020`

The executable includes all necessary dependencies (tttool, ffmpeg) except Chrome/Chromium which should be installed separately.

## Linux

### Python (Recommended)

```bash
git clone https://github.com/thawn/ttmp32gme.git && cd ttmp32gme
uv pip install -e .  # Recommended; or: pip install -e .
```

Install tttool: See [tttool installation](https://github.com/entropia/tip-toi-reveng#installation)

Optional (OGG support): `sudo apt-get install ffmpeg`

Run: `ttmp32gme` or `python -m ttmp32gme.ttmp32gme`

### Podman

**Pre-built image**:
```bash
podman run -d --rm \
  --publish 8080:8080 \
  --volume ~/.ttmp32gme:/var/lib/ttmp32gme \
  --volume /media/${USER}/tiptoi:/mnt/tiptoi \
  --name ttmp32gme thawn/ttmp32gme:latest
```

**Podman Compose**: Download [docker-compose.yml](https://raw.githubusercontent.com/thawn/ttmp32gme/master/docker-compose.yml), run `podman-compose up -d` (the docker-compose.yml file format is compatible with podman-compose)

## Command Line Options

```bash
ttmp32gme --port 8080                      # Custom port
ttmp32gme --host 0.0.0.0                   # Network access
ttmp32gme --database /path/to/db.sqlite    # Custom database
ttmp32gme --library /path/to/library       # Custom library
ttmp32gme -v                               # Increase verbosity (-v for INFO, -vv for DEBUG)
ttmp32gme --version                        # Show version
```

## Verification

```bash
ttmp32gme --version
curl http://localhost:10020/  # Should return HTML
```
