"""TtTool handling module for ttmp32gme - creates GME files."""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import shutil

from .build.file_handler import (
    cleanup_filename, get_executable_path, get_oid_cache,
    get_tiptoi_dir
)
from .library_handler import get_album, update_table_entry

logger = logging.getLogger(__name__)


def generate_codes_yaml(yaml_file: Path, connection) -> Path:
    """Generate script codes YAML file.
    
    Args:
        yaml_file: Main YAML file path
        connection: Database connection
        
    Returns:
        Path to codes YAML file
    """
    # Read scripts from main YAML file
    scripts = []
    with open(yaml_file, 'r') as f:
        in_scripts = False
        for line in f:
            line = line.strip()
            if line == 'scripts:':
                in_scripts = True
                continue
            if in_scripts and line.endswith(':'):
                scripts.append(line[:-1])
    
    # Get existing codes from database
    cursor = connection.cursor()
    cursor.execute('SELECT script, code FROM script_codes')
    codes = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Find last used code
    last_code = max(codes.values()) if codes else 0
    
    # Generate codes file
    codes_file = yaml_file.with_suffix('.codes.yaml')
    with open(codes_file, 'w') as f:
        f.write('# This file contains a mapping from script names to oid codes.\n')
        f.write('# This way the existing scripts are always assigned to the\n')
        f.write('# same codes, even if you add further scripts.\n')
        f.write('# \n')
        f.write('# You can copy the contents of this file into the main .yaml file,\n')
        f.write('# if you want to have both together.\n')
        f.write('# \n')
        f.write('# If you delete this file, the next run of "tttool assemble" might\n')
        f.write('# use different codes for your scripts, and you might have to re-\n')
        f.write('# create the images for your product.\n')
        f.write('scriptcodes:\n')
        
        for script in scripts:
            if script in codes:
                f.write(f'  {script}: {codes[script]}\n')
            else:
                last_code += 1
                if last_code > 14999:
                    # Look for free codes
                    used_codes = set(codes.values())
                    last_code = 1001
                    while last_code in used_codes:
                        last_code += 1
                    if last_code > 14999:
                        raise RuntimeError("Cannot create script. All script codes are used up.")
                
                codes[script] = last_code
                cursor.execute('INSERT INTO script_codes VALUES (?, ?)', (script, last_code))
                f.write(f'  {script}: {last_code}\n')
        
        connection.commit()
    
    return codes_file


def convert_tracks(album: Dict[str, Any], yaml_file: Path, config: Dict[str, Any], 
                  connection) -> Path:
    """Convert audio tracks to appropriate format.
    
    Args:
        album: Album dictionary
        yaml_file: YAML file path
        config: Configuration dictionary
        connection: Database connection
        
    Returns:
        Path to media directory
    """
    album_path = Path(album['path'])
    media_path = album_path / 'audio'
    media_path.mkdir(parents=True, exist_ok=True)
    
    tracks = get_sorted_tracks(album)
    
    if config.get('audio_format') == 'ogg':
        # Convert to OGG format using ffmpeg
        ffmpeg_path = get_executable_path('ffmpeg')
        if not ffmpeg_path:
            raise RuntimeError("ffmpeg not found, cannot convert to OGG format")
        
        for i, track_key in enumerate(tracks):
            track = album[track_key]
            source_file = Path(track['filename'])
            target_file = media_path / f'track_{i}.ogg'
            
            cmd = [
                ffmpeg_path, '-y', '-i', str(source_file),
                '-map', '0:a', '-ar', '22050', '-ac', '1', str(target_file)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
    else:
        # Copy MP3 files
        for i, track_key in enumerate(tracks):
            track = album[track_key]
            source_file = Path(track['filename'])
            target_file = media_path / f'track_{i}.mp3'
            shutil.copy(source_file, target_file)
    
    # Generate script content
    play_script = "  play:\n"
    next_script = "  next:\n"
    prev_script = "  prev:\n"
    track_scripts = ""
    
    for i, track_key in enumerate(tracks):
        if i < len(tracks) - 1:
            play_script += f"  - $current=={i}? P({i})"
            play_script += " C\n" if album.get('player_mode') == 'tiptoi' else f" J(t{i+1})\n"
            
            if i < len(tracks) - 2:
                next_script += f"  - $current=={i}? $current:={i+1} P({i+1})"
                next_script += " C\n" if album.get('player_mode') == 'tiptoi' else f" J(t{i+2})\n"
            else:
                next_script += f"  - $current=={i}? $current:={i+1} P({i+1}) C\n"
        else:
            play_script += f"  - $current=={i}? P({i}) C\n"
        
        if i > 0:
            prev_script += f"  - $current=={i}? $current:={i-1} P({i-1})"
            prev_script += " C\n" if album.get('player_mode') == 'tiptoi' else f" J(t{i})\n"
        
        if i < len(tracks) - 1:
            track_scripts += f"  t{i}:\n  - $current:={i} P({i})"
            track_scripts += " C\n" if album.get('player_mode') == 'tiptoi' else f" J(t{i+1})\n"
        else:
            track_scripts += f"  t{i}:\n  - $current:={i} P({i}) C\n"
        
        # Update track script in database
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE tracks SET tt_script=? WHERE parent_oid=? AND track=?',
            (f't{i}', album['oid'], track['track'])
        )
    
    connection.commit()
    
    # Handle general track controls
    last_track = len(tracks) - 1
    max_track_controls = config.get('print_max_track_controls', 24)
    
    if len(tracks) < max_track_controls:
        for i in range(len(tracks), max_track_controls):
            track_scripts += f"  t{i}:\n  - $current:={last_track} P({last_track}) C\n"
    
    # Generate welcome script
    if len(tracks) == 1:
        next_script += f"  - $current:={last_track} P({last_track}) C\n"
        prev_script += f"  - $current:={last_track} P({last_track}) C\n"
        play_script += f"  - $current:={last_track} P({last_track}) C\n"
        welcome = f"welcome: '{last_track}'\n"
    else:
        welcome = (
            "welcome: '0'\n" if album.get('player_mode') == 'tiptoi'
            else f"welcome: {', '.join(map(str, range(len(tracks))))}\n"
        )
    
    # Append to YAML file
    with open(yaml_file, 'a') as f:
        f.write("media-path: audio/track_%s\n")
        f.write("init: $current:=0\n")
        f.write(welcome)
        f.write("scripts:\n")
        f.write(play_script)
        f.write(next_script)
        f.write(prev_script)
        f.write("  stop:\n  - C C\n")
        f.write(track_scripts)
    
    return media_path


def get_tttool_parameters(connection) -> Dict[str, str]:
    """Get tttool parameters from configuration.
    
    Args:
        connection: Database connection
        
    Returns:
        Dictionary of tttool parameters
    """
    cursor = connection.cursor()
    cursor.execute("SELECT param, value FROM config WHERE param LIKE 'tt\\_%' ESCAPE '\\' AND value IS NOT NULL")
    
    parameters = {}
    for param, value in cursor.fetchall():
        parameter_name = param.replace('tt_', '', 1)
        parameters[parameter_name] = value
    
    return parameters


def get_tttool_command(connection) -> List[str]:
    """Build tttool command with parameters.
    
    Args:
        connection: Database connection
        
    Returns:
        Command as list of arguments
    """
    tttool_path = get_executable_path('tttool')
    if not tttool_path:
        raise RuntimeError("tttool not found")
    
    command = [tttool_path]
    parameters = get_tttool_parameters(connection)
    
    for param, value in sorted(parameters.items()):
        command.extend([f'--{param}', value])
    
    return command


def run_tttool(arguments: str, path: Optional[Path], connection) -> bool:
    """Run tttool command.
    
    Args:
        arguments: Command arguments
        path: Working directory
        connection: Database connection
        
    Returns:
        True if successful
    """
    original_dir = Path.cwd()
    
    try:
        if path:
            os.chdir(path)
        
        command = get_tttool_command(connection)
        command.extend(arguments.split())
        
        logger.info(f"Running: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"tttool failed: {e.stderr}")
        return False
    finally:
        os.chdir(original_dir)


def get_sorted_tracks(album: Dict[str, Any]) -> List[str]:
    """Get sorted list of track keys.
    
    Args:
        album: Album dictionary
        
    Returns:
        List of track keys (e.g., ['track_1', 'track_2', ...])
    """
    tracks = [key for key in album.keys() if key.startswith('track_')]
    # Extract numeric part and sort
    tracks.sort(key=lambda x: int(x.split('_')[1]))
    return tracks


def make_gme(oid: int, config: Dict[str, Any], connection) -> int:
    """Create GME file for an album.
    
    Args:
        oid: Album OID
        config: Configuration dictionary
        connection: Database connection
        
    Returns:
        Album OID
    """
    album = get_album(oid, connection)
    if not album:
        raise ValueError(f"Album {oid} not found")
    
    album_path = Path(album['path'])
    album_title = cleanup_filename(album['album_title'])
    yaml_file = album_path / f'{album_title}.yaml'
    
    # Create main YAML file
    with open(yaml_file, 'w') as f:
        f.write('#this file was generated automatically by ttmp32gme\n')
        f.write(f'product-id: {oid}\n')
        f.write('comment: "CHOMPTECH DATA FORMAT CopyRight 2019 Ver0.00.0001"\n')
        f.write(f"gme-lang: {config.get('pen_language', 'GERMAN')}\n")
    
    # Convert tracks and add scripts
    media_path = convert_tracks(album, yaml_file, config, connection)
    
    # Generate codes file
    codes_file = generate_codes_yaml(yaml_file, connection)
    
    # Run tttool to assemble GME
    yaml_basename = yaml_file.name
    if run_tttool(f'assemble {yaml_basename}', album_path, connection):
        gme_filename = yaml_basename.replace('.yaml', '.gme')
        update_table_entry('gme_library', 'oid=?', [oid], 
                          {'gme_file': gme_filename}, connection)
    
    # Cleanup temporary audio directory
    if media_path.exists():
        shutil.rmtree(media_path)
    
    return oid


def create_oids(oids: List[int], size: int, connection) -> List[Path]:
    """Create OID code images.
    
    Args:
        oids: List of OIDs to create
        size: Size in mm
        connection: Database connection
        
    Returns:
        List of OID image file paths
    """
    target_path = get_oid_cache()
    parameters = get_tttool_parameters(connection)
    dpi = parameters.get('dpi', '1200')
    pixel_size = parameters.get('pixel-size', '2')
    
    files = []
    
    for oid in oids:
        oid_file = target_path / f'{oid}-{size}-{dpi}-{pixel_size}.png'
        
        if not oid_file.exists():
            # Create OID image
            command = get_tttool_command(connection)
            command.extend(['--code-dim', str(size), 'oid-code', str(oid)])
            
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=target_path)
                logger.info(result.stdout)
                
                # Move generated file to cache
                generated_file = target_path / f'oid-{oid}.png'
                if generated_file.exists():
                    generated_file.rename(oid_file)
            except subprocess.CalledProcessError as e:
                logger.error(f"Could not create OID file: {e.stderr}")
                raise
        
        files.append(oid_file)
    
    return files


def copy_gme(oid: int, config: Dict[str, Any], connection) -> int:
    """Copy GME file to TipToi device.
    
    Args:
        oid: Album OID
        config: Configuration dictionary
        connection: Database connection
        
    Returns:
        Album OID
    """
    cursor = connection.cursor()
    cursor.execute('SELECT path, gme_file FROM gme_library WHERE oid=?', (oid,))
    row = cursor.fetchone()
    
    if not row:
        raise ValueError(f"Album {oid} not found")
    
    path, gme_file = row
    
    if not gme_file:
        # Create GME if it doesn't exist
        make_gme(oid, config, connection)
        cursor.execute('SELECT path, gme_file FROM gme_library WHERE oid=?', (oid,))
        path, gme_file = cursor.fetchone()
    
    tiptoi_dir = get_tiptoi_dir()
    if not tiptoi_dir:
        raise RuntimeError("TipToi device not found")
    
    gme_path = Path(path) / gme_file
    target_path = tiptoi_dir / gme_file
    
    logger.info(f"Copying {gme_file} to {tiptoi_dir}")
    shutil.copy(gme_path, target_path)
    logger.info("done.")
    
    return oid


def delete_gme_tiptoi(uid: int, connection) -> int:
    """Delete GME file from TipToi device.
    
    Args:
        uid: Album OID
        connection: Database connection
        
    Returns:
        Album OID
    """
    cursor = connection.cursor()
    cursor.execute('SELECT gme_file FROM gme_library WHERE oid=?', (uid,))
    row = cursor.fetchone()
    
    if not row or not row[0]:
        return uid
    
    gme_file = row[0]
    tiptoi_dir = get_tiptoi_dir()
    
    if tiptoi_dir:
        gme_path = tiptoi_dir / gme_file
        if gme_path.exists():
            gme_path.unlink()
            logger.info(f"Deleted {gme_file} from TipToi")
    
    return uid
