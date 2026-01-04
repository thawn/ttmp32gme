# ttmp32gme Docker/Podman Container

A containerized version of ttmp32gme that converts MP3/audio files into TipToi GME files.

## Features

- **Security**: Runs as non-root user (UID/GID 1000)
- **Podman Compatible**: Works seamlessly with Podman's user namespace mapping
- **Persistent Storage**: Separate volumes for configuration and TipToi device

## Quick Start

### Using Podman

```bash
podman run -d \
  --rm \
  --name ttmp32gme \
  --publish 8080:8080 \
  --volume ttmp32gme-data:/data \
  --volume /path/to/tiptoi:/mnt/tiptoi:Z \
  thawn/ttmp32gme:latest
```

**Note for Podman users**: The `:Z` flag on the TipToi volume enables proper SELinux labeling for shared access.

### Using Docker (Alternative)

```bash
docker run -d \
  --rm \
  --name ttmp32gme \
  --publish 8080:8080 \
  --volume ttmp32gme-data:/data \
  --volume /path/to/tiptoi:/mnt/tiptoi \
  thawn/ttmp32gme:latest
```

## Volume Mounts

- **`/data`**: Application data (database, generated library files)
  - First run: Container initializes this directory with default config
  - Subsequent runs: Uses existing data for persistence

- **`/mnt/tiptoi`**: TipToi pen mount point
  - Mount your TipToi device here to directly write generated files

## User Permissions

The container runs as user `ttmp32gme` (UID 1000, GID 1000).

### For Podman Users

Podman automatically maps the container user to your host user, so permissions work seamlessly:

```bash
# Your files will be owned by your user on the host
podman run --rm \
  --volume ./my-data:/data \
  --volume /media/tiptoi:/mnt/tiptoi:Z \
  --publish 8080:8080 \
  thawn/ttmp32gme:latest
```

### For Docker Users

If you encounter permission issues, you can use these options:

1. **Option 1**: Match your user ID (recommended)
```bash
docker run --user $(id -u):$(id -g) \
  --volume ./my-data:/data \
  --volume /media/tiptoi:/mnt/tiptoi \
  --publish 8080:8080 \
  thawn/ttmp32gme:latest
```

2. **Option 2**: Adjust host directory permissions
```bash
sudo chown -R 1000:1000 ./my-data
```

## Accessing the Application

Once running, open your web browser to:
- **Local access**: http://localhost:8080
- **Network access**: http://your-server-ip:8080

## Command Line Arguments

You can pass additional command line arguments to the container:

```bash
# Increase verbosity
docker run thawn/ttmp32gme -vv

# Combine with volume mounts
docker run -d \
  --publish 8080:8080 \
  --volume ttmp32gme-data:/data \
  thawn/ttmp32gme:latest -v

# Show help
docker run --rm thawn/ttmp32gme --help
```

Available arguments (see `--help` for full list):
- `-v`, `--verbose`: Increase verbosity (INFO level)
- `-vv`: Extra verbosity (DEBUG level)
- `--port PORT`: Custom port (must also update `--publish`, e.g., `-p 9000:9000 thawn/ttmp32gme --port=9000`)
- `--host HOST`: Server bind address
- `--no-browser`: Don't open browser on start (always set in container)

**Note**: The container automatically includes default arguments `--host=0.0.0.0 --port=8080 --database=/data/config.sqlite --library=/data/library`. Any additional arguments you provide are appended to these defaults. If you provide an argument that conflicts with a default (e.g., `--port`), the last value wins (yours will override the default).

## Environment Variables

You can configure the application using environment variables instead of command line arguments:

```bash
# Use environment variables
docker run -d \
  --env TTMP32GME_PORT=9000 \
  --env TTMP32GME_VERBOSE=2 \
  --publish 9000:9000 \
  --volume ttmp32gme-data:/data \
  thawn/ttmp32gme:latest

# Combine environment variables with command line arguments
# Command line arguments override environment variables
docker run -d \
  --env TTMP32GME_PORT=9000 \
  --publish 8080:8080 \
  thawn/ttmp32gme:latest --port=8080
```

Available environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `TTMP32GME_HOST` | `0.0.0.0` | Server bind address |
| `TTMP32GME_PORT` | `8080` | Server port |
| `TTMP32GME_DATABASE` | `/data/config.sqlite` | Path to database file |
| `TTMP32GME_LIBRARY` | `/data/library` | Path to library directory |
| `TTMP32GME_VERBOSE` | - | Verbosity level: `1`/`v`/`info` for INFO, `2`/`vv`/`debug` for DEBUG |
| `TTMP32GME_NO_BROWSER` | - | Set to `true` or `1` to disable browser auto-open |
| `TTMP32GME_DEV` | - | Set to `true` or `1` to use Flask development server |

**Note**: Command line arguments take precedence over environment variables. This allows you to set defaults with environment variables and override them with command line arguments when needed.

## Security Features

This container implements security best practices:

- ✅ **Non-root user**: Runs as dedicated `ttmp32gme` user
- ✅ **Minimal permissions**: Files owned by user with 775/664 permissions
- ✅ **Explicit volumes**: Declared volume mount points
- ✅ **Health checks**: Automatic container health monitoring
- ✅ **Podman ready**: Full compatibility with Podman's rootless mode

## Troubleshooting

### Permission denied errors

If you get "permission denied" errors when accessing volumes:

**For Podman**:
```bash
# Add :Z flag for SELinux systems
podman run --volume /path/to/data:/data:Z ...
```

**For Docker**:
```bash
# Match your user ID
docker run --user $(id -u):$(id -g) ...
```

### Cannot write to TipToi device

Ensure your TipToi device is mounted with write permissions:
```bash
# Check current permissions
ls -la /media/tiptoi

# If needed, adjust permissions
sudo chmod 775 /media/tiptoi
```
