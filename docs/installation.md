# Installation

## Windows and macOS

Download pre-built executables from [releases page](https://github.com/thawn/ttmp32gme/releases), extract, and run. Open `http://localhost:10020` in browser.

## Linux

### Python (Recommended)

```bash
git clone https://github.com/thawn/ttmp32gme.git && cd ttmp32gme
uv pip install -e .  # or: pip install -e .
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
ttmp32gme --debug                          # Debug mode
```

## Verification

```bash
ttmp32gme --version
curl http://localhost:10020/  # Should return HTML
```
