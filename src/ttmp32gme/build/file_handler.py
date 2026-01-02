"""Build and file handling utilities for ttmp32gme."""

import logging
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def get_local_storage() -> Path:
    """Get the local storage directory for configuration and library.

    Returns:
        Path to local storage directory
    """
    if platform.system() == "Windows":
        base_dir = Path(os.environ.get("APPDATA", "."))
    elif platform.system() == "Darwin":  # macOS
        base_dir = Path.home() / "Library" / "Application Support"
    else:  # Linux and others
        base_dir = Path.home() / ".ttmp32gme"

    if platform.system() != "Linux":
        storage_dir = base_dir / "ttmp32gme"
    else:
        storage_dir = base_dir

    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


def get_default_library_path() -> Path:
    """Get the default library path.

    Returns:
        Path to default library directory
    """
    library = get_local_storage() / "library"
    library.mkdir(parents=True, exist_ok=True)
    return library


def check_config_file() -> Path:
    """Check for and initialize config file if needed.

    Returns:
        Path to config file
    """
    config_dir = get_local_storage()
    config_file = config_dir / "config.sqlite"

    if not config_file.exists():
        # Copy default config from package
        src_dir = Path(__file__).parent.parent
        default_config = src_dir / "config.sqlite"
        if default_config.exists():
            shutil.copy(default_config, config_file)
        else:
            raise FileNotFoundError(
                f"Could not find default config file at {default_config}"
            )

    return config_file


def make_temp_album_dir(temp_name: int, library_path: Optional[Path] = None) -> Path:
    """Create a temporary album directory.

    Args:
        temp_name: Numeric identifier for temp directory
        library_path: Optional library path, uses default if not provided

    Returns:
        Path to temporary album directory
    """
    if library_path is None:
        library_path = get_default_library_path()

    album_path = library_path / "temp" / str(temp_name)
    album_path.mkdir(parents=True, exist_ok=True)
    return album_path


def make_new_album_dir(album_title: str, library_path: Optional[Path] = None) -> Path:
    """Create a new album directory with unique name.

    Args:
        album_title: Title for the album
        library_path: Optional library path, uses default if not provided

    Returns:
        Path to new album directory
    """
    if library_path is None:
        library_path = get_default_library_path()

    # Make sure no album hogs the temp directory
    if album_title == "temp":
        album_title = "temp_0"

    album_path = library_path / album_title
    count = 0
    while album_path.exists():
        album_path = library_path / f"{album_title}_{count}"
        count += 1

    album_path.mkdir(parents=True, exist_ok=True)
    return album_path


def move_to_album(temp_dir: Path, album_dir: Path) -> bool:
    """Move files from temp directory to album directory.

    Args:
        temp_dir: Source temporary directory
        album_dir: Destination album directory

    Returns:
        True if successful
    """
    try:
        for item in temp_dir.iterdir():
            shutil.move(str(item), str(album_dir / item.name))
        return True
    except Exception as e:
        logger.error(f"Error moving album files: {e}")
        return False


def remove_temp_dir(temp_dir: Path) -> bool:
    """Remove a temporary directory.

    Args:
        temp_dir: Temporary directory to remove

    Returns:
        True if successful
    """
    try:
        shutil.rmtree(temp_dir)
        return True
    except Exception as e:
        logger.error(f"Error removing temp directory: {e}")
        return False


def clear_album(album_dir: Path) -> bool:
    """Clear all files from an album directory.

    Args:
        album_dir: Album directory to clear

    Returns:
        True if successful
    """
    try:
        for item in album_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        return True
    except Exception as e:
        logger.error(f"Error clearing album directory: {e}")
        return False


def remove_album(album_dir: Path) -> bool:
    """Remove an album directory completely.

    Args:
        album_dir: Album directory to remove

    Returns:
        True if successful
    """
    try:
        shutil.rmtree(album_dir)
        return True
    except Exception as e:
        logger.error(f"Error removing album directory: {e}")
        return False


def cleanup_filename(filename: str) -> str:
    """Clean up filename by removing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Cleaned filename
    """
    # Remove or replace invalid filename characters
    return re.sub(r"[^\.a-zA-Z0-9]", "_", filename)


def get_executable_path(executable_name: str) -> Optional[str]:
    """Find executable in PATH or common locations.

    Looks for bundled dependencies first (for PyInstaller builds),
    then checks PATH and common installation locations.

    Args:
        executable_name: Name of executable to find

    Returns:
        Path to executable or None if not found
    """
    # Check for bundled dependencies first (PyInstaller)
    if getattr(sys, "frozen", False):
        # Running in a PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)

        # Check platform-specific lib subdirectories
        if platform.system() == "Windows":
            bundled_path = bundle_dir / "lib" / "win" / f"{executable_name}.exe"
        elif platform.system() == "Darwin":
            bundled_path = bundle_dir / "lib" / "mac" / executable_name
        else:
            bundled_path = bundle_dir / "lib" / "linux" / executable_name

        if bundled_path.exists() and os.access(bundled_path, os.X_OK):
            return str(bundled_path)

        # Also check directly in bundle_dir
        if platform.system() == "Windows":
            direct_path = bundle_dir / f"{executable_name}.exe"
        else:
            direct_path = bundle_dir / executable_name

        if direct_path.exists() and os.access(direct_path, os.X_OK):
            return str(direct_path)
    else:
        # Check lib/ directory relative to source (for development)
        src_dir = Path(__file__).parent.parent.parent.parent
        if platform.system() == "Windows":
            bundled_path = src_dir / "lib" / "win" / f"{executable_name}.exe"
        elif platform.system() == "Darwin":
            bundled_path = src_dir / "lib" / "mac" / executable_name
        else:
            bundled_path = src_dir / "lib" / "linux" / executable_name

        if bundled_path.exists() and os.access(bundled_path, os.X_OK):
            return str(bundled_path)

    # Check if it's in PATH
    result = shutil.which(executable_name)
    if result:
        return result

    # Check common installation locations
    common_paths = [
        Path("/usr/local/bin"),
        Path("/usr/bin"),
        Path.home() / "bin",
        Path.home() / ".local" / "bin",
    ]

    if platform.system() == "Windows":
        executable_name += ".exe"

    for path in common_paths:
        full_path = path / executable_name
        if full_path.exists() and os.access(full_path, os.X_OK):
            return str(full_path)

    return None


def get_tiptoi_dir() -> Optional[Path]:
    """Find the TipToi device mount point.

    Returns:
        Path to TipToi mount point or None if not found
    """
    # Common mount points for TipToi
    possible_mounts = []

    if platform.system() == "Windows":
        # Check for removable drives with TipToi signature files
        for drive in "DEFGHIJKLMNOPQRSTUVWXYZ":
            drive_path = Path(f"{drive}:/")
            if drive_path.exists() and (drive_path / ".tiptoi").exists():
                possible_mounts.append(drive_path)
    elif platform.system() == "Darwin":  # macOS
        volumes = Path("/Volumes")
        if volumes.exists():
            for vol in volumes.iterdir():
                if (vol / ".tiptoi").exists():
                    possible_mounts.append(vol)
    else:  # Linux
        # Check common mount points
        media_user = Path(f"/media/{os.environ.get('USER', '')}")
        mnt_tiptoi = Path("/mnt/tiptoi")

        if media_user.exists():
            for mount in media_user.iterdir():
                if (mount / ".tiptoi").exists():
                    possible_mounts.append(mount)
        if mnt_tiptoi.exists() and (mnt_tiptoi / ".tiptoi").exists():
            possible_mounts.append(mnt_tiptoi)

    return possible_mounts[0] if possible_mounts else None


def get_gmes_already_on_tiptoi() -> List[str]:
    """Get list of GME files already on TipToi device.

    Returns:
        List of GME filenames found on the TipToi device
    """
    tiptoi_dir = get_tiptoi_dir()
    if not tiptoi_dir:
        return []

    gmes = []
    for file in tiptoi_dir.glob("*.gme"):
        gmes.append(file.name)

    return gmes


def delete_gme_tiptoi(gme_filename: str) -> bool:
    """Delete a GME file from TipToi device.

    Args:
        gme_filename: Name of GME file to delete

    Returns:
        True if successful
    """
    tiptoi_dir = get_tiptoi_dir()
    if not tiptoi_dir:
        logger.error("TipToi device not found")
        return False

    gme_file = tiptoi_dir / gme_filename
    if gme_file.exists():
        try:
            gme_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Error deleting GME from TipToi: {e}")
            return False

    return False


def copy_library(old_path: Path, new_path: Path) -> str:
    """Move library to a new location.

    Args:
        old_path: Current library path
        new_path: New library path

    Returns:
        Success message or error description
    """
    old_path = Path(old_path)
    new_path = Path(new_path)

    assert old_path.exists(), "Old library path does not exist."

    assert not (
        new_path.exists() and any(new_path.iterdir())
    ), "New library path already exists and is not empty."

    new_path.mkdir(parents=True, exist_ok=True)
    shutil.copytree(old_path, new_path, dirs_exist_ok=True)
    return True


def open_browser(host: str, port: int) -> bool:
    """Open the default web browser to the application URL.

    Args:
        host: Server host
        port: Server port

    Returns:
        True if successful
    """
    url = f"http://{host}:{port}/"

    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", url], check=True)
        elif platform.system() == "Windows":
            subprocess.run(["start", url], shell=True, check=True)
        else:  # Linux and others
            subprocess.run(["xdg-open", url], check=True)
        return True
    except Exception as e:
        logger.error(f"Could not open browser: {e}")
        return False
