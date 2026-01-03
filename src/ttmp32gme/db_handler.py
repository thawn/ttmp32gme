import io
import logging
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from packaging.version import Version
from PIL import Image
from pydantic import BaseModel, Field, field_validator

from ttmp32gme.build.file_handler import (
    cleanup_filename,
    make_new_album_dir,
    remove_album,
)

logger = logging.getLogger(__name__)


# Pydantic Models for Input Validation


# Reusable field validators to avoid code duplication
def convert_str_to_int(v):
    """Convert string to integer.

    Args:
        v: Value to convert (can be str, int, or None)

    Returns:
        Integer value or None

    Raises:
        ValueError: If conversion fails
    """
    if v is not None and isinstance(v, str):
        try:
            return int(v)
        except ValueError:
            raise ValueError(f"Invalid integer value: {v}")
    return v


def trim_optional_str(v):
    """Trim optional string fields.

    Args:
        v: String value or None

    Returns:
        Trimmed string or None
    """
    if v and isinstance(v, str):
        return v.strip()
    return v


def validate_non_empty_str(v, field_name: str = "field"):
    """Validate and trim non-empty string fields.

    Args:
        v: String value to validate
        field_name: Name of the field (for error messages)

    Returns:
        Trimmed string

    Raises:
        ValueError: If string is empty or whitespace only
        TypeError: If value is not a string
    """
    if not isinstance(v, str):
        raise TypeError(f"{field_name} must be a string")
    stripped = v.strip()
    if not stripped:
        raise ValueError(f"{field_name} cannot be empty")
    return stripped


class AlbumUpdateModel(BaseModel):
    """Validates album update data from frontend."""

    oid: Optional[int] = Field(None, description="Album OID")
    uid: Optional[int] = Field(None, description="Album UID (alias for OID)")
    old_oid: Optional[int] = Field(None, description="Previous OID if changing")
    album_title: Optional[str] = Field(None, max_length=255)
    album_artist: Optional[str] = Field(None, max_length=255)
    num_tracks: Optional[int] = Field(None, ge=0, le=999)
    player_mode: Optional[str] = Field(None, pattern="^(music|tiptoi)$")
    cover: Optional[str] = Field(None, description="Cover image path")

    # Allow dynamic track fields (track1_title, track2_title, etc.)
    model_config = {"extra": "allow"}

    @field_validator("oid", "uid", mode="before")
    @classmethod
    def convert_to_int(cls, v):
        """Convert string OIDs to integers."""
        return convert_str_to_int(v)


class ConfigUpdateModel(BaseModel):
    """Validates configuration update data from frontend."""

    host: Optional[str] = Field(None, pattern="^[a-zA-Z0-9.-]+$")
    port: Optional[int] = Field(None, ge=1, le=65535)
    open_browser: Optional[bool] = None
    audio_format: Optional[str] = Field(None, pattern="^(mp3|ogg)$")
    pen_language: Optional[str] = Field(None, max_length=50)
    library_path: Optional[str] = Field(None, max_length=500)

    # Allow other config fields
    model_config = {"extra": "allow"}


class LibraryActionModel(BaseModel):
    """Validates library action data (delete, cleanup, make_gme, etc.)."""

    uid: int = Field(..., description="Album OID/UID (required)")

    # Optional fields for various actions
    tiptoi_dir: Optional[str] = None

    # Allow other action-specific fields
    model_config = {"extra": "allow"}

    @field_validator("uid", mode="before")
    @classmethod
    def convert_uid_to_int(cls, v):
        """Convert string UID to integer."""
        return convert_str_to_int(v)


class AlbumMetadataModel(BaseModel):
    """Validates album-level metadata extracted from audio files."""

    oid: int = Field(..., description="Album OID", ge=0, le=1000)
    album_title: str = Field(..., max_length=255, description="Album title")
    album_artist: Optional[str] = Field(
        None, max_length=255, description="Album artist"
    )
    album_year: Optional[str] = Field(None, max_length=10, description="Album year")
    num_tracks: int = Field(..., ge=0, le=999, description="Number of tracks")
    picture_filename: Optional[str] = Field(
        None, max_length=255, description="Cover image filename"
    )
    path: str = Field(..., max_length=500, description="Album directory path")

    @field_validator("album_title", mode="before")
    @classmethod
    def validate_album_title(cls, v):
        """Ensure album title is not empty."""
        return validate_non_empty_str(v, "Album title")

    @field_validator("album_artist", mode="before")
    @classmethod
    def validate_album_artist(cls, v):
        """Trim album artist."""
        return trim_optional_str(v)

    @field_validator("album_year", mode="before")
    @classmethod
    def validate_year(cls, v):
        """Validate year format."""
        if v:
            v = str(v).strip()
            # Accept various year formats (YYYY, YYYY-MM-DD, etc.)
            if len(v) >= 4:
                return v[:10]  # Limit to 10 chars
        return v


class TrackMetadataModel(BaseModel):
    """Validates track-level metadata extracted from audio files."""

    parent_oid: int = Field(..., description="Parent album OID", ge=0, le=1000)
    album: Optional[str] = Field(None, max_length=255, description="Track album name")
    artist: Optional[str] = Field(None, max_length=255, description="Track artist")
    disc: Optional[str] = Field(None, max_length=10, description="Disc number")
    duration: int = Field(..., ge=0, description="Track duration in milliseconds")
    genre: Optional[str] = Field(None, max_length=100, description="Track genre")
    lyrics: Optional[str] = Field(None, description="Track lyrics")
    title: str = Field(..., max_length=255, description="Track title")
    track: int = Field(..., ge=1, le=999, description="Track number")
    filename: str = Field(..., max_length=255, description="Track filename")

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v):
        """Ensure track title is not empty."""
        return validate_non_empty_str(v, "Track title")

    @field_validator("album", "artist", "genre", mode="before")
    @classmethod
    def trim_string_fields(cls, v):
        """Trim string fields."""
        return trim_optional_str(v)


class DBHandler:
    # Valid table names that can be used in queries
    VALID_TABLES = {"config", "gme_library", "script_codes", "tracks"}

    # Valid column names for each table (populated dynamically)
    _valid_columns: Dict[str, set] = {}

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._gme_library_columns: Optional[List[str]] = None

    @property
    def gme_library_columns(self) -> List[str]:
        if self._gme_library_columns is None:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA table_info(gme_library);")
            self._gme_library_columns = [row[1] for row in cursor.fetchall()]
            cursor.close()
        return self._gme_library_columns

    def connect(self):
        if not self.conn:
            # check_same_thread=False allows connection to be used across Flask request threads
            # This is safe because SQLite handles its own locking
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            # Populate valid columns cache
            self._populate_valid_columns()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize(self):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS config (
            param TEXT NOT NULL UNIQUE,
            value TEXT,
            PRIMARY KEY(param)
        );
        """
        )
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS gme_library (
            oid INTEGER NOT NULL UNIQUE,
            album_title TEXT,
            album_artist TEXT,
            album_year INTEGER,
            num_tracks INTEGER NOT NULL DEFAULT 0,
            picture_filename TEXT,
            gme_file TEXT,
            path TEXT,
            player_mode TEXT DEFAULT 'music',
            PRIMARY KEY(`oid`)
        );
        """
        )
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS script_codes (
            script TEXT NOT NULL UNIQUE,
            code INTEGER NOT NULL,
            PRIMARY KEY(script)
        );
        """
        )
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS tracks (
            parent_oid	INTEGER NOT NULL,
            album	TEXT,
            artist	TEXT,
            disc	INTEGER,
            duration	INTEGER,
            genre	TEXT,
            lyrics	TEXT,
            title	TEXT,
            track	INTEGER,
            filename	TEXT,
            tt_script	TEXT
        );
        """
        )
        cursor.executescript(
            """
            INSERT OR IGNORE INTO config VALUES('host','127.0.0.1');
            INSERT OR IGNORE INTO config VALUES('port','10020');
            INSERT OR IGNORE INTO config VALUES('version','2.0.0');
            INSERT OR IGNORE INTO config VALUES('open_browser','TRUE');
            INSERT OR IGNORE INTO config VALUES('tt_dpi','1200');
            INSERT OR IGNORE INTO config VALUES('tt_code-dim',NULL);
            INSERT OR IGNORE INTO config VALUES('tt_pixel-size','2');
            INSERT OR IGNORE INTO config VALUES('tt_transscript',NULL);
            INSERT OR IGNORE INTO config VALUES('audio_format','mp3');
            INSERT OR IGNORE INTO config VALUES('print_max_track_controls','24');
            INSERT OR IGNORE INTO config VALUES('print_page_size','A4');
            INSERT OR IGNORE INTO config VALUES('print_page_margin','0.5in');
            INSERT OR IGNORE INTO config VALUES('print_show_cover','TRUE');
            INSERT OR IGNORE INTO config VALUES('print_show_album_info','TRUE');
            INSERT OR IGNORE INTO config VALUES('print_show_album_controls','TRUE');
            INSERT OR IGNORE INTO config VALUES('print_show_tracks','TRUE');
            INSERT OR IGNORE INTO config VALUES('print_show_general_controls','FALSE');
            INSERT OR IGNORE INTO config VALUES('print_num_cols','1');
            INSERT OR IGNORE INTO config VALUES('print_tile_size',NULL);
            INSERT OR IGNORE INTO config VALUES('print_preset','list');
            INSERT OR IGNORE INTO config VALUES('pen_language','GERMAN');
            INSERT OR IGNORE INTO config VALUES('library_path','');
        """
        )
        cursor.executescript(
            """
            INSERT OR IGNORE INTO script_codes VALUES('next',3944);
            INSERT OR IGNORE INTO script_codes VALUES('prev',3945);
            INSERT OR IGNORE INTO script_codes VALUES('stop',3946);
            INSERT OR IGNORE INTO script_codes VALUES('play',3947);
            INSERT OR IGNORE INTO script_codes VALUES('t0',2663);
            INSERT OR IGNORE INTO script_codes VALUES('t1',2664);
            INSERT OR IGNORE INTO script_codes VALUES('t2',2665);
            INSERT OR IGNORE INTO script_codes VALUES('t3',2666);
            INSERT OR IGNORE INTO script_codes VALUES('t4',2667);
            INSERT OR IGNORE INTO script_codes VALUES('t5',2047);
            INSERT OR IGNORE INTO script_codes VALUES('t6',2048);
            INSERT OR IGNORE INTO script_codes VALUES('t7',2049);
            INSERT OR IGNORE INTO script_codes VALUES('t8',2050);
            INSERT OR IGNORE INTO script_codes VALUES('t9',2051);
            INSERT OR IGNORE INTO script_codes VALUES('t10',2052);
            INSERT OR IGNORE INTO script_codes VALUES('t11',2053);
            INSERT OR IGNORE INTO script_codes VALUES('t12',2054);
            INSERT OR IGNORE INTO script_codes VALUES('t13',2055);
            INSERT OR IGNORE INTO script_codes VALUES('t14',2056);
            INSERT OR IGNORE INTO script_codes VALUES('t15',2057);
            INSERT OR IGNORE INTO script_codes VALUES('t16',2058);
            INSERT OR IGNORE INTO script_codes VALUES('t17',2059);
            INSERT OR IGNORE INTO script_codes VALUES('t18',2060);
            INSERT OR IGNORE INTO script_codes VALUES('t19',2061);
            INSERT OR IGNORE INTO script_codes VALUES('t20',2062);
            INSERT OR IGNORE INTO script_codes VALUES('t21',2063);
            INSERT OR IGNORE INTO script_codes VALUES('t22',2064);
            INSERT OR IGNORE INTO script_codes VALUES('t23',2065);
    """
        )
        self.commit()
        # Refresh column cache after table creation
        self._populate_valid_columns()

    def execute(self, query: str, params: Tuple[Any, ...] = ()) -> sqlite3.Cursor:
        self.connect()
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur

    def fetchall(self, query: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
        cur = self.execute(query, params)
        results = cur.fetchall()
        cur.close()
        return results

    def fetchone(
        self, query: str, params: Tuple[Any, ...] = ()
    ) -> Optional[sqlite3.Row]:
        cur = self.execute(query, params)
        result = cur.fetchone()
        cur.close()
        return result

    def commit(self):
        if self.conn:
            self.conn.commit()

    def _populate_valid_columns(self):
        """Populate the cache of valid column names for each table."""
        for table in self.VALID_TABLES:
            try:
                cursor = self.conn.cursor()
                # Safe to use f-string here: table is from VALID_TABLES whitelist
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [row[1] for row in cursor.fetchall()]
                self._valid_columns[table] = set(columns)
                cursor.close()
            except sqlite3.OperationalError:
                # Table might not exist yet (during initialization)
                self._valid_columns[table] = set()

    def _validate_table_name(self, table: str) -> None:
        """Validate that a table name is allowed.

        Args:
            table: Table name to validate

        Raises:
            ValueError: If table name is not in the whitelist
        """
        if table not in self.VALID_TABLES:
            raise ValueError(
                f"Invalid table name: {table}. "
                f"Allowed tables: {', '.join(sorted(self.VALID_TABLES))}"
            )

    def _validate_field_names(self, table: str, fields: List[str]) -> None:
        """Validate that field names are allowed for the given table.

        Args:
            table: Table name
            fields: List of field names to validate

        Raises:
            ValueError: If any field name is not valid for the table
        """
        valid_columns = self._valid_columns.get(table, set())
        if not valid_columns:
            # Re-populate in case table was just created
            self._populate_valid_columns()
            valid_columns = self._valid_columns.get(table, set())

        invalid_fields = [f for f in fields if f not in valid_columns]
        if invalid_fields:
            raise ValueError(
                f"Invalid field names for table {table}: {', '.join(invalid_fields)}. "
                f"Allowed fields: {', '.join(sorted(valid_columns))}"
            )

    def write_to_database(self, table: str, data: Dict[str, Any]):
        """Write data to database table.

        Args:
            table: Table name
            data: Data dictionary
            connection: Database connection

        Raises:
            ValueError: If table name or field names are invalid
        """
        self._validate_table_name(table)
        fields = sorted(data.keys())
        self._validate_field_names(table, fields)

        values = [data[field] for field in fields]
        placeholders = ", ".join("?" * len(fields))
        query = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})"

        self.execute(query, values)
        self.commit()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_config(self) -> Dict[str, str]:
        """Get configuration parameters.

        Returns:
            Configuration dictionary
        """
        query = "SELECT param, value FROM config"
        config = {}
        for row in self.fetchall(query):
            config[row["param"]] = row["value"]
        return config

    def get_config_value(self, param: str) -> Optional[str]:
        """Get a specific configuration value.

        Args:
            param: Configuration parameter name

        Returns:
            Configuration value or None
        """
        query = "SELECT value FROM config WHERE param=?"
        params = (param,)
        row = self.fetchone(query, params)
        return row["value"] if row else None

    def oid_exist(self, oid: int) -> bool:
        """Check if an OID exists in the database.

        Args:
            oid: OID to check

        Returns:
            True if OID exists
        """
        query = "SELECT oid FROM gme_library WHERE oid = ?"
        params = (oid,)
        return self.fetchone(query, params) is not None

    def new_oid(self) -> int:
        """Generate a new unique OID.

        Args:

        Returns:
            New OID
        """
        query = "SELECT oid FROM gme_library ORDER BY oid DESC"
        old_oids = [row[0] for row in self.fetchall(query)]

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
                raise RuntimeError(
                    "Could not find a free OID. Try deleting OIDs from your library."
                )

        return new_oid

    def get_tracks(self, album: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
        """Get all tracks for an album.

        Args:
            album: Album dictionary

        Returns:
            Dictionary of tracks indexed by track number
        """
        query = "SELECT * FROM tracks WHERE parent_oid=? ORDER BY track"
        params = (album["oid"],)
        cursor = self.execute(query, params)

        columns = [desc[0] for desc in cursor.description]
        tracks = {}

        for row in cursor.fetchall():
            track = dict(zip(columns, row))
            tracks[track["track"]] = track

        return tracks

    def update_table_entry(
        self, table: str, keyname: str, search_keys: List, data: Dict[str, Any]
    ) -> bool:
        """Update a table entry.

        Args:
            table: Table name
            keyname: Key column name with condition (e.g., 'oid=?')
            search_keys: Values for the key condition
            data: Data to update

        Returns:
            True if successful

        Raises:
            ValueError: If table name or field names are invalid
        """
        self._validate_table_name(table)
        fields = sorted(data.keys())
        self._validate_field_names(table, fields)

        values = [data[field] for field in fields]
        set_clause = ", ".join(f"{field}=?" for field in fields)
        query = f"UPDATE {table} SET {set_clause} WHERE {keyname}"

        self.execute(query, values + search_keys)
        self.commit()
        return True

    def _extract_audio_metadata(
        self, file_path: Path, oid: int, track_no: int
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[bytes]]:
        """Extract metadata from audio file.

        Args:
            file_path: Path to audio file
            oid: Album OID
            track_no: Default track number

        Returns:
            Tuple of (album_data, track_info, picture_data) or (None, None, None) on error
        """
        try:
            # Use EasyID3 for MP3 files to support easy tag access
            if file_path.suffix.lower() == ".mp3":
                audio = MP3(str(file_path), ID3=EasyID3)
            else:
                audio = MutagenFile(str(file_path))

            if audio is None:
                return None, None, None

            # Extract album info (using EasyID3 interface)
            album_data = {}
            if "album" in audio:
                album_data["album_title"] = str(audio["album"][0])
                album_data["path"] = cleanup_filename(album_data["album_title"])

            if "albumartist" in audio:
                album_data["album_artist"] = str(audio["albumartist"][0])
            elif "artist" in audio:
                album_data["album_artist"] = str(audio["artist"][0])

            if "date" in audio:
                album_data["album_year"] = str(audio["date"][0])

            # Extract cover if present (need raw ID3 for APIC)
            picture_data = None
            if file_path.suffix.lower() == ".mp3":
                mp3_raw = MP3(str(file_path))  # Load with raw ID3 for APIC
                if mp3_raw.tags:
                    for key in mp3_raw.tags.keys():
                        if key.startswith("APIC"):
                            apic = mp3_raw.tags[key]
                            picture_data = apic.data
                            album_data["picture_filename"] = get_cover_filename(
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

            if not track_info["title"]:
                track_info["title"] = cleanup_filename(file_path.name)

            return album_data, track_info, picture_data

        except Exception as e:
            logger.error(f"Error processing audio file {file_path}: {e}")
            return None, None, None

    def _process_cover_image(
        self, file_path: Path
    ) -> Tuple[Optional[str], Optional[bytes]]:
        """Process cover image file.

        Args:
            file_path: Path to image file

        Returns:
            Tuple of (filename, image_data) or (None, None) on error
        """
        try:
            with open(file_path, "rb") as f:
                picture_data = f.read()
            picture_filename = cleanup_filename(file_path.name)
            return picture_filename, picture_data
        except Exception as e:
            logger.error(f"Error processing image file {file_path}: {e}")
            return None, None

    def _finalize_album_data(
        self, album_data: Dict[str, Any], oid: int, num_tracks: int
    ) -> Dict[str, Any]:
        """Finalize album data with defaults and validation.

        Args:
            album_data: Raw album data
            oid: Album OID
            num_tracks: Number of tracks

        Returns:
            Validated album data
        """
        album_data["oid"] = oid
        album_data["num_tracks"] = num_tracks

        if not album_data.get("album_title"):
            album_data["path"] = "unknown"
            album_data["album_title"] = "unknown"

        # Validate with Pydantic model
        validated = AlbumMetadataModel(**album_data)
        return validated.model_dump()

    def _sort_and_renumber_tracks(
        self, track_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Sort tracks and renumber them sequentially.

        Args:
            track_data: List of track dictionaries

        Returns:
            Sorted and renumbered track list
        """
        track_data.sort(
            key=lambda t: (
                t.get("disc", 0),
                t.get("track", 0),
                t.get("filename", ""),
            )
        )
        for i, track in enumerate(track_data, 1):
            track["track"] = i
        return track_data

    def _save_album_to_database(
        self,
        album_data: Dict[str, Any],
        track_data: List[Dict[str, Any]],
        picture_data: Optional[bytes],
        album_path: Path,
    ) -> None:
        """Save album and tracks to database with validation.

        Args:
            album_data: Validated album data
            track_data: List of track dictionaries
            picture_data: Cover image data (if any)
            album_path: Album directory path

        Raises:
            ValidationError: If data validation fails
        """
        # Save cover image
        if album_data.get("picture_filename") and picture_data:
            picture_file = album_path / album_data["picture_filename"]
            with open(picture_file, "wb") as f:
                f.write(picture_data)

        # Write album to database (already validated)
        self.write_to_database("gme_library", album_data)

        # Validate and write tracks to database
        for track in track_data:
            # First, validate all metadata except filename (which is still a Path)
            temp_track = track.copy()
            source_file = temp_track.pop("filename")  # Remove Path object
            temp_track["filename"] = (
                source_file.name
            )  # Use just the name for validation

            # Validate track metadata
            validated_track = TrackMetadataModel(**temp_track)

            # Now move file to album directory
            target_file = album_path / cleanup_filename(source_file.name)
            try:
                source_file.rename(target_file)
                logger.info(f"moved track file {source_file} to {target_file}")
                final_filename = target_file.name
            except Exception as e:
                logger.error(
                    f"Error moving track file {source_file} to album directory: {e}"
                )
                # If move fails, use just the source filename
                final_filename = source_file.name

            # Update filename in validated data and write to database
            validated_data = validated_track.model_dump()
            validated_data["filename"] = final_filename
            self.write_to_database("tracks", validated_data)

    def create_library_entry(self, album_list: List[Dict], library_path: Path) -> bool:
        """Create a new library entry from uploaded files.

        Args:
            album_list: List of albums with file paths
            library_path: Library path

        Returns:
            True if successful
        """
        logger.info(f"create_library_entry: Processing {len(album_list)} albums")
        for album_idx, album in enumerate(album_list):
            logger.info(f"Processing album {album_idx}: {album}")
            if not album:
                logger.info(f"Album {album_idx} is empty, skipping")
                continue

            logger.info(f"Album {album_idx} has {len(album)} files")
            oid = self.new_oid()
            logger.info(f"Generated OID {oid} for album {album_idx}")

            album_data = {}
            track_data = []
            picture_data = None
            track_no = 1

            # Process all files in the album
            # Sort by filename (not UUID) for predictable track order
            sorted_file_ids = sorted(
                album.keys(), key=lambda fid: Path(album[fid]).name
            )
            for file_id in sorted_file_ids:
                file_path = Path(album[file_id])

                if file_path.suffix.lower() in [".mp3", ".ogg"]:
                    # Handle audio files using helper method
                    audio_album_data, track_info, audio_picture_data = (
                        self._extract_audio_metadata(file_path, oid, track_no)
                    )

                    if track_info:
                        # Merge album data (first file wins for album-level metadata)
                        if not album_data.get("album_title") and audio_album_data.get(
                            "album_title"
                        ):
                            album_data["album_title"] = audio_album_data["album_title"]
                            album_data["path"] = audio_album_data["path"]
                        if not album_data.get("album_artist") and audio_album_data.get(
                            "album_artist"
                        ):
                            album_data["album_artist"] = audio_album_data[
                                "album_artist"
                            ]
                        if not album_data.get("album_year") and audio_album_data.get(
                            "album_year"
                        ):
                            album_data["album_year"] = audio_album_data["album_year"]
                        if not album_data.get(
                            "picture_filename"
                        ) and audio_album_data.get("picture_filename"):
                            album_data["picture_filename"] = audio_album_data[
                                "picture_filename"
                            ]
                            picture_data = audio_picture_data

                        track_data.append(track_info)
                        track_no += 1

                elif file_path.suffix.lower() in [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".gif",
                    ".tif",
                    ".tiff",
                ]:
                    # Handle image files using helper method
                    # Note: Separate image files take precedence over embedded covers
                    pic_filename, pic_data = self._process_cover_image(file_path)
                    if pic_filename:
                        album_data["picture_filename"] = pic_filename
                        picture_data = pic_data

            logger.info(
                f"Album {album_idx}: Extracted data - title: {album_data.get('album_title', 'NONE')}, tracks: {len(track_data)}"
            )

            # Finalize and validate album data using helper method
            album_data = self._finalize_album_data(album_data, oid, len(track_data))

            # Create album directory
            album_path = make_new_album_dir(album_data["path"], library_path)
            album_data["path"] = str(album_path)

            # Sort and renumber tracks using helper method
            track_data = self._sort_and_renumber_tracks(track_data)

            # Save to database with validation using helper method
            logger.info(
                f"Album {album_idx}: Writing to database - {album_data['album_title']} with {len(track_data)} tracks"
            )
            self._save_album_to_database(
                album_data, track_data, picture_data, album_path
            )

            logger.info("Album %s: Successfully written to database", album_idx)
            shutil.rmtree(Path(album[file_id]).parent, ignore_errors=True)

        logger.info("create_library_entry: Completed processing all albums")
        return True

    def db_row_to_album(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a complete album dictionary including track info.

        Args:
            columns: list of column names
            row: Database row

        Returns:
            Album including tracks as dictionary
        """
        album = dict(zip(self.gme_library_columns, row))

        # Add tracks
        tracks = self.get_tracks(album)
        for track_no, track in tracks.items():
            album[f"track_{track_no}"] = track

        return album

    def get_album(self, oid: int) -> Optional[Dict[str, Any]]:
        """Get album by OID.

        Args:
            oid: Album OID

        Returns:
            Album dictionary or None
        """
        query = "SELECT * FROM gme_library WHERE oid=?"
        params = (oid,)
        row = self.fetchone(query, params)

        if not row:
            return None

        album = self.db_row_to_album(row)

        return album

    def get_album_list(self) -> List[Dict[str, Any]]:
        """Get list of all albums.

        Args:

        Returns:
            List of album dictionaries
        """
        query = "SELECT * FROM gme_library ORDER BY oid"

        albums = []

        for row in self.fetchall(query):
            album = self.db_row_to_album(row)
            albums.append(album)

        return albums

    def get_gme_file_info(self, oid: int) -> Optional[Tuple[str, str]]:
        """Get GME file path and filename for an album.

        Args:
            oid: Album OID

        Returns:
            Tuple of (album_path, gme_filename) or None if album not found
        """
        query = "SELECT path, gme_file FROM gme_library WHERE oid=?"
        params = (oid,)
        row = self.fetchone(query, params)

        if not row:
            return None

        return (row[0], row[1])

    def update_tracks(
        self, tracks: List[Dict[str, Any]], parent_oid: int, new_parent_oid: int
    ) -> bool:
        """Update tracks in the database.

        Args:
            tracks: List of track dictionaries
            parent_oid: Original parent OID
            new_parent_oid: New parent OID

        Returns:
            True if successful
        """

        complete_track_data = self.get_tracks({"oid": parent_oid})
        self.delete_album_tracks(parent_oid)  # Clear existing tracks to avoid conflicts
        for track in tracks:
            track_data = complete_track_data.get(int(track.pop("old_track")), {})
            track["parent_oid"] = new_parent_oid
            track_data.update(track)
            self.write_to_database("tracks", track_data)

        return True

    def update_album(self, album_data: Dict[str, Any]) -> int:
        """Update an existing album.

        Args:
            album_data: Album data to update

        Returns:
            Album OID
        """
        oid = album_data.get("oid") or album_data.get("uid")
        if not oid:
            raise ValueError("Album OID/UID is required")

        # Remove uid if present (use oid)
        album_data.pop("uid", None)

        # store old_uid and use it for searching the entry to update
        old_oid = album_data.pop("old_oid", None)
        if old_oid is None:
            old_oid = oid
        elif old_oid != oid:
            logger.info(
                f"OID has changed from {old_oid} to {oid}, need to update the key"
            )
            if self.oid_exist(oid):
                raise ValueError(
                    f"Cannot change OID to {oid}, it already exists, please choose another OID."
                )

        tracks, album_data = extract_tracks_from_album(album_data)

        self.update_table_entry("gme_library", "oid=?", [old_oid], album_data)
        self.update_tracks(tracks, old_oid, oid)

        return oid

    def delete_album(self, uid: int) -> int:
        """Delete an album.

        Args:
            uid: Album OID

        Returns:
            Deleted album OID
        """
        album = self.get_album(uid)
        if album:
            # Delete album directory
            album_dir = Path(album["path"])
            remove_album(album_dir)

            # Delete from database
            self.execute("DELETE FROM tracks WHERE parent_oid=?", (uid,))
            self.execute("DELETE FROM gme_library WHERE oid=?", (uid,))
            self.commit()

        return uid

    def delete_album_tracks(self, oid: int) -> int:
        """Delete all tracks of an album.

        Args:
            oid: Album OID

        Returns:
            Album OID
        """
        self.execute("DELETE FROM tracks WHERE parent_oid=?", (oid,))
        self.commit()
        return oid

    def cleanup_album(self, uid: int) -> int:
        """Clean up an album directory.

        Args:
            uid: Album OID

        Returns:
            Album OID
        """
        album = self.get_album(uid)
        if album:
            album_dir = Path(album["path"])
            # Clean non-essential files but keep album data
            for item in album_dir.glob("*.yaml"):
                item.unlink()
            for item in album_dir.glob("*.gme"):
                item.unlink()
            audio_dir = album_dir / "audio"
            if audio_dir.exists():
                import shutil

                shutil.rmtree(audio_dir)

            # Update database to set gme_file to NULL since GME files were deleted
            self.update_table_entry("gme_library", "oid=?", [uid], {"gme_file": None})

        return uid

    def replace_cover(self, uid: int, filename: str, file_data: bytes) -> int:
        """Replace album cover image.

        Args:
            uid: Album OID
            filename: New cover filename
            file_data: Image data

        Returns:
            Album OID
        """
        album = self.get_album(uid)
        if not album:
            raise ValueError(f"Album {uid} not found")

        album_dir = Path(album["path"])

        # Remove old cover if exists
        if album.get("picture_filename"):
            old_cover = album_dir / album["picture_filename"]
            if old_cover.exists():
                old_cover.unlink()

        # Save new cover
        clean_filename = cleanup_filename(filename)
        cover_file = album_dir / clean_filename
        with open(cover_file, "wb") as f:
            f.write(file_data)

        # Update database
        self.update_table_entry(
            "gme_library", "oid=?", [uid], {"picture_filename": clean_filename}
        )

        return uid

    def change_library_path(self, old_path: str, new_path: Path) -> bool:
        """Change the library path in the configuration.

        Args:
            old_path: Current library path
            new_path: New library path

        Returns:
            True if successful
        """
        import re

        cursor = self.execute("SELECT oid, path FROM gme_library")
        rows = cursor.fetchall()
        try:
            for oid, old_path in rows:
                updated_path = re.sub(
                    re.escape(old_path), str(new_path.absolute()), old_path
                )
                cursor.execute(
                    "UPDATE gme_library SET path=? WHERE oid=?", (updated_path, oid)
                )
            self.commit()
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Error updating library paths: {e}")
        return True

    def _fix_text_encoding(
        self, table: str, rowid_col: str, text_columns: List[str]
    ) -> int:
        """Fix text encoding issues in a database table.

        This method fixes text data that was stored with incorrect encoding (e.g., from legacy Perl code)
        by reading it as raw bytes and re-encoding as UTF-8.

        Args:
            table: Table name to fix
            rowid_col: Name of the row identifier column (e.g., 'oid', 'rowid')
            text_columns: List of text column names to fix

        Returns:
            Number of rows fixed
        """
        # Temporarily disable text_factory to read raw bytes
        old_text_factory = self.conn.text_factory
        self.conn.text_factory = bytes

        fixed_count = 0

        try:
            # Get all rows with their identifiers
            cursor = self.conn.cursor()

            # Build query to select rowid and text columns
            if rowid_col == "rowid":
                select_cols = f"rowid, {', '.join(text_columns)}"
            else:
                select_cols = f"{rowid_col}, {', '.join(text_columns)}"

            cursor.execute(f"SELECT {select_cols} FROM {table}")
            rows = cursor.fetchall()

            for row in rows:
                row_id = row[0]
                needs_fix = False
                fixed_values = {}

                # Check each text column
                for i, col_name in enumerate(text_columns, start=1):
                    value = row[i]

                    if value is None:
                        continue

                    # Try to decode as UTF-8
                    try:
                        if isinstance(value, bytes):
                            # Try UTF-8 first
                            text = value.decode("utf-8")
                        else:
                            # Already text, no fix needed
                            continue
                    except UnicodeDecodeError:
                        # Failed UTF-8, try Latin-1 (which accepts all bytes)
                        try:
                            if isinstance(value, bytes):
                                text = value.decode("latin-1")
                                fixed_values[col_name] = text
                                needs_fix = True
                                logger.info(
                                    f"Fixed encoding for {table}.{col_name} "
                                    f"(row {row_id}): {value[:50]}... -> {text[:50]}..."
                                )
                        except Exception as e:
                            logger.warning(
                                f"Could not fix encoding for {table}.{col_name} "
                                f"(row {row_id}): {e}"
                            )

                # Update the row if any column needed fixing
                if needs_fix:
                    # Restore normal text_factory for the update
                    self.conn.text_factory = str

                    set_clause = ", ".join(f"{col}=?" for col in fixed_values.keys())
                    values = list(fixed_values.values()) + [row_id]

                    update_sql = f"UPDATE {table} SET {set_clause} WHERE {rowid_col}=?"
                    cursor.execute(update_sql, values)
                    fixed_count += 1

                    # Switch back to bytes for reading next row
                    self.conn.text_factory = bytes

            cursor.close()

        finally:
            # Restore original text_factory
            self.conn.text_factory = old_text_factory

        return fixed_count

    def update_db(self) -> bool:
        """Update database schema to latest version.

        Args:

        Returns:
            True if update successful
        """
        updates = {
            "0.1.0": ["UPDATE config SET value='0.1.0' WHERE param='version';"],
            "0.2.0": ["UPDATE config SET value='0.2.0' WHERE param='version';"],
            "0.2.1": ["UPDATE config SET value='0.2.1' WHERE param='version';"],
            "0.2.3": [
                "UPDATE config SET value='0.2.3' WHERE param='version';",
                "INSERT INTO config (param, value) VALUES ('pen_language', 'GERMAN');",
            ],
            "0.3.0": [
                "UPDATE config SET value='0.3.0' WHERE param='version';",
                "INSERT INTO config (param, value) VALUES ('library_path', '');",
                "INSERT INTO config (param, value) VALUES ('player_mode', 'music');",
            ],
            "0.3.1": [
                "UPDATE config SET value='0.3.1' WHERE param='version';",
                "DELETE FROM config WHERE param='player_mode';",
                "ALTER TABLE gme_library ADD COLUMN player_mode TEXT DEFAULT 'music';",
            ],
            "1.0.0": ["UPDATE config SET value='1.0.0' WHERE param='version';"],
            "2.0.0": [
                "UPDATE config SET value='2.0.0' WHERE param='version';",
                "INSERT OR IGNORE INTO config (param, value) VALUES ('print_page_margin', '0.5in');",
            ],
            "2.0.1": [
                # Fix encoding issues from legacy Perl databases
                lambda: self._fix_text_encoding(
                    "gme_library",
                    "oid",
                    [
                        "album_title",
                        "album_artist",
                        "picture_filename",
                        "gme_file",
                        "path",
                    ],
                ),
                lambda: self._fix_text_encoding(
                    "tracks",
                    "rowid",
                    [
                        "album",
                        "artist",
                        "genre",
                        "lyrics",
                        "title",
                        "filename",
                        "tt_script",
                    ],
                ),
                "UPDATE config SET value='2.0.1' WHERE param='version';",
            ],
        }
        current_version = Version(self.get_config_value("version"))

        for version_str in sorted(updates.keys(), key=Version):
            update_version = Version(version_str)
            if update_version > current_version:
                try:
                    for sql_or_func in updates[version_str]:
                        if callable(sql_or_func):
                            # Execute function (e.g., for encoding fixes)
                            result = sql_or_func()
                            logger.info(f"Executed update function, result: {result}")
                        else:
                            # Execute SQL
                            self.execute(sql_or_func)
                    self.commit()
                except Exception as e:
                    self.conn.rollback()
                    raise RuntimeError(f"Can't update config database.\n\tError: {e}")

        return True

    def get_oid_cache(self) -> Path:
        """Get the OID cache directory from library path in database.

        Returns:
            Path to OID cache directory
        """
        # Get library path from database configuration
        library_path_str = self.get_config_value("library_path")

        if library_path_str:
            library_path = Path(library_path_str)
        else:
            # Fallback to default if not set
            from ttmp32gme.build.file_handler import get_default_library_path

            library_path = get_default_library_path()

        cache_dir = library_path / ".oid_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def create_oid_images_zip(self) -> Optional[io.BytesIO]:
        """Create a ZIP file containing all OID images from the cache.

        Returns:
            BytesIO object containing the ZIP file, or None if no images found
        """
        import zipfile

        oid_cache = self.get_oid_cache()

        # Get all PNG files in the OID cache
        png_files = list(oid_cache.glob("*.png"))

        if not png_files:
            logger.warning("No OID images found in cache")
            return None

        # Create ZIP file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            for png_file in png_files:
                zipf.write(png_file, png_file.name)

        memory_file.seek(0)
        logger.info(f"Created ZIP with {len(png_files)} OID images")
        return memory_file


def extract_tracks_from_album(album: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract track dictionaries from an album dictionary.

    Args:
        album: Album dictionary

    Returns:
        List of track dictionaries
    """
    tracks = []
    for key in sorted(album.keys(), reverse=True):
        if key.startswith("track_"):
            track = album.pop(key)
            track["old_track"] = key.removeprefix("track_")
            tracks.append(track)
    return tracks, album


def get_cover_filename(mimetype: Optional[str], picture_data: bytes) -> Optional[str]:
    """Generate a filename for cover image.

    Args:
        mimetype: Image MIME type
        picture_data: Image data

    Returns:
        Cover filename or None
    """
    if mimetype and mimetype.startswith("image/"):
        ext = mimetype.split("/")[-1]
        return f"cover.{ext}"
    elif picture_data:
        try:
            img = Image.open(io.BytesIO(picture_data))
            return f"cover.{img.format.lower()}"
        except Exception:
            return None
    return None
