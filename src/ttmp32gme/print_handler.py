"""Print handling module for ttmp32gme - creates print layouts."""

import logging
import os
import platform
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import render_template

from ttmp32gme.build.file_handler import get_executable_path
from ttmp32gme.db_handler import DBHandler
from ttmp32gme.tttool_handler import create_oids, get_sorted_tracks

logger = logging.getLogger(__name__)


def format_tracks(
    album: Dict[str, Any], oid_map: Dict[str, Dict[str, int]], db_handler: DBHandler
) -> str:
    """Format track list with OID codes for printing.

    Args:
        album: Album dictionary containing track information
        oid_map: Mapping of script names to OID codes (e.g., {"t0": {"code": 2663}})
        db_handler: Database handler instance for accessing album data

    Returns:
        HTML content for track list with embedded OID images
    """
    content = ""
    tracks = get_sorted_tracks(album)

    for i, track_key in enumerate(tracks):
        track = album[track_key]
        tt_script = track.get("tt_script") or f"t{i}"
        oid_code = oid_map.get(tt_script, {}).get("code", 0)

        # Create OID image
        oid_files = create_oids([oid_code], 24, db_handler)
        oid_file = oid_files[0]
        oid_path = f"/images/{oid_file.name}"

        # File is automatically served via Flask route in ttmp32gme.py

        content += '<li class="list-group-item">'
        content += (
            '<table width="100%"><tr><td><div class="img-6mm track-img-container">'
        )
        content += (
            f'<img class="img-24mm" src="{oid_path}" alt="oid {oid_code}"></div></td>'
        )

        duration_min = track.get("duration", 0) // 60000
        duration_sec = (track.get("duration", 0) // 1000) % 60

        content += f'<td class="track-title">{i + 1}. {track.get("title", "")}</td>'
        content += (
            f'<td class="runtime">(<strong>{duration_min:02d}:{duration_sec:02d}'
            f"</strong>)</td>"
        )
        content += "</tr></table></li>\n"

    return content


def format_controls(oid_map: Dict[str, Dict[str, int]], db_handler: DBHandler) -> str:
    """Format playback controls with OID codes.

    Args:
        oid_map: Mapping of script names to OID codes (e.g., {"play": {"code": 3947}})
        db_handler: Database handler instance for creating OID images

    Returns:
        HTML content for playback controls (prev, play, stop, next buttons)
    """
    scripts = ["prev", "play", "stop", "next"]
    icons = ["backward", "play", "stop", "forward"]
    oids = [oid_map.get(script, {}).get("code", 0) for script in scripts]

    oid_files = create_oids(oids, 24, db_handler)

    template = (
        '<a class="btn btn-default play-control">'
        '<img class="img-24mm play-img" src="{}" alt="oid: {}">'
        '<span class="glyphicon glyphicon-{}"></span></a>'
    )

    content = ""
    for _i, (oid_file, oid, icon) in enumerate(zip(oid_files, oids, icons)):
        oid_path = f"/images/{oid_file.name}"
        # File is automatically served via Flask route in ttmp32gme.py
        content += template.format(oid_path, oid, icon)

    return content


def format_track_control(
    track_no: int, oid_map: Dict[str, Dict[str, int]], db_handler: DBHandler
) -> str:
    """Format a single track control button.

    Args:
        track_no: Track number (1-indexed)
        oid_map: Mapping of script names to OID codes (e.g., {"t0": {"code": 2663}})
        db_handler: Database handler instance for creating OID images

    Returns:
        HTML content for track control button with embedded OID image
    """
    script = f"t{track_no - 1}"
    oid = oid_map.get(script, {}).get("code", 0)

    oid_files = create_oids([oid], 24, db_handler)
    oid_file = oid_files[0]
    oid_path = f"/images/{oid_file.name}"

    # File is automatically served via Flask route in ttmp32gme.py

    template = (
        '<a class="btn btn-default play-control">'
        '<img class="img-24mm play-img" src="{}" alt="oid: {}">{}</a>'
    )

    return template.format(oid_path, oid, track_no)


def format_main_oid(oid: int, db_handler: DBHandler) -> str:
    """Format main OID image for an album.

    Args:
        oid: Album OID number
        db_handler: Database handler instance for creating OID images

    Returns:
        HTML img tag with embedded OID image
    """
    oid_files = create_oids([oid], 24, db_handler)
    oid_file = oid_files[0]
    oid_path = f"/images/{oid_file.name}"

    # File is automatically served via Flask route in ttmp32gme.py

    return f'<img class="img-24mm play-img" src="{oid_path}" alt="oid: {oid}">'


def format_cover(album: Dict[str, Any]) -> str:
    """Format cover image for an album.

    Args:
        album: Album dictionary containing picture_filename and oid

    Returns:
        HTML img tag for cover image, or empty string if no cover exists
    """
    if album.get("picture_filename"):
        return (
            f'<img class="img-responsive cover-img" '
            f'src="/images/{album["oid"]}/{album["picture_filename"]}" '
            f'alt="cover">'
        )
    return ""


def create_print_layout(
    oids: List[int], template: Any, config: Dict[str, Any], db_handler: DBHandler
) -> str:
    """Create print layout for selected albums.

    Args:
        oids: List of album OIDs to include in print layout
        template: Flask template object for rendering (unused, kept for compatibility)
        config: Configuration dictionary with print settings
        db_handler: Database handler instance for accessing album data

    Returns:
        HTML content for complete print layout including all albums and controls
    """
    content = ""

    # Get OID map from database
    script_codes = db_handler.fetchall("SELECT script, code FROM script_codes")
    oid_map = {row[0]: {"code": row[1]} for row in script_codes}

    controls = format_controls(oid_map, db_handler)

    for oid in oids:
        if not oid:
            continue

        album = db_handler.get_album(oid)
        if not album:
            logger.error(f"Album with OID {oid} not found")
            continue

        if not album.get("gme_file"):
            # Create GME if it doesn't exist
            from ttmp32gme.tttool_handler import make_gme

            make_gme(oid, config, db_handler)
            album = db_handler.get_album(oid)

            # If still no album after make_gme, skip
            if not album:
                logger.error(f"Failed to create GME for OID {oid}")
                continue

            # Refresh OID map after creating GME
            script_codes = db_handler.fetchall("SELECT script, code FROM script_codes")
            oid_map = {row[0]: {"code": row[1]} for row in script_codes}

        # Prepare album data for template
        album["track_list"] = format_tracks(album, oid_map, db_handler)
        album["play_controls"] = controls
        album["main_oid_image"] = format_main_oid(oid, db_handler)
        album["formatted_cover"] = format_cover(album)

        # Create HTML for album
        content += render_template("printing_contents.html", **album)

    # Add general controls
    content += '<div id="general-controls" class="row general-controls">'
    content += '  <div class="col-xs-6 col-xs-offset-3 general-controls" style="margin-bottom:10px;">'
    content += (
        f'<div class="btn-group btn-group-lg btn-group-justified">{controls}</div>'
    )
    content += "  </div>"

    # Add general track controls
    content += '<div class="col-xs-12" style="margin-bottom:10px;">'
    content += '<div class="btn-group btn-group-lg btn-group-justified">'

    max_track_controls = config.get("print_max_track_controls", 24)
    counter = 1
    while counter <= max_track_controls:
        content += format_track_control(counter, oid_map, db_handler)
        if counter < max_track_controls and (counter % 12) == 0:
            content += "</div></div>"
            content += '<div class="col-xs-12" style="margin-bottom:10px;">'
            content += '<div class="btn-group btn-group-lg btn-group-justified">'
        counter += 1

    content += "</div></div></div>"

    return content


def create_pdf(
    port: int,
    chromium_names: Tuple[str, ...] = (
        "chromium",
        "chromium-browser",
        "google-chrome",
        "chrome",
    ),
) -> Optional[Path]:
    """Create PDF from print layout using Chromium headless.

    Args:
        port: Server port number for accessing the print page via HTTP

    Returns:
        Path to created temporary PDF file, or None if PDF creation failed
    """
    # Try multiple possible chromium binary names
    fallback_options = ("google-chrome", "chrome")
    chromium_path = None
    found_name = None

    for name in chromium_names:
        chromium_path = get_executable_path(name)
        if chromium_path:
            found_name = name
            break

    if not chromium_path:
        logger.error("Could not create pdf, chromium not found.")
        return None

    # Create PDF in a temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix="ttmp32gme_print_")
    pdf_file = Path(temp_path)
    # Close the file descriptor as chromium will write to the file
    os.close(temp_fd)

    args = [
        chromium_path,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_file}",
        f"http://localhost:{port}/pdf",
    ]

    logger.info(f"Creating PDF with {found_name}: {' '.join(args)}")

    try:
        # Run chromium and check if it starts successfully
        process = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Wait for the pdf to be created or process to exit
        timeout = 10  # seconds
        for _ in range(timeout):
            # check if process has exited
            returncode = process.poll()
            if returncode is not None:
                break
            time.sleep(1)

        # Final check if PDF was created with content
        if pdf_file.exists() and pdf_file.stat().st_size > 0:
            return pdf_file
        else:
            logger.warning(
                f"PDF file was not created within the timeout period of {timeout} seconds. Checking fallback options..."
            )
            stdout, stderr = process.communicate()
            logger.debug(f"{found_name} stdout: {stdout}")
            logger.debug(f"{found_name} stderr: {stderr}")
            if chromium_path in fallback_options:
                logger.error("PDF creation failed. Exhausted fallback options.")
                return None
            else:
                logger.info("Trying google-chrome fallback for PDF creation.")
                return create_pdf(port, chromium_names=fallback_options)

    except Exception as e:
        logger.error(f"Could not create PDF: {e}")
        return None


def format_print_button() -> str:
    """Format the print button HTML based on platform and chromium availability.

    Returns:
        HTML string for print/PDF button(s) appropriate for the current platform
    """
    if platform.system() == "Windows":
        return (
            '<button type="button" id="pdf-save" class="btn btn-primary" '
            'data-toggle="popover" title="Save as pdf. The PDF usually prints better than the webpage.">'
            "Save as PDF</button>"
        )

    # Try multiple possible chromium binary names
    chromium_names = ["chromium", "chromium-browser", "google-chrome", "chrome"]
    chromium_path = None

    for name in chromium_names:
        chromium_path = get_executable_path(name)
        if chromium_path:
            break

    if chromium_path:
        return (
            '<button type="button" class="btn btn-info" onclick="javascript:window.print()">'
            "Print This Page</button> "
            '<button type="button" id="pdf-save" class="btn btn-primary" '
            'data-toggle="popover" title="Save as pdf. The PDF usually prints better than the webpage.">'
            "Save as PDF</button>"
        )

    return '<button type="button" class="btn btn-info" onclick="javascript:window.print()">Print This Page</button>'


def generate_pdf_with_threading(
    port: int, timeout: int = 60
) -> Dict[str, Optional[Any]]:
    """Generate PDF using threading to avoid server deadlock.

    This function generates a PDF in a separate thread to avoid blocking
    the server when Chromium needs to make a request back to the server
    to render the page.

    Args:
        port: Server port number for accessing the print page via HTTP
        timeout: Maximum time in seconds to wait for PDF generation (default: 60)

    Returns:
        Dictionary with the following keys:
        - 'success': Boolean indicating if PDF generation succeeded
        - 'file': Path to the generated PDF file (if successful)
        - 'error': Error message (if failed)
        - 'timeout': Boolean indicating if operation timed out
    """
    # Use threading to avoid deadlock with Waitress
    # The PDF generation spawns Chromium which needs to make a request back
    # to this server. By using a thread, we ensure the request handler
    # doesn't block all available threads.
    pdf_result: Dict[str, Optional[Any]] = {"file": None, "error": None}
    pdf_event = threading.Event()

    def generate_pdf_async() -> None:
        """Generate PDF in a separate thread to avoid blocking."""
        try:
            pdf_result["file"] = create_pdf(port)
        except Exception as e:
            pdf_result["error"] = str(e)
        finally:
            pdf_event.set()

    # Start PDF generation in background thread
    pdf_thread = threading.Thread(target=generate_pdf_async, daemon=True)
    pdf_thread.start()

    # Wait for PDF generation to complete (with timeout)
    # This allows other threads to handle Chromium's /pdf request
    if pdf_event.wait(timeout=timeout):
        if pdf_result["error"]:
            logger.error(f"PDF generation error: {pdf_result['error']}")
            return {
                "success": False,
                "file": None,
                "error": f"PDF generation failed: {pdf_result['error']}",
                "timeout": False,
            }
        elif pdf_result["file"]:
            logger.info(f"PDF generated successfully: {pdf_result['file']}")
            return {
                "success": True,
                "file": pdf_result["file"],
                "error": None,
                "timeout": False,
            }
        else:
            logger.error("PDF generation failed without specific error")
            return {
                "success": False,
                "file": None,
                "error": "PDF generation failed",
                "timeout": False,
            }
    else:
        # Timeout occurred
        logger.error(f"PDF generation timed out after {timeout} seconds")
        return {
            "success": False,
            "file": None,
            "error": "PDF generation timed out",
            "timeout": True,
        }
