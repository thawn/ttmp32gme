"""Library handling module for ttmp32gme - manages albums and tracks."""

import shutil
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from PIL import Image
import io

from .build.file_handler import (
    cleanup_filename, make_new_album_dir, 
    remove_album, clear_album
)

logger = logging.getLogger(__name__)


def oid_exist(oid: int, connection) -> bool:
    """Check if an OID exists in the database.
    
    Args:
        oid: OID to check
        connection: Database connection
        
    Returns:
        True if OID exists
    """
    cursor = connection.cursor()
    cursor.execute('SELECT oid FROM gme_library WHERE oid = ?', (oid,))
    return cursor.fetchone() is not None


def new_oid(connection) -> int:
    """Generate a new unique OID.
    
    Args:
        connection: Database connection
        
    Returns:
        New OID
    """
    cursor = connection.cursor()
    cursor.execute('SELECT oid FROM gme_library ORDER BY oid DESC')
    old_oids = [row[0] for row in cursor.fetchall()]
    
    if not old_oids:
        return 920
    
    if old_oids[0] < 999:
        # Free OIDs above the highest used OID
        return old_oids[0] + 1
    
    # Look for freed OIDs
    oid_set = set(old_oids)
    new_oid = old_oids[-1] + 1
    
    while new_oid < 1001 and new_oid in oid_set:
        new_oid += 1
    
    if new_oid == 1000:
        # Look for free OIDs below the default
        new_oid = old_oids[-1] - 1
        while new_oid > 0 and new_oid in oid_set:
            new_oid -= 1
        
        if new_oid > 1:
            return new_oid
        else:
            raise RuntimeError('Could not find a free OID. Try deleting OIDs from your library.')
    
    return new_oid


def write_to_database(table: str, data: Dict[str, Any], connection):
    """Write data to database table.
    
    Args:
        table: Table name
        data: Data dictionary
        connection: Database connection
    """
    fields = sorted(data.keys())
    values = [data[field] for field in fields]
    placeholders = ', '.join('?' * len(fields))
    query = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})"
    
    cursor = connection.cursor()
    cursor.execute(query, values)
    connection.commit()


def get_tracks(album: Dict[str, Any], connection) -> Dict[int, Dict[str, Any]]:
    """Get all tracks for an album.
    
    Args:
        album: Album dictionary
        connection: Database connection
        
    Returns:
        Dictionary of tracks indexed by track number
    """
    cursor = connection.cursor()
    cursor.execute(
        'SELECT * FROM tracks WHERE parent_oid=? ORDER BY track',
        (album['oid'],)
    )
    
    columns = [desc[0] for desc in cursor.description]
    tracks = {}
    
    for row in cursor.fetchall():
        track = dict(zip(columns, row))
        tracks[track['track']] = track
    
    return tracks


def update_table_entry(table: str, keyname: str, search_keys: List, 
                      data: Dict[str, Any], connection) -> bool:
    """Update a table entry.
    
    Args:
        table: Table name
        keyname: Key column name with condition (e.g., 'oid=?')
        search_keys: Values for the key condition
        data: Data to update
        connection: Database connection
        
    Returns:
        True if successful
    """
    fields = sorted(data.keys())
    values = [data[field] for field in fields]
    set_clause = ', '.join(f"{field}=?" for field in fields)
    query = f"UPDATE {table} SET {set_clause} WHERE {keyname}"
    
    cursor = connection.cursor()
    cursor.execute(query, values + search_keys)
    connection.commit()
    return True


def get_cover_filename(mimetype: Optional[str], picture_data: bytes) -> Optional[str]:
    """Generate a filename for cover image.
    
    Args:
        mimetype: Image MIME type
        picture_data: Image data
        
    Returns:
        Cover filename or None
    """
    if mimetype and mimetype.startswith('image/'):
        ext = mimetype.split('/')[-1]
        return f'cover.{ext}'
    elif picture_data:
        try:
            img = Image.open(io.BytesIO(picture_data))
            return f'cover.{img.format.lower()}'
        except Exception:
            return None
    return None


def create_library_entry(album_list: List[Dict], connection, library_path: Path, debug: int = 0) -> bool:
    """Create a new library entry from uploaded files.
    
    Args:
        album_list: List of albums with file paths
        connection: Database connection
        library_path: Library path
        debug: Debug level
        
    Returns:
        True if successful
    """
    logger.info(f"create_library_entry: Processing {len(album_list)} albums")
    for i, album in enumerate(album_list):
        logger.info(f"Processing album {i}: {album}")
        if not album:
            logger.info(f"Album {i} is empty, skipping")
            continue

        logger.info(f"Album {i} has {len(album)} files")
        oid = new_oid(connection)
        logger.info(f"Generated OID {oid} for album {i}")
        album_data = {}
        track_data = []
        picture_data = None
        track_no = 1

        for file_id in sorted(album.keys()):
            file_path = Path(album[file_id])

            if file_path.suffix.lower() in ['.mp3', '.ogg']:
                # Handle audio files
                try:
                    # Use EasyID3 for MP3 files to support easy tag access
                    if file_path.suffix.lower() == '.mp3':
                        audio = MP3(str(file_path), ID3=EasyID3)
                    else:
                        audio = MutagenFile(str(file_path))

                    if audio is None:
                        continue

                    # Extract album info (using EasyID3 interface)
                    if not album_data.get('album_title') and 'album' in audio:
                        album_data['album_title'] = str(audio['album'][0])
                        album_data['path'] = cleanup_filename(album_data['album_title'])

                    if not album_data.get('album_artist'):
                        if 'albumartist' in audio:
                            album_data['album_artist'] = str(audio['albumartist'][0])
                        elif 'artist' in audio:
                            album_data['album_artist'] = str(audio['artist'][0])

                    if not album_data.get('album_year') and 'date' in audio:
                        album_data['album_year'] = str(audio['date'][0])

                    # Extract cover if present (need raw ID3 for APIC)
                    if not album_data.get('picture_filename') and file_path.suffix.lower() == '.mp3':
                        mp3_raw = MP3(str(file_path))  # Load with raw ID3 for APIC
                        if mp3_raw.tags:
                            for key in mp3_raw.tags.keys():
                                if key.startswith('APIC'):
                                    apic = mp3_raw.tags[key]
                                    picture_data = apic.data
                                    album_data['picture_filename'] = get_cover_filename(
                                        apic.mime, picture_data
                                    )
                                    break

                    # Extract track info (using EasyID3 interface)
                    track_info = {
                        "parent_oid": oid,
                        "album": str(audio.get("album", [""])[0]),
                        "artist": str(audio.get("artist", [""])[0]),
                        "disc": str(audio.get("discnumber", [""])[0]),
                        "duration": int(audio.info.length * 1000) if audio.info else 0,
                        "genre": str(audio.get("genre", [""])[0]),
                        "lyrics": str(audio.get("lyrics", [""])[0]),
                        "title": str(audio.get("title", [""])[0]),
                        "track": int(
                            str(audio.get("tracknumber", [track_no])[0]).split("/")[0]
                        ),
                        "filename": file_path,
                    }

                    if not track_info['title']:
                        track_info['title'] = cleanup_filename(file_path.name)

                    track_data.append(track_info)
                    track_no += 1

                except Exception as e:
                    logger.error(f"Error processing audio file {file_path}: {e}")

            elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff']:
                # Handle image files
                try:
                    with open(file_path, 'rb') as f:
                        picture_data = f.read()
                    album_data['picture_filename'] = cleanup_filename(file_path.name)
                except Exception as e:
                    logger.error(f"Error processing image file {file_path}: {e}")

        # Finalize album data
        album_data['oid'] = oid
        album_data['num_tracks'] = len(track_data)

        logger.info(f"Album {i}: Extracted data - title: {album_data.get('album_title', 'NONE')}, tracks: {len(track_data)}")

        if not album_data.get('album_title'):
            album_data['path'] = 'unknown'
            album_data['album_title'] = 'unknown'

        album_path = make_new_album_dir(album_data['path'], library_path)
        album_data['path'] = str(album_path)

        # Save cover image
        if album_data.get('picture_filename') and picture_data:
            picture_file = album_path / album_data['picture_filename']
            with open(picture_file, 'wb') as f:
                f.write(picture_data)

        # Sort and renumber tracks
        track_data.sort(key=lambda t: (t.get('disc', 0), t.get('track', 0), t.get('filename', '')))
        for i, track in enumerate(track_data, 1):
            track['track'] = i

        # Write to database
        logger.info(f"Album {i}: Writing to database - {album_data['album_title']} with {len(track_data)} tracks")
        write_to_database('gme_library', album_data, connection)
        for track in track_data:
            target_file = album_path / cleanup_filename(track["filename"].name)
            try:
                track["filename"].rename(target_file)
            except Exception as e:
                logger.error(
                    f"Error moving track file {track['filename']} to album directory: {e}"
                )
            logger.info(f"moving track file {track['filename']} to {target_file}")
            track["filename"] = target_file.name
            write_to_database('tracks', track, connection)
        logger.info(f"Album {i}: Successfully written to database")
        shutil.rmtree(Path(album[file_id]).parent, ignore_errors=True)

    logger.info(f"create_library_entry: Completed processing all albums")
    return True


def db_row_to_album(columns: list, row: sqlite3.Row, connection) -> Dict[str, Any]:
    """Convert a database row to an album dictionary.
    
    Args:
        cursor: Database cursor
        row: Database row
        
    Returns:
        Row as dictionary
    """
    album = dict(zip(columns, row))
    
    # Add tracks
    tracks = get_tracks(album, connection)
    for track_no, track in tracks.items():
        album[f'track_{track_no}'] = track
    
    return album


def get_album(oid: int, connection) -> Optional[Dict[str, Any]]:
    """Get album by OID.
    
    Args:
        oid: Album OID
        connection: Database connection
        
    Returns:
        Album dictionary or None
    """
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM gme_library WHERE oid=?', (oid,))
    row = cursor.fetchone()
    
    if not row:
        return None
    
    columns = [desc[0] for desc in cursor.description]
    album = db_row_to_album(columns, row, connection)
    
    return album


def get_album_list(connection, httpd=None, debug: int = 0) -> List[Dict[str, Any]]:
    """Get list of all albums.
    
    Args:
        connection: Database connection
        httpd: Optional HTTP server instance
        debug: Debug level
        
    Returns:
        List of album dictionaries
    """
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM gme_library ORDER BY oid')
    
    columns = [desc[0] for desc in cursor.description]
    albums = []
    
    for row in cursor.fetchall():
        album = db_row_to_album(columns, row, connection)
        albums.append(album)
    
    return albums


def update_album(album_data: Dict[str, Any], connection, debug: int = 0) -> int:
    """Update an existing album.
    
    Args:
        album_data: Album data to update
        connection: Database connection
        debug: Debug level
        
    Returns:
        Album OID
    """
    oid = album_data.get('oid') or album_data.get('uid')
    if not oid:
        raise ValueError("Album OID/UID is required")
    
    # Remove uid if present (use oid)
    album_data.pop('uid', None)
    
    update_data = {k: v for k, v in album_data.items() if k != 'oid'}
    update_table_entry('gme_library', 'oid=?', [oid], update_data, connection)
    
    return oid


def delete_album(uid: int, httpd, connection, library_path: Path) -> int:
    """Delete an album.
    
    Args:
        uid: Album OID
        httpd: HTTP server instance
        connection: Database connection
        library_path: Library path
        
    Returns:
        Deleted album OID
    """
    album = get_album(uid, connection)
    if album:
        # Delete album directory
        album_dir = Path(album['path'])
        remove_album(album_dir)
        
        # Delete from database
        cursor = connection.cursor()
        cursor.execute('DELETE FROM tracks WHERE parent_oid=?', (uid,))
        cursor.execute('DELETE FROM gme_library WHERE oid=?', (uid,))
        connection.commit()
    
    return uid


def cleanup_album(uid: int, httpd, connection, library_path: Path) -> int:
    """Clean up an album directory.
    
    Args:
        uid: Album OID
        httpd: HTTP server instance
        connection: Database connection
        library_path: Library path
        
    Returns:
        Album OID
    """
    album = get_album(uid, connection)
    if album:
        album_dir = Path(album['path'])
        # Clean non-essential files but keep album data
        for item in album_dir.glob('*.yaml'):
            item.unlink()
        for item in album_dir.glob('*.gme'):
            item.unlink()
        audio_dir = album_dir / 'audio'
        if audio_dir.exists():
            import shutil
            shutil.rmtree(audio_dir)
    
    return uid


def replace_cover(uid: int, filename: str, file_data: bytes, 
                 httpd, connection) -> int:
    """Replace album cover image.
    
    Args:
        uid: Album OID
        filename: New cover filename
        file_data: Image data
        httpd: HTTP server instance
        connection: Database connection
        
    Returns:
        Album OID
    """
    album = get_album(uid, connection)
    if not album:
        raise ValueError(f"Album {uid} not found")
    
    album_dir = Path(album['path'])
    
    # Remove old cover if exists
    if album.get('picture_filename'):
        old_cover = album_dir / album['picture_filename']
        if old_cover.exists():
            old_cover.unlink()
    
    # Save new cover
    clean_filename = cleanup_filename(filename)
    cover_file = album_dir / clean_filename
    with open(cover_file, 'wb') as f:
        f.write(file_data)
    
    # Update database
    update_table_entry('gme_library', 'oid=?', [uid], 
                      {'picture_filename': clean_filename}, connection)
    
    return uid


def get_album_online(oid: int, httpd, connection) -> Dict[str, Any]:
    """Get album and make files available online.
    
    Args:
        oid: Album OID
        httpd: HTTP server instance (not used in Flask - routes handle this)
        connection: Database connection
        
    Returns:
        Album dictionary
    """
    album = get_album(oid, connection)
    if not album:
        return {}
    
    # Files are served automatically via Flask routes in ttmp32gme.py
    # /images/<oid>/<filename> for covers
    # /images/<oid_file> for OID codes
    
    return album


def put_file_online(file_path: Path, online_path: str, httpd) -> bool:
    """Make a file available via HTTP server.
    
    Args:
        file_path: Local file path
        online_path: URL path
        httpd: HTTP server instance (not used in Flask - routes handle this)
        
    Returns:
        True if successful
    """
    # Files are served automatically via Flask routes in ttmp32gme.py
    # No dynamic route registration needed - the serve_dynamic_image route
    # handles all /images/* requests
    return True
