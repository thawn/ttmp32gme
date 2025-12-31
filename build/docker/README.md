# ttmp32gme Docker/Podman Container

A containerized version of ttmp32gme that converts MP3/audio files into TipToi GME files.

## Features

- **Security**: Runs as non-root user (UID/GID 1000)
- **Podman Compatible**: Works seamlessly with Podman's user namespace mapping
- **Persistent Storage**: Separate volumes for configuration and TipToi device

## Quick Start

### Using Docker

```bash
docker run -d \
  --rm \
  --name ttmp32gme \
  --publish 8080:8080 \
  --volume ttmp32gme-data:/data \
  --volume /path/to/tiptoi:/mnt/tiptoi \
  thawn/ttmp32gme:latest
```

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

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| HOST | 0.0.0.0 | Server bind address |
| PORT | 8080 | Server port |

Example with custom settings:

```bash
docker run -d \
  --env HOST=127.0.0.1 \
  --env PORT=9000 \
  --publish 9000:9000 \
  --volume ttmp32gme-data:/data \
  thawn/ttmp32gme:latest
```

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
