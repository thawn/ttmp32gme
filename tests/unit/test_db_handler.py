"""Unit tests for db_handler module."""

import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
from pydantic import ValidationError

from ttmp32gme.db_handler import (
    DBHandler,
    AlbumMetadataModel,
    TrackMetadataModel,
)


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

    def test_finalize_album_data_with_title(self, db):
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

    def test_finalize_album_data_without_title(self, db):
        """Test _finalize_album_data defaults to 'unknown' when no title."""
        album_data = {}
        result = db._finalize_album_data(album_data, 920, 5)
        
        assert result["oid"] == 920
        assert result["num_tracks"] == 5
        assert result["album_title"] == "unknown"
        assert result["path"] == "unknown"

    def test_finalize_album_data_validation_error(self, db):
        """Test _finalize_album_data raises error for invalid OID."""
        album_data = {
            "album_title": "Test Album",
            "path": "Test_Album",
        }
        with pytest.raises(ValidationError):
            # OID out of range
            db._finalize_album_data(album_data, 9999, 5)

    def test_sort_and_renumber_tracks(self, db):
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

    def test_sort_and_renumber_tracks_empty(self, db):
        """Test _sort_and_renumber_tracks with empty list."""
        result = db._sort_and_renumber_tracks([])
        assert result == []

    def test_process_cover_image_success(self, db):
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

    def test_process_cover_image_nonexistent(self, db):
        """Test _process_cover_image with nonexistent file."""
        filename, data = db._process_cover_image(Path("/nonexistent/image.jpg"))
        assert filename is None
        assert data is None

    def test_extract_audio_metadata_with_real_file(self, db):
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

    @patch('ttmp32gme.db_handler.MutagenFile')
    def test_extract_audio_metadata_none_audio(self, mock_mutagen, db):
        """Test _extract_audio_metadata when audio is None."""
        mock_mutagen.return_value = None
        
        file_path = Path("/tmp/test.ogg")
        album_data, track_info, picture_data = db._extract_audio_metadata(
            file_path, 920, 1
        )
        
        assert album_data is None
        assert track_info is None
        assert picture_data is None

    @patch('ttmp32gme.db_handler.MP3')
    def test_extract_audio_metadata_exception(self, mock_mp3, db):
        """Test _extract_audio_metadata handles exceptions."""
        mock_mp3.side_effect = Exception("Test error")
        
        file_path = Path("/tmp/test.mp3")
        album_data, track_info, picture_data = db._extract_audio_metadata(
            file_path, 920, 1
        )
        
        assert album_data is None
        assert track_info is None
        assert picture_data is None
