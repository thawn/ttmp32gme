"""Main ttmp32gme Flask application."""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
)
from packaging.version import Version
from pydantic import ValidationError
from werkzeug.utils import secure_filename

from ttmp32gme import __version__
from ttmp32gme.build.file_handler import (
    check_config_file,
    get_default_library_path,
    get_executable_path,
    get_resource_path,
    get_tiptoi_dir,
    make_temp_album_dir,
    open_browser,
)
from ttmp32gme.db_handler import (
    AlbumUpdateModel,
    ConfigUpdateModel,
    DBHandler,
    LibraryActionModel,
)
from ttmp32gme.print_handler import (
    PRINT_PDF_FILENAME,
    create_pdf,
    create_print_layout,
    format_print_button,
)
from ttmp32gme.tttool_handler import copy_gme, delete_gme_tiptoi, make_gme

# Configure logging (default to WARNING, can be overridden by -v flags)
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create Flask app
# Configure paths for both development and PyInstaller
if getattr(sys, "frozen", False):
    # Running in PyInstaller bundle
    base_path = Path(getattr(sys, "_MEIPASS", "."))
    template_folder = str(base_path / "templates")
    static_folder = str(base_path / "assets")
else:
    # Running in development
    template_folder = "../templates"
    static_folder = "../assets"

app = Flask(
    __name__,
    static_folder=static_folder,
    static_url_path="/assets/",
    template_folder=template_folder,
)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB max upload

# Global state TODO: use Flask global or app context instead
db_handler = None
config = {}
file_count = 0
album_count = 0
current_album = None
file_list = []
album_list = []
print_content = (
    'Please go to the /print page, configure your layout, and click "save as pdf"'
)

# Custom paths (set via command line or defaults)
custom_db_path = None
custom_library_path = None


def get_db():
    """Get database handler."""
    global db_handler
    if db_handler is None:
        if custom_db_path:
            config_file = Path(custom_db_path)
            # Ensure parent directory exists
            config_file.parent.mkdir(parents=True, exist_ok=True)
            # If custom path doesn't exist, copy default config
            if not config_file.exists():
                default_config = get_resource_path("ttmp32gme/config.sqlite")
                if default_config.exists():
                    import shutil

                    shutil.copy(default_config, config_file)
        else:
            config_file = check_config_file()
        db_handler = DBHandler(str(config_file))
        db_handler.connect()
    return db_handler


def fetch_config() -> Dict[str, Any]:
    """Fetch configuration from database."""
    db = get_db()

    temp_config = db.get_config()

    # Ensure library_path is set (but don't override if already set in database)
    if not temp_config.get("library_path"):
        # No path in database, use custom path or default
        if custom_library_path:
            default_path = str(custom_library_path)
        else:
            default_path = str(get_default_library_path())

        # Save to database
        db.execute(
            "INSERT OR REPLACE INTO config (param, value) VALUES (?, ?)",
            ("library_path", default_path),
        )
        db.commit()
        logger.info(f"Initialized library_path in database: {default_path}")
        temp_config["library_path"] = default_path

    # convert strings to numeric types where appropriate
    if "port" in temp_config:
        temp_config["port"] = int(temp_config["port"])
    if "tt_dpi" in temp_config:
        temp_config["tt_dpi"] = int(temp_config["tt_dpi"])
    if "tt_pixel-size" in temp_config:
        temp_config["tt_pixel-size"] = int(temp_config["tt_pixel-size"])
    if "print_num_cols" in temp_config:
        temp_config["print_num_cols"] = int(temp_config["print_num_cols"])
    if "print_max_track_controls" in temp_config:
        temp_config["print_max_track_controls"] = int(
            temp_config["print_max_track_controls"]
        )

    logger.debug(f"Fetched config: {temp_config}")
    return temp_config


# TODO: Move as property change method to DBHandler class
def save_config(config_params: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    """Save configuration to database."""
    global config

    db = get_db()
    answer = "Success."

    # Handle library path changes
    if "library_path" in config_params:
        new_path = Path(config_params["library_path"]).absolute()
        if config.get("library_path") and str(new_path) != config["library_path"]:
            logger.info(f"Moving library to new path: {new_path}")
            from ttmp32gme.build.file_handler import copy_library

            try:
                copy_library(Path(config["library_path"]), new_path)
                db.change_library_path(config["library_path"], new_path)
            except Exception as e:
                answer = f"Error moving library: {e}\nReverting to old path: {config['library_path']}"
                config_params["library_path"] = config["library_path"]
                logger.error(answer)
                import shutil

                shutil.rmtree(new_path, ignore_errors=True)

    # Validate DPI and pixel size
    if "tt_dpi" in config_params and "tt_pixel-size" in config_params:
        dpi = int(config_params["tt_dpi"])
        pixel_size = int(config_params["tt_pixel-size"])
        if dpi / pixel_size < 200:
            config_params["tt_dpi"] = config.get("tt_dpi")
            config_params["tt_pixel-size"] = config.get("tt_pixel-size")
            if answer == "Success.":
                answer = "OID pixels too large, please increase resolution and/or decrease pixel size."

    # Update database
    for param, value in config_params.items():
        db.execute("UPDATE config SET value=? WHERE param=?", (value, param))

    db.commit()
    config = fetch_config()
    return config, answer


def get_navigation(url: str) -> str:
    """Generate navigation HTML."""
    site_map = {
        "/": '<span class="glyphicon glyphicon-upload" aria-hidden="true"></span> Upload',
        "/library": '<span class="glyphicon glyphicon-th-list" aria-hidden="true"></span> Library',
        "/config": '<span class="glyphicon glyphicon-cog" aria-hidden="true"></span> Configuration',
        "/help": '<span class="glyphicon glyphicon-question-sign" aria-hidden="true"></span> Help',
    }

    nav = ""
    for path, label in site_map.items():
        if url == path:
            nav += f"<li class='active'><a href='{path}'>{label}</a></li>"
        else:
            nav += f"<li><a href='{path}'>{label}</a></li>"

    return nav


# Routes
@app.route("/")
def index():
    """Upload page."""
    global album_count, file_count, current_album

    album_count += 1
    file_count = 0
    current_album = make_temp_album_dir(album_count, Path(config["library_path"]))

    # Load static HTML content
    upload_html = get_resource_path("upload.html")
    with open(upload_html, "r") as f:
        content = f.read()

    return render_template(
        "base.html",
        title="Upload",
        strippedTitle="Upload",
        navigation=get_navigation("/"),
        content=content,
    )


@app.route("/", methods=["POST"])
def upload_post():
    """Handle file uploads."""
    global file_count, album_count, current_album

    if "qquuid" in request.form:
        if "_method" in request.form:
            # Delete temporary uploaded files
            file_uuid = request.form["qquuid"]
            if album_count < len(album_list) and file_uuid in album_list[album_count]:
                file_to_delete = album_list[album_count][file_uuid]
                try:
                    os.unlink(file_to_delete)
                    return jsonify({"success": True})
                except Exception as e:
                    logger.error(f"Error deleting file: {e}")
                    return jsonify({"success": False}), 500

        elif "qqfile" in request.files:
            # Handle file upload
            file = request.files["qqfile"]
            filename = secure_filename(request.form.get("qqfilename", str(file_count)))
            file_uuid = request.form["qquuid"]

            file_path = current_album / filename
            file.save(str(file_path))

            # Ensure album_list has enough elements
            while len(album_list) <= album_count:
                album_list.append({})

            album_list[album_count][file_uuid] = str(file_path)
            file_list.append(file_uuid)
            file_count += 1

            return jsonify({"success": True})

    elif "action" in request.form:
        # Copy albums to library
        db = get_db()
        logger.info(
            f"Copying albums to library. Album list has {len(album_list)} albums"
        )
        logger.info(f"Album list contents: {album_list}")
        db.create_library_entry(album_list, Path(config["library_path"]))

        # Reset state
        file_count = 0
        album_count = 0
        current_album = make_temp_album_dir(album_count, Path(config["library_path"]))
        file_list.clear()
        album_list.clear()

        return jsonify({"success": True})

    return jsonify({"success": False}), 400


@app.route("/library")
def library():
    """Library page."""
    library_html = get_resource_path("library.html")
    with open(library_html, "r") as f:
        content = f.read()

    return render_template(
        "base.html",
        title="Library",
        strippedTitle="Library",
        navigation=get_navigation("/library"),
        content=content,
    )


@app.route("/library", methods=["POST"])
def library_post():
    """Handle library operations."""
    db = get_db()
    action = request.form.get("action")

    if action == "list":
        albums = db.get_album_list()
        tiptoi_connected = get_tiptoi_dir() is not None
        return jsonify(
            {"success": True, "list": albums, "tiptoi_connected": tiptoi_connected}
        )

    elif action in [
        "update",
        "delete",
        "cleanup",
        "make_gme",
        "copy_gme",
        "delete_gme_tiptoi",
    ]:
        data = json.loads(request.form.get("data", "{}"))

        try:
            if action == "update":
                # Validate album update data
                try:
                    validated_data = AlbumUpdateModel(**data)
                    validated_dict = validated_data.model_dump(exclude_none=True)
                except ValidationError as e:
                    logger.error(f"Validation error in album update: {e}")
                    return jsonify({"success": False, "error": str(e)}), 400

                old_player_mode = validated_dict.pop("old_player_mode", None)
                oid = db.update_album(validated_dict)
                album = db.get_album(oid)

                if old_player_mode and old_player_mode != validated_dict.get(
                    "player_mode"
                ):
                    make_gme(oid, config, db)

                return jsonify({"success": True, "element": album})

            elif action in [
                "delete",
                "cleanup",
                "make_gme",
                "copy_gme",
                "delete_gme_tiptoi",
            ]:
                # Validate action data (requires uid)
                try:
                    validated_data = LibraryActionModel(**data)
                    uid = validated_data.uid
                except ValidationError as e:
                    logger.error(f"Validation error in {action}: {e}")
                    return jsonify({"success": False, "error": str(e)}), 400

                if action == "delete":
                    oid = db.delete_album(uid)
                    return jsonify({"success": True, "element": {"oid": oid}})

                elif action == "cleanup":
                    oid = db.cleanup_album(uid)
                    album = db.get_album(oid)
                    return jsonify({"success": True, "element": album})

                elif action == "make_gme":
                    oid = make_gme(uid, config, db)
                    album = db.get_album(oid)
                    return jsonify({"success": True, "element": album})

                elif action == "copy_gme":
                    oid = copy_gme(uid, config, db)
                    album = db.get_album(oid)
                    return jsonify({"success": True, "element": album})

                elif action == "delete_gme_tiptoi":
                    oid = delete_gme_tiptoi(uid, db)
                    album = db.get_album(oid)
                    return jsonify({"success": True, "element": album})

        except Exception as e:
            logger.error(f"Error in library operation: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    elif action == "add_cover":
        uid = request.form.get("uid")
        filename = request.form.get("qqfilename")
        file_data = request.files["qqfile"].read()

        try:
            # Validate uid
            try:
                uid_int = int(uid)
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "Invalid UID"}), 400

            oid = db.replace_cover(uid_int, filename, file_data)
            album = db.get_album(oid)
            return jsonify({"success": True, "uid": album})
        except Exception as e:
            logger.error(f"Error replacing cover: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({"success": False, "error": "Invalid action"}), 400


@app.route("/print")
def print_page():
    """Print page."""
    data = json.loads(request.args.get("data", "{}"))
    oids = data.get("oids", [])

    # Create print layout content
    content = create_print_layout(oids, None, config, get_db())

    return render_template(
        "print.html",
        title="Print",
        strippedTitle="Print",
        navigation=get_navigation("/print"),
        print_button=format_print_button(),
        content=content,
    )


@app.route("/print", methods=["POST"])
def print_post():
    """Handle print operations."""
    action = request.form.get("action")

    if action == "get_config":
        return jsonify({"success": True, "element": config})

    elif action in ["save_config", "save_pdf"]:
        data = json.loads(request.form.get("data", "{}"))

        if action == "save_config":
            # Validate print configuration data
            try:
                validated_data = ConfigUpdateModel(**data)
                validated_dict = validated_data.model_dump(exclude_none=True)
            except ValidationError as e:
                logger.error(f"Validation error in print config save: {e}")
                return jsonify({"success": False, "error": str(e)}), 400

            new_config, message = save_config(validated_dict)
            if message == "Success.":
                return jsonify({"success": True, "element": new_config})
            else:
                return jsonify({"success": False, "error": message}), 400

        elif action == "save_pdf":
            global print_content
            print_content = data.get("content", "")
            pdf_file = create_pdf(config["port"], Path(config["library_path"]))
            if pdf_file:
                return jsonify({"success": True})
            else:
                return (
                    jsonify({"success": False, "error": "PDF generation failed"}),
                    500,
                )

    return jsonify({"success": False, "error": "Invalid action"}), 400


@app.route("/pdf")
def pdf_page():
    """PDF generation page."""
    return render_template(
        "pdf.html",
        strippedTitle="PDF",
        content=print_content,
        page_size=config.get("print_page_size", "A4"),
        page_margin=config.get("print_page_margin", "0.5in"),
    )


@app.route("/config")
def config_page():
    """Configuration page."""
    config_html = get_resource_path("config.html")
    with open(config_html, "r") as f:
        content = f.read()

    return render_template(
        "base.html",
        title="Configuration",
        strippedTitle="Configuration",
        navigation=get_navigation("/config"),
        content=content,
    )


@app.route("/config", methods=["POST"])
def config_post():
    """Handle configuration updates."""
    action = request.form.get("action")

    if action == "update":
        data = json.loads(request.form.get("data", "{}"))

        # Validate configuration data
        try:
            validated_data = ConfigUpdateModel(**data)
            validated_dict = validated_data.model_dump(exclude_none=True)
        except ValidationError as e:
            logger.error(f"Validation error in config update: {e}")
            return jsonify({"success": False, "error": str(e)}), 400

        new_config, message = save_config(validated_dict)

        if message == "Success.":
            return jsonify(
                {
                    "success": True,
                    "config": {
                        "host": new_config["host"],
                        "port": new_config["port"],
                        "open_browser": new_config["open_browser"],
                        "audio_format": new_config["audio_format"],
                        "pen_language": new_config["pen_language"],
                        "library_path": new_config["library_path"],
                    },
                }
            )
        else:
            return jsonify({"success": False, "error": message}), 400

    elif action == "load":
        return jsonify(
            {
                "success": True,
                "config": {
                    "host": config["host"],
                    "port": config["port"],
                    "open_browser": config["open_browser"],
                    "audio_format": config["audio_format"],
                    "pen_language": config["pen_language"],
                    "library_path": config["library_path"],
                },
            }
        )

    return jsonify({"success": False}), 400


@app.route("/help")
def help_page():
    """Help page."""
    help_html = get_resource_path("help.html")
    with open(help_html, "r") as f:
        content = f.read()

    return render_template(
        "base.html",
        title="Help",
        strippedTitle="Help",
        navigation=get_navigation("/help"),
        content=content,
    )


@app.route("/images/<path:filename>")
def serve_dynamic_image(filename):
    """Serve dynamically generated images (OID codes, covers, etc.)."""
    db = get_db()

    # Check OID cache first
    oid_cache = db.get_oid_cache()
    image_path = oid_cache / filename
    if image_path.exists():
        return send_from_directory(oid_cache, filename)

    # Check if it's an album cover (format: oid/filename)
    parts = filename.split("/", 1)
    if len(parts) == 2:
        oid_str, cover_filename = parts
        try:
            db = get_db()
            row = db.fetchone(
                "SELECT path FROM gme_library WHERE oid=?", (int(oid_str),)
            )
            if row:
                album_path = Path(row[0])
                cover_path = album_path / cover_filename
                if cover_path.exists():
                    return send_from_directory(album_path, cover_filename)
        except Exception as e:
            logger.error(f"Error serving album cover: {e}")

    # Return 404 if file not found
    return "File not found", 404


@app.route("/download_gme/<int:oid>")
def download_gme(oid):
    """Download GME file for an album."""
    try:
        db = get_db()
        result = db.get_gme_file_info(oid)

        if not result:
            logger.error(f"Album with OID {oid} not found")
            return "Album not found", 404

        album_path, gme_filename = result

        if not gme_filename:
            logger.error(f"No GME file for album {oid}")
            return "GME file not created yet", 404

        album_dir = Path(album_path)
        gme_path = album_dir / gme_filename

        if not gme_path.exists():
            logger.error(f"GME file not found at {gme_path}")
            return "GME file not found on filesystem", 404

        logger.info(f"Serving GME file: {gme_filename} from {album_dir}")
        return send_from_directory(
            album_dir, gme_filename, as_attachment=True, download_name=gme_filename
        )
    except Exception as e:
        logger.error(f"Error downloading GME file: {e}")
        return "Error downloading GME file", 500


@app.route("/download_oid_images")
def download_oid_images():
    """Download all OID images as a ZIP file."""
    try:
        db = get_db()
        zip_file = db.create_oid_images_zip()

        if zip_file is None:
            return "No OID images available", 404

        return send_file(
            zip_file,
            mimetype="application/zip",
            as_attachment=True,
            download_name="oid_images.zip",
        )
    except Exception as e:
        logger.error(f"Error downloading OID images: {e}")
        return "Error creating OID images ZIP file", 500


@app.route("/download/print.pdf")
def download_print_pdf():
    """Download the generated print PDF file and clean it up afterwards."""
    try:
        library_path = Path(config["library_path"])
        pdf_file = library_path / PRINT_PDF_FILENAME

        if not pdf_file.exists():
            logger.error(f"PDF file not found at {pdf_file}")
            return (
                "PDF file not available. Please generate a new PDF from the Print page.",
                404,
            )

        logger.info(f"Serving PDF file: {pdf_file}")
        response = send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=PRINT_PDF_FILENAME,
        )

        # Clean up the PDF file after sending it
        # This ensures the next print request generates a fresh PDF
        try:
            pdf_file.unlink()
            logger.info(f"Cleaned up PDF file: {pdf_file}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up PDF file: {cleanup_error}")

        return response
    except Exception as e:
        logger.error(f"Error downloading PDF file: {e}")
        return "Error downloading PDF file", 500


def main():
    """Main entry point."""
    global config, custom_db_path, custom_library_path

    parser = argparse.ArgumentParser(
        description="ttmp32gme - TipToi MP3 to GME converter"
    )
    parser.add_argument("--port", "-p", type=int, help="Server port")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG)",
    )
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--database", type=str, help="Path to database file")
    parser.add_argument("--library", type=str, help="Path to library directory")
    parser.add_argument(
        "--no-browser", action="store_true", help="Do not open web browser on start"
    )

    args = parser.parse_args()

    # Set logging level based on verbose flag (do this early)
    if args.verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
        logger.info("Verbose mode enabled (INFO level)")
    elif args.verbose >= 2:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled (DEBUG level)")

    if args.version:
        print(f"ttmp32gme version {__version__}")
        return

    # Set custom paths from command-line arguments
    if args.database:
        custom_db_path = Path(args.database).absolute()
        logger.info(f"Using custom database path: {custom_db_path}")

    if args.library:
        custom_library_path = Path(args.library).absolute()
        # Ensure library directory exists
        custom_library_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using custom library path: {custom_library_path}")

    # Initialize database and config
    check_config_file() if not custom_db_path else custom_db_path
    db = get_db()
    config = fetch_config()

    # Check for database updates
    db_version = config.get("version", "0.1.0")
    if Version(__version__) > Version(db_version):
        logger.info("Updating config...")
        db.update_db()
        logger.info("Update successful.")
        config = fetch_config()

    # Override config with command-line args
    if args.port:
        config["port"] = args.port
    if args.host:
        config["host"] = args.host

    port = int(config.get("port", 10020))
    host = config.get("host", "127.0.0.1")

    # Check for tttool
    tttool_path = get_executable_path("tttool")
    if tttool_path:
        logger.info(f"Using tttool: {tttool_path}")
    else:
        logger.error("No useable tttool found")

    # Open browser if configured and not disabled by command-line argument
    if config.get("open_browser") == "TRUE" and not args.no_browser:
        open_browser(host, port)

    logger.info(f"Server running on http://{host}:{port}/")
    logger.info("Open this URL in your web browser to continue.")

    # Run Flask app (enable Flask debug mode only with -vv or more)
    app.run(host=host, port=port, debug=(args.verbose >= 2))


if __name__ == "__main__":
    main()
