# Installation

ttmp32gme can be installed on Windows, macOS, and Linux using several methods.

## Windows and macOS (Binary Installers)

### Download Pre-built Executables

The easiest way to use ttmp32gme on Windows and macOS is to download the pre-built executables:

1. Visit the [releases page](https://github.com/thawn/ttmp32gme/releases)
2. Download the appropriate installer for your platform
3. Extract the files to a directory of your choice
4. Run the executable
5. Open `http://localhost:10020` in your web browser

**Note**: The pre-built executables include all dependencies except tttool, which must be installed separately.

## Linux

### Python Installation (Recommended)

#### Requirements

* Python 3.11 or higher
* pip or [uv](https://github.com/astral-sh/uv) package manager
* tttool (see installation instructions below)
* Optional: ffmpeg (for OGG format support)

#### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/thawn/ttmp32gme.git
   cd ttmp32gme
   ```

2. **Install Python dependencies**:
   
   Using uv (recommended - faster):
   ```bash
   uv pip install -e .
   ```
   
   Or using pip:
   ```bash
   pip install -e .
   ```

3. **Install tttool** (see [Installing tttool](#installing-tttool) below)

4. **Optional: Install ffmpeg** for OGG support:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # Fedora
   sudo dnf install ffmpeg
   
   # Arch Linux
   sudo pacman -S ffmpeg
   ```

5. **Run ttmp32gme**:
   ```bash
   ttmp32gme
   ```
   
   Or:
   ```bash
   python -m ttmp32gme.ttmp32gme
   ```

6. **Access the interface**:
   Open `http://localhost:10020` in your web browser

### Docker Installation

Docker provides an isolated environment with all dependencies included.

#### Using Pre-built Docker Image

1. **Pull the image**:
   ```bash
   docker pull thawn/ttmp32gme:latest
   ```

2. **Run the container**:
   ```bash
   docker run -d --rm \
     --publish 8080:8080 \
     --volume ~/.ttmp32gme:/var/lib/ttmp32gme \
     --volume /media/${USER}/tiptoi:/mnt/tiptoi \
     --name ttmp32gme \
     thawn/ttmp32gme:latest
   ```
   
   This command:
   - Publishes the web interface on port 8080
   - Stores the library in `~/.ttmp32gme`
   - Mounts the TipToi pen at `/mnt/tiptoi` (adjust path as needed)

3. **Access the interface**:
   Open `http://localhost:8080` in your web browser

#### Using Docker Compose

1. **Download docker-compose.yml**:
   ```bash
   wget https://raw.githubusercontent.com/thawn/ttmp32gme/master/docker-compose.yml
   ```

2. **Start the service**:
   ```bash
   docker-compose up -d
   ```

3. **Access the interface**:
   Open `http://localhost:8080` in your web browser

#### Using the Docker Installer Script

1. **Download the installer files**:
   ```bash
   wget https://raw.githubusercontent.com/thawn/ttmp32gme/master/build/docker/install.sh
   wget https://raw.githubusercontent.com/thawn/ttmp32gme/master/build/docker/ttmp32gme
   ```

2. **Install**:
   ```bash
   sudo bash install.sh
   ```

3. **Start the service**:
   ```bash
   ttmp32gme start
   ```
   
   If your TipToi is mounted at a custom location:
   ```bash
   ttmp32gme start /path/to/tiptoi
   ```

4. **Stop the service**:
   ```bash
   ttmp32gme stop
   ```

## Installing tttool

tttool is the underlying tool that creates GME files. It must be installed separately.

### Ubuntu/Debian

```bash
# Add the tttool repository
sudo add-apt-repository ppa:tttool/tttool
sudo apt-get update
sudo apt-get install tttool
```

### macOS

```bash
# Using Homebrew
brew install tttool
```

### From Source

See the [tttool installation guide](https://github.com/entropia/tip-toi-reveng#installation) for detailed instructions on building from source.

### Verify Installation

```bash
tttool --version
```

## Command Line Options

When running ttmp32gme from the command line, you can customize its behavior:

```bash
ttmp32gme [OPTIONS]
```

### Available Options

* `--port PORT`, `-p PORT`: Server port (default: 10020)
* `--host HOST`: Server host (default: 127.0.0.1)
* `--database DATABASE`: Custom database file path (default: ~/.ttmp32gme/config.sqlite)
* `--library LIBRARY`: Custom library directory (default: ~/.ttmp32gme/library)
* `--debug`, `-d`: Enable debug mode
* `--version`, `-v`: Show version information

### Examples

**Start on a different port**:
```bash
ttmp32gme --port 8080
```

**Use custom database and library paths**:
```bash
ttmp32gme --database /path/to/custom.sqlite --library /path/to/custom/library
```

**Run on all network interfaces** (accessible from other computers):
```bash
ttmp32gme --host 0.0.0.0 --port 8080
```

**Enable debug logging**:
```bash
ttmp32gme --debug
```

## Verifying Installation

After installation, verify that ttmp32gme is working:

1. **Check version**:
   ```bash
   ttmp32gme --version
   ```

2. **Start the server**:
   ```bash
   ttmp32gme
   ```

3. **Test the web interface**:
   ```bash
   curl http://localhost:10020/
   ```
   
   This should return HTML content.

4. **Access in browser**:
   Open `http://localhost:10020` and verify the interface loads correctly.

## Troubleshooting Installation

### Python Version Issues

Ensure you have Python 3.11 or higher:
```bash
python --version
```

If you have multiple Python versions, use:
```bash
python3.11 -m pip install -e .
```

### tttool Not Found

If you get "tttool not found" errors:

1. Verify tttool is installed: `which tttool`
2. Ensure tttool is in your PATH
3. Try installing from a different source

### Permission Errors

If you encounter permission errors:

* Use `pip install --user -e .` instead of system-wide installation
* Or use a virtual environment:
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install -e .
  ```

### Port Already in Use

If port 10020 is already in use:
```bash
ttmp32gme --port 8080
```

## Next Steps

* Read the [Getting Started](getting-started.md) guide
* Learn about [usage](usage.md)
* Configure [print settings](print-configuration.md)
