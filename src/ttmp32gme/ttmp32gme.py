"""Main ttmp32gme Flask application."""

import os
import sys
import sqlite3
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import json

from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from werkzeug.utils import secure_filename
from packaging.version import Version

from .db_update import update as db_update
from .build.file_handler import (
    check_config_file, get_default_library_path, 
    make_temp_album_dir, get_tiptoi_dir, open_browser,
    get_executable_path
)
from .library_handler import (
    create_library_entry, get_album_list, get_album, get_album_online,
    update_album, delete_album, cleanup_album, replace_cover
)
from .tttool_handler import make_gme, copy_gme, delete_gme_tiptoi
from .print_handler import create_print_layout, create_pdf, format_print_button
from . import __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__,
           static_folder='../assets',
           template_folder='../templates')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload

# Global state
db_connection = None
config = {}
file_count = 0
album_count = 0
current_album = None
file_list = []
album_list = []
print_content = 'Please go to the /print page, configure your layout, and click "save as pdf"'


def get_db():
    """Get database connection."""
    global db_connection
    if db_connection is None:
        config_file = check_config_file()
        db_connection = sqlite3.connect(str(config_file), check_same_thread=False)
        db_connection.row_factory = sqlite3.Row
    return db_connection


def fetch_config() -> Dict[str, Any]:
    """Fetch configuration from database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT param, value FROM config')
    
    temp_config = {row[0]: row[1] for row in cursor.fetchall()}
    
    if not temp_config.get('library_path'):
        temp_config['library_path'] = str(get_default_library_path())
    
    logger.debug(f'Fetched config: {temp_config}')
    return temp_config


def save_config(config_params: Dict[str, Any]) -> tuple[Dict[str, Any], str]:
    """Save configuration to database."""
    global config
    
    db = get_db()
    cursor = db.cursor()
    answer = 'Success.'
    
    # Handle library path changes
    if 'library_path' in config_params:
        new_path = Path(config_params['library_path'])
        if config.get('library_path') and str(new_path) != config['library_path']:
            logger.info(f'Moving library to new path: {new_path}')
            from .build.file_handler import move_library
            answer = move_library(
                Path(config['library_path']), 
                new_path, 
                db
            )
            if answer != 'Success.':
                config_params['library_path'] = config['library_path']
    
    # Validate DPI and pixel size
    if 'tt_dpi' in config_params and 'tt_pixel-size' in config_params:
        dpi = int(config_params['tt_dpi'])
        pixel_size = int(config_params['tt_pixel-size'])
        if dpi / pixel_size < 200:
            config_params['tt_dpi'] = config.get('tt_dpi')
            config_params['tt_pixel-size'] = config.get('tt_pixel-size')
            if answer == 'Success.':
                answer = 'OID pixels too large, please increase resolution and/or decrease pixel size.'
    
    # Update database
    for param, value in config_params.items():
        cursor.execute('UPDATE config SET value=? WHERE param=?', (value, param))
    
    db.commit()
    config = fetch_config()
    return config, answer


def get_navigation(url: str) -> str:
    """Generate navigation HTML."""
    site_map = {
        '/': '<span class="glyphicon glyphicon-upload" aria-hidden="true"></span> Upload',
        '/library': '<span class="glyphicon glyphicon-th-list" aria-hidden="true"></span> Library',
        '/config': '<span class="glyphicon glyphicon-cog" aria-hidden="true"></span> Configuration',
        '/help': '<span class="glyphicon glyphicon-question-sign" aria-hidden="true"></span> Help',
    }
    
    nav = ""
    for path, label in site_map.items():
        if url == path:
            nav += f"<li class='active'><a href='{path}'>{label}</a></li>"
        else:
            nav += f"<li><a href='{path}'>{label}</a></li>"
    
    return nav


# Routes
@app.route('/')
def index():
    """Upload page."""
    global album_count, file_count, current_album
    
    album_count += 1
    file_count = 0
    current_album = make_temp_album_dir(album_count, Path(config['library_path']))
    
    # Load static HTML content
    upload_html = Path(__file__).parent.parent / 'upload.html'
    with open(upload_html, 'r') as f:
        content = f.read()
    
    return render_template('base.html',
                         title='Upload',
                         strippedTitle='Upload',
                         navigation=get_navigation('/'),
                         content=content)


@app.route('/', methods=['POST'])
def upload_post():
    """Handle file uploads."""
    global file_count, album_list, file_list, album_count, current_album
    
    if 'qquuid' in request.form:
        if '_method' in request.form:
            # Delete temporary uploaded files
            file_uuid = request.form['qquuid']
            if album_count < len(album_list) and file_uuid in album_list[album_count]:
                file_to_delete = album_list[album_count][file_uuid]
                try:
                    os.unlink(file_to_delete)
                    return jsonify({'success': True})
                except Exception as e:
                    logger.error(f"Error deleting file: {e}")
                    return jsonify({'success': False}), 500
        
        elif 'qqfile' in request.files:
            # Handle file upload
            file = request.files['qqfile']
            filename = secure_filename(request.form.get('qqfilename', str(file_count)))
            file_uuid = request.form['qquuid']
            
            file_path = current_album / filename
            file.save(str(file_path))
            
            if album_count >= len(album_list):
                album_list.append({})
            
            album_list[album_count][file_uuid] = str(file_path)
            file_list.append(file_uuid)
            file_count += 1
            
            return jsonify({'success': True})
    
    elif 'action' in request.form:
        # Copy albums to library
        logger.info("Copying albums to library")
        create_library_entry(
            album_list,
            get_db(),
            Path(config['library_path'])
        )
        
        # Reset state
        file_count = 0
        album_count = 0
        current_album = make_temp_album_dir(album_count, Path(config['library_path']))
        file_list.clear()
        album_list.clear()
        
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 400


@app.route('/library')
def library():
    """Library page."""
    library_html = Path(__file__).parent.parent / 'library.html'
    with open(library_html, 'r') as f:
        content = f.read()
    
    return render_template('base.html',
                         title='Library',
                         strippedTitle='Library',
                         navigation=get_navigation('/library'),
                         content=content)


@app.route('/library', methods=['POST'])
def library_post():
    """Handle library operations."""
    db = get_db()
    action = request.form.get('action')
    
    if action == 'list':
        albums = get_album_list(db)
        tiptoi_connected = get_tiptoi_dir() is not None
        return jsonify({
            'success': True,
            'list': albums,
            'tiptoi_connected': tiptoi_connected
        })
    
    elif action in ['update', 'delete', 'cleanup', 'make_gme', 'copy_gme', 'delete_gme_tiptoi']:
        data = json.loads(request.form.get('data', '{}'))
        
        try:
            if action == 'update':
                old_player_mode = data.pop('old_player_mode', None)
                oid = update_album(data, db)
                album = get_album_online(oid, None, db)
                
                if old_player_mode and old_player_mode != data.get('player_mode'):
                    make_gme(oid, config, db)
                
                return jsonify({'success': True, 'element': album})
            
            elif action == 'delete':
                oid = delete_album(data['uid'], None, db, Path(config['library_path']))
                return jsonify({'success': True, 'element': {'oid': oid}})
            
            elif action == 'cleanup':
                oid = cleanup_album(data['uid'], None, db, Path(config['library_path']))
                album = get_album_online(oid, None, db)
                return jsonify({'success': True, 'element': album})
            
            elif action == 'make_gme':
                oid = make_gme(data['uid'], config, db)
                album = get_album_online(oid, None, db)
                return jsonify({'success': True, 'element': album})
            
            elif action == 'copy_gme':
                oid = copy_gme(data['uid'], config, db)
                album = get_album_online(oid, None, db)
                return jsonify({'success': True, 'element': album})
            
            elif action == 'delete_gme_tiptoi':
                oid = delete_gme_tiptoi(data['uid'], db)
                album = get_album_online(oid, None, db)
                return jsonify({'success': True, 'element': album})
        
        except Exception as e:
            logger.error(f"Error in library operation: {e}")
            return jsonify({'success': False}), 500
    
    elif action == 'add_cover':
        uid = request.form.get('uid')
        filename = request.form.get('qqfilename')
        file_data = request.files['qqfile'].read()
        
        try:
            oid = replace_cover(int(uid), filename, file_data, None, db)
            album = get_album_online(oid, None, db)
            return jsonify({'success': True, 'uid': album})
        except Exception as e:
            logger.error(f"Error replacing cover: {e}")
            return jsonify({'success': False}), 500
    
    return jsonify({'success': False}), 400


@app.route('/print')
def print_page():
    """Print page."""
    data = json.loads(request.args.get('data', '{}'))
    oids = data.get('oids', [])
    
    # Create print layout content
    content = create_print_layout(oids, None, config, None, get_db())
    
    return render_template('print.html',
                         title='Print',
                         strippedTitle='Print',
                         navigation=get_navigation('/print'),
                         print_button=format_print_button(),
                         content=content)


@app.route('/print', methods=['POST'])
def print_post():
    """Handle print operations."""
    action = request.form.get('action')
    
    if action == 'get_config':
        return jsonify({'success': True, 'element': config})
    
    elif action in ['save_config', 'save_pdf']:
        data = json.loads(request.form.get('data', '{}'))
        
        if action == 'save_config':
            new_config, message = save_config(data)
            if message == 'Success.':
                return jsonify({'success': True, 'element': new_config})
            else:
                return jsonify({'success': False}), 400, message
        
        elif action == 'save_pdf':
            global print_content
            print_content = data.get('content', '')
            pdf_file = create_pdf(config['port'], Path(config['library_path']))
            if pdf_file:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False}), 500
    
    return jsonify({'success': False}), 400


@app.route('/pdf')
def pdf_page():
    """PDF generation page."""
    return render_template('pdf.html',
                         strippedTitle='PDF',
                         content=print_content)


@app.route('/config')
def config_page():
    """Configuration page."""
    config_html = Path(__file__).parent.parent / 'config.html'
    with open(config_html, 'r') as f:
        content = f.read()
    
    return render_template('base.html',
                         title='Configuration',
                         strippedTitle='Configuration',
                         navigation=get_navigation('/config'),
                         content=content)


@app.route('/config', methods=['POST'])
def config_post():
    """Handle configuration updates."""
    action = request.form.get('action')
    
    if action == 'update':
        data = json.loads(request.form.get('data', '{}'))
        new_config, message = save_config(data)
        
        if message == 'Success.':
            return jsonify({
                'success': True,
                'config': {
                    'host': new_config['host'],
                    'port': new_config['port'],
                    'open_browser': new_config['open_browser'],
                    'audio_format': new_config['audio_format'],
                    'pen_language': new_config['pen_language'],
                    'library_path': new_config['library_path']
                }
            })
        else:
            return jsonify({'success': False}), 400, message
    
    elif action == 'load':
        return jsonify({
            'success': True,
            'config': {
                'host': config['host'],
                'port': config['port'],
                'open_browser': config['open_browser'],
                'audio_format': config['audio_format'],
                'pen_language': config['pen_language'],
                'library_path': config['library_path']
            }
        })
    
    return jsonify({'success': False}), 400


@app.route('/help')
def help_page():
    """Help page."""
    help_html = Path(__file__).parent.parent / 'help.html'
    with open(help_html, 'r') as f:
        content = f.read()
    
    return render_template('base.html',
                         title='Help',
                         strippedTitle='Help',
                         navigation=get_navigation('/help'),
                         content=content)


@app.route('/assets/<path:filename>')
def serve_asset(filename):
    """Serve static assets."""
    return send_from_directory(app.static_folder, filename)


@app.route('/assets/images/<path:filename>')
def serve_dynamic_image(filename):
    """Serve dynamically generated images (OID codes, covers, etc.)."""
    from .build.file_handler import get_oid_cache, get_default_library_path
    
    # Check OID cache first
    oid_cache = get_oid_cache()
    image_path = oid_cache / filename
    if image_path.exists():
        return send_from_directory(oid_cache, filename)
    
    # Check if it's an album cover (format: oid/filename)
    parts = filename.split('/', 1)
    if len(parts) == 2:
        oid_str, cover_filename = parts
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT path FROM gme_library WHERE oid=?', (int(oid_str),))
            row = cursor.fetchone()
            if row:
                album_path = Path(row[0])
                cover_path = album_path / cover_filename
                if cover_path.exists():
                    return send_from_directory(album_path, cover_filename)
        except (ValueError, Exception) as e:
            logger.error(f"Error serving album cover: {e}")
    
    # Return 404 if file not found
    return "File not found", 404


def main():
    """Main entry point."""
    global config
    
    parser = argparse.ArgumentParser(description='ttmp32gme - TipToi MP3 to GME converter')
    parser.add_argument('--port', '-p', type=int, help='Server port')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Server host')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode')
    parser.add_argument('--version', '-v', action='store_true', help='Show version')
    
    args = parser.parse_args()
    
    if args.version:
        print(f"ttmp32gme version {__version__}")
        return
    
    # Initialize database and config
    config_file = check_config_file()
    db = get_db()
    config = fetch_config()
    
    # Check for database updates
    db_version = config.get('version', '0.1.0')
    if Version(__version__) > Version(db_version):
        logger.info("Updating config...")
        db_update(db_version, db)
        logger.info("Update successful.")
        config = fetch_config()
    
    # Override config with command-line args
    if args.port:
        config['port'] = args.port
    if args.host:
        config['host'] = args.host
    
    port = int(config.get('port', 10020))
    host = config.get('host', '127.0.0.1')
    
    # Check for tttool
    tttool_path = get_executable_path('tttool')
    if tttool_path:
        logger.info(f"Using tttool: {tttool_path}")
    else:
        logger.error("No useable tttool found")
    
    # Open browser if configured
    if config.get('open_browser') == 'TRUE':
        open_browser(host, port)
    
    logger.info(f"Server running on http://{host}:{port}/")
    logger.info("Open this URL in your web browser to continue.")
    
    # Run Flask app
    app.run(host=host, port=port, debug=args.debug)


if __name__ == '__main__':
    main()
