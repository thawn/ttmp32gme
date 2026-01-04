"""Unit tests for db_handler module."""

import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from mutagen.oggvorbis import OggVorbis
from pydantic import ValidationError

from ttmp32gme.db_handler import (
    AlbumMetadataModel,
    AlbumUpdateModel,
    DBHandler,
    LibraryActionModel,
    TrackMetadataModel,
    convert_str_to_int,
    trim_optional_str,
    validate_non_empty_str,
)


class TestReusableValidators:
    """Test reusable validator functions."""

    def test_convert_str_to_int_with_string(self):
        """Test converting string to int."""
        assert convert_str_to_int("42") == 42
        assert convert_str_to_int("920") == 920

    def test_convert_str_to_int_with_int(self):
        """Test that integers pass through unchanged."""
        assert convert_str_to_int(42) == 42
        assert convert_str_to_int(920) == 920

    def test_convert_str_to_int_with_none(self):
        """Test that None passes through unchanged."""
        assert convert_str_to_int(None) is None

    def test_convert_str_to_int_invalid(self):
        """Test that invalid strings raise ValueError."""
        with pytest.raises(ValueError) as exc:
            convert_str_to_int("not_a_number")
        assert "invalid literal for int()" in str(exc.value)

    def test_trim_optional_str_with_whitespace(self):
        """Test trimming strings with whitespace."""
        assert trim_optional_str("  hello  ") == "hello"
        assert trim_optional_str("world\n") == "world"

    def test_trim_optional_str_with_none(self):
        """Test that None returns None."""
        assert trim_optional_str(None) is None

    def test_trim_optional_str_with_empty(self):
        """Test that empty string returns empty string unchanged."""
        assert trim_optional_str("") == ""

    def test_trim_optional_str_with_non_string(self):
        """Test that non-string values return unchanged."""
        for v in [[], True, 123, 3.14, {}]:
            with pytest.raises(ValueError) as exc:
                trim_optional_str(v)
            assert "must be a string or None" in str(exc.value)

    def test_validate_non_empty_str_valid(self):
        """Test validating non-empty strings."""
        assert validate_non_empty_str("hello") == "hello"
        assert validate_non_empty_str("  world  ") == "world"

    def test_validate_non_empty_str_empty(self):
        """Test that empty strings raise ValueError."""
        with pytest.raises(ValueError) as exc:
            validate_non_empty_str("")
        assert "cannot be empty" in str(exc.value)

    def test_validate_non_empty_str_whitespace(self):
        """Test that whitespace-only strings raise ValueError."""
        with pytest.raises(ValueError) as exc:
            validate_non_empty_str("   ")
        assert "cannot be empty" in str(exc.value)

    def test_validate_non_empty_str_custom_field_name(self):
        """Test custom field name in error message."""
        with pytest.raises(ValueError) as exc:
            validate_non_empty_str("", "Custom field")
        assert "Custom field cannot be empty" in str(exc.value)

    def test_validate_non_empty_str_non_string(self):
        """Test that non-string values raise TypeError."""
        with pytest.raises(TypeError) as exc:
            validate_non_empty_str(123)
        assert "must be a string" in str(exc.value)

        with pytest.raises(TypeError) as exc:
            validate_non_empty_str(None, "My field")
        assert "My field must be a string" in str(exc.value)


class TestAlbumUpdateModel:
    """Test AlbumUpdateModel validation."""

    def test_oid_string_to_int_conversion(self):
        """Test that OID strings are converted to integers."""
        data = {"oid": "920", "album_title": "Test"}
        model = AlbumUpdateModel(**data)
        assert model.oid == 920
        assert isinstance(model.oid, int)

    def test_uid_string_to_int_conversion(self):
        """Test that UID strings are converted to integers."""
        data = {"uid": "920", "album_title": "Test"}
        model = AlbumUpdateModel(**data)
        assert model.uid == 920
        assert isinstance(model.uid, int)


class TestLibraryActionModel:
    """Test LibraryActionModel validation."""

    def test_uid_string_to_int_conversion(self):
        """Test that UID strings are converted to integers."""
        data = {"uid": "920"}
        model = LibraryActionModel(**data)
        assert model.uid == 920
        assert isinstance(model.uid, int)

    def test_uid_required(self):
        """Test that UID is required."""
        with pytest.raises(ValidationError) as exc:
            LibraryActionModel()
        assert "uid" in str(exc.value)


class TestAlbumMetadataModel:
    """Test AlbumMetadataModel validation."""

    def test_valid_album_metadata(self):
        """Test valid album metadata."""
        data = {
            "oid": 920,
            "album_title": "Test Album",
            "album_artist": "Test Artist",
            "album_year": "2023",
            "num_tracks": 5,
            "picture_filename": "cover.jpg",
            "path": "/path/to/album",
        }
        model = AlbumMetadataModel(**data)
        assert model.oid == 920
        assert model.album_title == "Test Album"
        assert model.album_artist == "Test Artist"
        assert model.num_tracks == 5

    def test_album_title_required(self):
        """Test that album title is required."""
        data = {
            "oid": 920,
            "num_tracks": 5,
            "path": "/path/to/album",
        }
        with pytest.raises(ValidationError) as exc:
            AlbumMetadataModel(**data)
        assert "album_title" in str(exc.value)

    def test_album_title_empty(self):
        """Test that empty album title is rejected."""
        data = {
            "oid": 920,
            "album_title": "   ",
            "num_tracks": 5,
            "path": "/path/to/album",
        }
        with pytest.raises(ValidationError) as exc:
            AlbumMetadataModel(**data)
        assert "Album title cannot be empty" in str(exc.value)

    def test_album_title_trimmed(self):
        """Test that album title is trimmed."""
        data = {
            "oid": 920,
            "album_title": "  Test Album  ",
            "num_tracks": 5,
            "path": "/path/to/album",
        }
        model = AlbumMetadataModel(**data)
        assert model.album_title == "Test Album"

    def test_invalid_oid_range(self):
        """Test that OID must be in valid range."""
        data = {
            "oid": 1500,  # Too high
            "album_title": "Test Album",
            "num_tracks": 5,
            "path": "/path/to/album",
        }
        with pytest.raises(ValidationError):
            AlbumMetadataModel(**data)

    def test_negative_oid(self):
        """Test that negative OID is rejected."""
        data = {
            "oid": -1,
            "album_title": "Test Album",
            "num_tracks": 5,
            "path": "/path/to/album",
        }
        with pytest.raises(ValidationError):
            AlbumMetadataModel(**data)

    def test_num_tracks_range(self):
        """Test that num_tracks must be in valid range."""
        data = {
            "oid": 920,
            "album_title": "Test Album",
            "num_tracks": 1000,  # Too high
            "path": "/path/to/album",
        }
        with pytest.raises(ValidationError):
            AlbumMetadataModel(**data)

    def test_year_validation(self):
        """Test year validation and truncation."""
        data = {
            "oid": 920,
            "album_title": "Test Album",
            "num_tracks": 5,
            "album_year": "2023-01-01T00:00:00",
            "path": "/path/to/album",
        }
        model = AlbumMetadataModel(**data)
        # Should be truncated to 10 chars
        assert len(model.album_year) <= 10


class TestTrackMetadataModel:
    """Test TrackMetadataModel validation."""

    def test_valid_track_metadata(self):
        """Test valid track metadata."""
        data = {
            "parent_oid": 920,
            "album": "Test Album",
            "artist": "Test Artist",
            "disc": "1",
            "duration": 180000,
            "genre": "Rock",
            "lyrics": "Test lyrics",
            "title": "Test Track",
            "track": 1,
            "filename": "test_track.mp3",
        }
        model = TrackMetadataModel(**data)
        assert model.parent_oid == 920
        assert model.title == "Test Track"
        assert model.track == 1
        assert model.duration == 180000

    def test_track_title_required(self):
        """Test that track title is required."""
        data = {
            "parent_oid": 920,
            "duration": 180000,
            "track": 1,
            "filename": "test_track.mp3",
        }
        with pytest.raises(ValidationError) as exc:
            TrackMetadataModel(**data)
        assert "title" in str(exc.value)

    def test_track_title_empty(self):
        """Test that empty track title is rejected."""
        data = {
            "parent_oid": 920,
            "title": "   ",
            "duration": 180000,
            "track": 1,
            "filename": "test_track.mp3",
        }
        with pytest.raises(ValidationError) as exc:
            TrackMetadataModel(**data)
        assert "Track title cannot be empty" in str(exc.value)

    def test_track_title_trimmed(self):
        """Test that track title is trimmed."""
        data = {
            "parent_oid": 920,
            "title": "  Test Track  ",
            "duration": 180000,
            "track": 1,
            "filename": "test_track.mp3",
        }
        model = TrackMetadataModel(**data)
        assert model.title == "Test Track"

    def test_invalid_track_number(self):
        """Test that track number must be >= 1."""
        data = {
            "parent_oid": 920,
            "title": "Test Track",
            "duration": 180000,
            "track": 0,  # Invalid
            "filename": "test_track.mp3",
        }
        with pytest.raises(ValidationError):
            TrackMetadataModel(**data)

    def test_invalid_duration(self):
        """Test that duration must be >= 0."""
        data = {
            "parent_oid": 920,
            "title": "Test Track",
            "duration": -1000,  # Invalid
            "track": 1,
            "filename": "test_track.mp3",
        }
        with pytest.raises(ValidationError):
            TrackMetadataModel(**data)


class TestDBHandlerHelperMethods:
    """Test DBHandler helper methods."""

    @pytest.fixture
    def db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_handler = DBHandler(db_path)
        db_handler.initialize()
        yield db_handler

        db_handler.close()
        Path(db_path).unlink(missing_ok=True)

    def test_finalize_album_data_with_title(self, db: DBHandler):
        """Test _finalize_album_data with valid title."""
        album_data = {
            "album_title": "Test Album",
            "album_artist": "Test Artist",
            "path": "Test_Album",
        }
        result = db._finalize_album_data(album_data, 920, 5)

        assert result["oid"] == 920
        assert result["num_tracks"] == 5
        assert result["album_title"] == "Test Album"
        assert result["path"] == "Test_Album"

    def test_finalize_album_data_without_title(self, db: DBHandler):
        """Test _finalize_album_data defaults to 'unknown' when no title."""
        album_data = {}
        result = db._finalize_album_data(album_data, 920, 5)

        assert result["oid"] == 920
        assert result["num_tracks"] == 5
        assert result["album_title"] == "unknown"
        assert result["path"] == "unknown"

    def test_finalize_album_data_validation_error(self, db: DBHandler):
        """Test _finalize_album_data raises error for invalid OID."""
        album_data = {
            "album_title": "Test Album",
            "path": "Test_Album",
        }
        with pytest.raises(ValidationError):
            # OID out of range
            db._finalize_album_data(album_data, 9999, 5)

    def test_sort_and_renumber_tracks(self, db: DBHandler):
        """Test _sort_and_renumber_tracks."""
        track_data = [
            {"track": 3, "disc": 1, "filename": "track3.mp3"},
            {"track": 1, "disc": 1, "filename": "track1.mp3"},
            {"track": 2, "disc": 2, "filename": "track2.mp3"},
        ]
        result = db._sort_and_renumber_tracks(track_data)

        assert len(result) == 3
        # Should be sorted by disc, then track
        assert result[0]["track"] == 1  # disc 1, originally track 1
        assert result[1]["track"] == 2  # disc 1, originally track 3
        assert result[2]["track"] == 3  # disc 2, originally track 2

    def test_sort_and_renumber_tracks_empty(self, db: DBHandler):
        """Test _sort_and_renumber_tracks with empty list."""
        result = db._sort_and_renumber_tracks([])
        assert result == []

    def test_process_cover_image_success(self, db: DBHandler):
        """Test _process_cover_image with valid image."""
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"fake image data")
            image_path = Path(f.name)

        try:
            filename, data = db._process_cover_image(image_path)
            assert filename is not None
            assert filename.endswith(".jpg")
            assert data == b"fake image data"
        finally:
            image_path.unlink(missing_ok=True)

    def test_process_cover_image_nonexistent(self, db: DBHandler):
        """Test _process_cover_image with nonexistent file."""
        filename, data = db._process_cover_image(Path("/nonexistent/image.jpg"))
        assert filename is None
        assert data is None

    def test_extract_audio_metadata_with_real_file(self, db: DBHandler):
        """Test _extract_audio_metadata with real test file."""
        # Use the actual test file from fixtures
        test_file = Path(__file__).parent.parent / "fixtures" / "test_audio.mp3"
        if not test_file.exists():
            pytest.skip("Test audio file not found")

        album_data, track_info, picture_data = db._extract_audio_metadata(
            test_file, 920, 1
        )

        # Should successfully extract something from the file
        assert track_info is not None
        assert track_info["parent_oid"] == 920
        assert track_info["filename"] == test_file
        assert track_info["duration"] >= 0

    @patch("ttmp32gme.db_handler.MutagenFile")
    def test_extract_audio_metadata_none_audio(self, mock_mutagen, db: DBHandler):
        """Test _extract_audio_metadata when audio is None."""
        mock_mutagen.return_value = None

        file_path = Path("/tmp/test.ogg")
        album_data, track_info, picture_data = db._extract_audio_metadata(
            file_path, 920, 1
        )

        assert album_data is None
        assert track_info is None
        assert picture_data is None

    @patch("ttmp32gme.db_handler.MP3")
    def test_extract_audio_metadata_exception(self, mock_mp3, db: DBHandler):
        """Test _extract_audio_metadata handles exceptions."""
        mock_mp3.side_effect = Exception("Test error")

        file_path = Path("/tmp/test.mp3")
        album_data, track_info, picture_data = db._extract_audio_metadata(
            file_path, 920, 1
        )

        assert album_data is None
        assert track_info is None
        assert picture_data is None


class TestDBHandlerCoreMethods:
    """Test core DBHandler methods."""

    @pytest.fixture
    def db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_handler = DBHandler(db_path)
        db_handler.initialize()
        yield db_handler

        db_handler.close()
        Path(db_path).unlink(missing_ok=True)

    def test_connect_and_close(self):
        """Test database connection and closing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            db = DBHandler(db_path)
            assert db._conn is None

            # The db should connect on first use of db.conn
            assert db.conn is not None

            db.close()
            assert db._conn is None
        finally:
            Path(db_path).unlink(missing_ok=True)

    def testexecute_context(self, db: DBHandler):
        """Test execute method."""
        with db.execute_context(
            "SELECT * FROM config WHERE param=?", ("version",)
        ) as cursor:
            assert cursor is not None
            result = cursor.fetchone()
            assert result is not None

    def test_fetchall(self, db: DBHandler):
        """Test fetchall method."""
        results = db.fetchall("SELECT * FROM config")
        assert len(results) > 0
        assert "param" in results[0].keys()

    def test_fetchone(self, db: DBHandler):
        """Test fetchone method."""
        result = db.fetchone("SELECT * FROM config WHERE param=?", ("version",))
        assert result is not None
        assert result["param"] == "version"

    def test_fetchone_not_found(self, db: DBHandler):
        """Test fetchone when no result found."""
        result = db.fetchone("SELECT * FROM config WHERE param=?", ("nonexistent",))
        assert result is None

    def test_commit(self, db: DBHandler):
        """Test commit method."""
        db.execute_and_commit(
            "INSERT INTO config (param, value) VALUES (?, ?)",
            ("test_param", "test_value"),
        )
        result = db.fetchone("SELECT * FROM config WHERE param=?", ("test_param",))
        assert result is not None
        assert result["value"] == "test_value"

    def test_write_to_database(self, db: DBHandler):
        """Test write_to_database method."""
        data = {"param": "test_write", "value": "test_value_123"}
        db.write_to_database("config", data)

        result = db.fetchone("SELECT * FROM config WHERE param=?", ("test_write",))
        assert result is not None
        assert result["value"] == "test_value_123"

    def test_get_config(self, db: DBHandler):
        """Test get_config method."""
        config = db.get_config()
        assert isinstance(config, dict)
        assert "version" in config
        assert "host" in config
        assert "port" in config

    def test_get_config_value(self, db: DBHandler):
        """Test get_config_value method."""
        version = db.get_config_value("version")
        assert version is not None
        assert version == "2.0.0"

    def test_get_config_value_not_found(self, db: DBHandler):
        """Test get_config_value for non-existent parameter."""
        value = db.get_config_value("nonexistent_param")
        assert value is None

    def test_oid_exist(self, db: DBHandler):
        """Test oid_exist method."""
        # Initially no albums
        assert db.oid_exist(920) is False

        # Add an album
        db.write_to_database(
            "gme_library",
            {
                "oid": 920,
                "album_title": "Test Album",
                "num_tracks": 1,
                "path": "/test/path",
            },
        )

        # Now it should exist
        assert db.oid_exist(920) is True
        assert db.oid_exist(921) is False

    def test_new_oid_empty_database(self, db: DBHandler):
        """Test new_oid with empty database."""
        oid = db.new_oid()
        assert oid == 920  # Default starting OID

    def test_new_oid_with_existing_albums(self, db: DBHandler):
        """Test new_oid with existing albums."""
        # Add some albums
        db.write_to_database(
            "gme_library",
            {
                "oid": 920,
                "album_title": "Album 1",
                "num_tracks": 1,
                "path": "/test/path1",
            },
        )
        db.write_to_database(
            "gme_library",
            {
                "oid": 921,
                "album_title": "Album 2",
                "num_tracks": 1,
                "path": "/test/path2",
            },
        )

        oid = db.new_oid()
        assert oid == 922  # Next available OID

    def test_get_tracks(self, db: DBHandler):
        """Test get_tracks method."""
        # Add an album and tracks
        db.write_to_database(
            "gme_library",
            {
                "oid": 920,
                "album_title": "Test Album",
                "num_tracks": 2,
                "path": "/test/path",
            },
        )
        db.write_to_database(
            "tracks",
            {
                "parent_oid": 920,
                "title": "Track 1",
                "track": 1,
                "duration": 180000,
                "filename": "track1.mp3",
            },
        )
        db.write_to_database(
            "tracks",
            {
                "parent_oid": 920,
                "title": "Track 2",
                "track": 2,
                "duration": 200000,
                "filename": "track2.mp3",
            },
        )

        album = {"oid": 920}
        tracks = db.get_tracks(album)

        assert len(tracks) == 2
        assert 1 in tracks
        assert 2 in tracks
        assert tracks[1]["title"] == "Track 1"
        assert tracks[2]["title"] == "Track 2"

    def test_update_table_entry(self, db: DBHandler):
        """Test update_table_entry method."""
        # Add a config entry
        db.write_to_database(
            "config", {"param": "test_update", "value": "original_value"}
        )

        # Update it
        db.update_table_entry(
            "config", "param=?", ["test_update"], {"value": "updated_value"}
        )

        result = db.fetchone("SELECT * FROM config WHERE param=?", ("test_update",))
        assert result["value"] == "updated_value"

    def test_db_row_to_album(self, db: DBHandler):
        """Test db_row_to_album method."""
        # Add album and tracks
        db.write_to_database(
            "gme_library",
            {
                "oid": 920,
                "album_title": "Test Album",
                "album_artist": "Test Artist",
                "num_tracks": 1,
                "path": "/test/path",
            },
        )
        db.write_to_database(
            "tracks",
            {
                "parent_oid": 920,
                "title": "Track 1",
                "track": 1,
                "duration": 180000,
                "filename": "track1.mp3",
            },
        )

        row = db.fetchone("SELECT * FROM gme_library WHERE oid=?", (920,))
        album = db.db_row_to_album(row)

        assert album["oid"] == 920
        assert album["album_title"] == "Test Album"
        assert "track_1" in album
        assert album["track_1"]["title"] == "Track 1"

    def test_get_album(self, db: DBHandler):
        """Test get_album method."""
        # Add album and track
        db.write_to_database(
            "gme_library",
            {
                "oid": 920,
                "album_title": "Test Album",
                "num_tracks": 1,
                "path": "/test/path",
            },
        )
        db.write_to_database(
            "tracks",
            {
                "parent_oid": 920,
                "title": "Track 1",
                "track": 1,
                "duration": 180000,
                "filename": "track1.mp3",
            },
        )

        album = db.get_album(920)
        assert album is not None
        assert album["oid"] == 920
        assert album["album_title"] == "Test Album"
        assert "track_1" in album

    def test_get_album_not_found(self, db: DBHandler):
        """Test get_album when album doesn't exist."""
        album = db.get_album(999)
        assert album is None

    def test_get_album_list(self, db: DBHandler):
        """Test get_album_list method."""
        # Add multiple albums
        db.write_to_database(
            "gme_library",
            {"oid": 920, "album_title": "Album 1", "num_tracks": 0, "path": "/path1"},
        )
        db.write_to_database(
            "gme_library",
            {"oid": 921, "album_title": "Album 2", "num_tracks": 0, "path": "/path2"},
        )

        albums = db.get_album_list()
        assert len(albums) == 2
        assert albums[0]["oid"] == 920
        assert albums[1]["oid"] == 921

    def test_delete_album_tracks(self, db: DBHandler):
        """Test delete_album_tracks method."""
        # Add album and tracks
        db.write_to_database(
            "gme_library",
            {
                "oid": 920,
                "album_title": "Test Album",
                "num_tracks": 2,
                "path": "/test/path",
            },
        )
        db.write_to_database(
            "tracks",
            {
                "parent_oid": 920,
                "title": "Track 1",
                "track": 1,
                "duration": 180000,
                "filename": "track1.mp3",
            },
        )
        db.write_to_database(
            "tracks",
            {
                "parent_oid": 920,
                "title": "Track 2",
                "track": 2,
                "duration": 200000,
                "filename": "track2.mp3",
            },
        )

        # Verify tracks exist
        tracks = db.get_tracks({"oid": 920})
        assert len(tracks) == 2

        # Delete tracks
        db.delete_album_tracks(920)

        # Verify tracks are deleted
        tracks = db.get_tracks({"oid": 920})
        assert len(tracks) == 0

    def test_context_manager(self):
        """Test DBHandler as context manager."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            with DBHandler(db_path) as db:
                db.initialize()
                assert db.conn is not None

                # Use the database
                config = db.get_config()
                assert "version" in config

            # Connection should be closed after exiting context
            # (we can't directly test this without accessing private state)
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_gme_library_columns(self, db: DBHandler):
        """Test gme_library_columns property."""
        columns = db.gme_library_columns
        assert isinstance(columns, list)
        assert "oid" in columns
        assert "album_title" in columns
        assert "num_tracks" in columns
        assert "path" in columns

    def test_update_tracks(self, db: DBHandler):
        """Test update_tracks method."""

        # Create a temporary directory for album
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Add album with tracks
            db.write_to_database(
                "gme_library",
                {
                    "oid": 920,
                    "album_title": "Test Album",
                    "num_tracks": 2,
                    "path": str(temp_dir),
                },
            )
            db.write_to_database(
                "tracks",
                {
                    "parent_oid": 920,
                    "title": "Track 1",
                    "track": 1,
                    "duration": 180000,
                    "filename": "track1.mp3",
                    "album": "Test Album",
                    "artist": "Test Artist",
                },
            )
            db.write_to_database(
                "tracks",
                {
                    "parent_oid": 920,
                    "title": "Track 2",
                    "track": 2,
                    "duration": 200000,
                    "filename": "track2.mp3",
                    "album": "Test Album",
                    "artist": "Test Artist",
                },
            )

            # Update tracks
            # Get the actual track IDs from the database
            current_tracks = db.get_tracks({"oid": 920})
            tracks_to_update = [
                {
                    "id": current_tracks[1]["id"],
                    "track": 2,
                    "title": "Updated Track 1",
                },
                {
                    "id": current_tracks[2]["id"],
                    "track": 1,
                    "title": "Updated Track 2",
                },
            ]

            db.update_tracks(tracks_to_update, 920, 920)

            # Verify tracks were updated
            updated_tracks = db.get_tracks({"oid": 920})
            assert len(updated_tracks) == 2
            assert updated_tracks[1]["title"] == "Updated Track 2"
            assert updated_tracks[2]["title"] == "Updated Track 1"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_update_album(self, db: DBHandler):
        """Test update_album method."""

        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Add album with track
            db.write_to_database(
                "gme_library",
                {
                    "oid": 920,
                    "album_title": "Original Album",
                    "album_artist": "Original Artist",
                    "num_tracks": 1,
                    "path": str(temp_dir),
                },
            )
            db.write_to_database(
                "tracks",
                {
                    "parent_oid": 920,
                    "title": "Track 1",
                    "track": 1,
                    "duration": 180000,
                    "filename": "track1.mp3",
                    "album": "Original Album",
                    "artist": "Original Artist",
                },
            )

            # Update album
            # Get the actual track ID from the database
            current_tracks = db.get_tracks({"oid": 920})
            album_data = {
                "oid": 920,
                "album_title": "Updated Album",
                "album_artist": "Updated Artist",
                "track_1": {
                    "id": current_tracks[1]["id"],
                    "track": 1,
                    "title": "Updated Track 1",
                },
            }

            result_oid = db.update_album(album_data)
            assert result_oid == 920

            # Verify album was updated
            album = db.get_album(920)
            assert album["album_title"] == "Updated Album"
            assert album["album_artist"] == "Updated Artist"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_delete_album(self, db: DBHandler):
        """Test delete_album method."""

        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Add album with track
            db.write_to_database(
                "gme_library",
                {
                    "oid": 920,
                    "album_title": "Test Album",
                    "num_tracks": 1,
                    "path": str(temp_dir),
                },
            )
            db.write_to_database(
                "tracks",
                {
                    "parent_oid": 920,
                    "title": "Track 1",
                    "track": 1,
                    "duration": 180000,
                    "filename": "track1.mp3",
                },
            )

            # Verify album exists
            assert db.get_album(920) is not None

            # Delete album
            db.delete_album(920)

            # Verify album is deleted
            assert db.get_album(920) is None

            # Verify tracks are also deleted
            tracks = db.get_tracks({"oid": 920})
            assert len(tracks) == 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_replace_cover(self, db: DBHandler):
        """Test replace_cover method."""

        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Add album
            db.write_to_database(
                "gme_library",
                {
                    "oid": 920,
                    "album_title": "Test Album",
                    "num_tracks": 0,
                    "path": str(temp_dir),
                    "picture_filename": "old_cover.jpg",
                },
            )

            # Create old cover file
            old_cover = temp_dir / "old_cover.jpg"
            old_cover.write_bytes(b"old image data")

            # Replace cover
            new_cover_data = b"new image data"
            db.replace_cover(920, "new_cover.jpg", new_cover_data)

            # Verify old cover is removed
            assert not old_cover.exists()

            # Verify new cover exists
            new_cover = temp_dir / "new_cover.jpg"
            assert new_cover.exists()
            assert new_cover.read_bytes() == new_cover_data

            # Verify database is updated
            album = db.get_album(920)
            assert album["picture_filename"] == "new_cover.jpg"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cleanup_album(self, db: DBHandler):
        """Test cleanup_album method."""

        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Add album with gme_file set
            db.write_to_database(
                "gme_library",
                {
                    "oid": 920,
                    "album_title": "Test Album",
                    "num_tracks": 0,
                    "path": str(temp_dir),
                    "gme_file": "album.gme",
                },
            )

            # Verify gme_file is set before cleanup
            album_before = db.get_album(920)
            assert album_before["gme_file"] == "album.gme"

            # Create files to be cleaned up
            yaml_file = temp_dir / "album.yaml"
            yaml_file.write_text("test yaml content")

            gme_file = temp_dir / "album.gme"
            gme_file.write_bytes(b"test gme data")

            audio_dir = temp_dir / "audio"
            audio_dir.mkdir()
            (audio_dir / "track.mp3").write_bytes(b"audio data")

            # Cleanup album
            db.cleanup_album(920)

            # Verify files are cleaned up
            assert not yaml_file.exists()
            assert not gme_file.exists()
            assert not audio_dir.exists()

            # Verify album still exists in database
            album_after = db.get_album(920)
            assert album_after is not None

            # Verify gme_file column is set to NULL
            assert album_after["gme_file"] is None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_extract_ogg_metadata(self, db: DBHandler):
        """Test extracting metadata from OGG Vorbis files."""
        # Get path to test MP3 file
        test_mp3 = Path(__file__).parent.parent / "fixtures" / "test_audio.mp3"
        if not test_mp3.exists():
            pytest.skip("Test audio file not available")

        # Check if ffmpeg is available
        if not shutil.which("ffmpeg"):
            pytest.skip("ffmpeg not found")

        # Create temp directory for test OGG file
        temp_dir = Path(tempfile.mkdtemp())
        try:
            test_ogg = temp_dir / "test_with_tags.ogg"

            # Convert MP3 to OGG using ffmpeg (same args as tttool_handler.py)
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(test_mp3),
                "-map",
                "0:a",
                "-ar",
                "22050",
                "-ac",
                "1",
                str(test_ogg),
            ]
            subprocess.run(cmd, check=True, capture_output=True)

            # Add Vorbis tags
            audio = OggVorbis(str(test_ogg))
            audio["title"] = "Test OGG Title"
            audio["artist"] = "Test OGG Artist"
            audio["album"] = "Test OGG Album"
            audio["date"] = "2024"
            audio["tracknumber"] = "1"
            audio.save()

            # Test metadata extraction
            album_data, track_info, picture_data = db._extract_audio_metadata(
                test_ogg, 920, 1
            )

            # Verify album data
            assert album_data is not None
            assert album_data["album_title"] == "Test OGG Album"
            assert album_data["album_artist"] == "Test OGG Artist"
            assert album_data["album_year"] == "2024"

            # Verify track info
            assert track_info is not None
            assert track_info["title"] == "Test OGG Title"
            assert track_info["artist"] == "Test OGG Artist"
            assert track_info["album"] == "Test OGG Album"
            assert track_info["track"] == 1
            assert track_info["duration"] > 0

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_extract_ogg_metadata_no_tags(self, db: DBHandler):
        """Test extracting metadata from OGG file without tags."""
        # Get path to test MP3 file
        test_mp3 = Path(__file__).parent.parent / "fixtures" / "test_audio.mp3"
        if not test_mp3.exists():
            pytest.skip("Test audio file not available")

        # Check if ffmpeg is available
        if not shutil.which("ffmpeg"):
            pytest.skip("ffmpeg not found")

        # Create temp directory for test OGG file
        temp_dir = Path(tempfile.mkdtemp())
        try:
            test_ogg = temp_dir / "test_no_tags.ogg"

            # Convert MP3 to OGG without adding tags
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(test_mp3),
                "-map",
                "0:a",
                "-ar",
                "22050",
                "-ac",
                "1",
                str(test_ogg),
            ]
            subprocess.run(cmd, check=True, capture_output=True)

            # Test metadata extraction
            album_data, track_info, picture_data = db._extract_audio_metadata(
                test_ogg, 920, 1
            )

            # Album data handling: When an OGG file has no tags, the _extract_audio_metadata function
            # returns None for album_data (since there are no album-level tags to extract).
            # We explicitly check for None here as that's the expected behavior.
            assert (
                album_data is None or album_data == {}
            ), f"Expected None or empty album data for tagless OGG file, got {album_data}"

            # Track info should have filename as title
            assert track_info is not None
            assert track_info["title"] == "test_no_tags.ogg"
            assert track_info["artist"] == ""
            assert track_info["album"] == ""
            assert track_info["duration"] > 0

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
