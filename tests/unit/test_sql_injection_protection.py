"""Unit tests for SQL injection protection and input sanitization."""

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from ttmp32gme.db_handler import (
    AlbumMetadataModel,
    AlbumUpdateModel,
    ConfigUpdateModel,
    DBHandler,
    TrackMetadataModel,
    sanitize_string,
    validate_column_names,
    validate_table_name,
)


class TestSanitizeString:
    """Test string sanitization for SQL injection and XSS prevention."""

    def test_sanitize_normal_string(self):
        """Test that normal strings pass through unchanged."""
        assert sanitize_string("Hello World") == "Hello World"
        assert sanitize_string("Album Title 123") == "Album Title 123"

    def test_sanitize_html_tags_stripped(self):
        """Test that HTML tags are stripped by default."""
        result = sanitize_string("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "alert" not in result or "Hello" in result

    def test_sanitize_html_tags_allowed(self):
        """Test that allowed HTML tags are preserved when allow_html=True."""
        result = sanitize_string("<b>Bold</b> text", allow_html=True)
        assert "<b>Bold</b>" in result or "Bold" in result

    def test_sanitize_sql_injection_select(self):
        """Test that SELECT statements are rejected."""
        with pytest.raises(ValueError) as exc:
            sanitize_string("'; SELECT * FROM users; --")
        assert "suspicious SQL patterns" in str(exc.value)

    def test_sanitize_sql_injection_drop(self):
        """Test that DROP statements are rejected."""
        with pytest.raises(ValueError) as exc:
            sanitize_string("'; DROP TABLE users; --")
        assert "suspicious SQL patterns" in str(exc.value)

    def test_sanitize_sql_injection_union(self):
        """Test that UNION attacks are rejected."""
        with pytest.raises(ValueError) as exc:
            sanitize_string("1' UNION SELECT password FROM users--")
        assert "suspicious SQL patterns" in str(exc.value)

    def test_sanitize_sql_injection_or_equals(self):
        """Test that OR 1=1 style attacks are rejected."""
        with pytest.raises(ValueError) as exc:
            sanitize_string("admin' OR 1=1--")
        assert "suspicious SQL patterns" in str(exc.value)

    def test_sanitize_sql_comment_after_quote(self):
        """Test that SQL comments after quotes are rejected."""
        with pytest.raises(ValueError) as exc:
            sanitize_string("test' -- comment")
        assert "suspicious SQL patterns" in str(exc.value)

    def test_sanitize_semicolon_after_quote(self):
        """Test that semicolons after quotes are rejected."""
        with pytest.raises(ValueError) as exc:
            sanitize_string("test'; DROP TABLE")
        assert "suspicious SQL patterns" in str(exc.value)

    def test_sanitize_legitimate_semicolon(self):
        """Test that legitimate semicolons are allowed."""
        result = sanitize_string("Symphony No. 9; Ode to Joy")
        assert "Symphony No. 9; Ode to Joy" in result

    def test_sanitize_legitimate_double_dash(self):
        """Test that legitimate double dashes are allowed."""
        result = sanitize_string("Best of 1990--2000")
        assert "Best of 1990--2000" in result

    def test_sanitize_legitimate_or_and(self):
        """Test that legitimate OR/AND words are allowed."""
        result = sanitize_string("Track 1 OR 2019 Release")
        assert "Track 1 OR 2019 Release" in result

    def test_sanitize_case_insensitive(self):
        """Test that SQL keywords in suspicious contexts are caught."""
        with pytest.raises(ValueError) as exc:
            sanitize_string("SeLeCt * FrOm users")
        assert "suspicious SQL patterns" in str(exc.value)


class TestTableAndColumnValidation:
    """Test table and column name validation."""

    def test_valid_table_names(self):
        """Test that valid table names pass validation."""
        assert validate_table_name("gme_library") == "gme_library"
        assert validate_table_name("tracks") == "tracks"
        assert validate_table_name("config") == "config"
        assert validate_table_name("script_codes") == "script_codes"

    def test_invalid_table_name(self):
        """Test that invalid table names are rejected."""
        with pytest.raises(ValueError) as exc:
            validate_table_name("malicious_table")
        assert "Invalid table name" in str(exc.value)

    def test_sql_injection_in_table_name(self):
        """Test that SQL injection attempts in table names are rejected."""
        with pytest.raises(ValueError):
            validate_table_name("users; DROP TABLE users--")

    def test_valid_column_names_gme_library(self):
        """Test that valid gme_library columns pass validation."""
        columns = ["oid", "album_title", "album_artist"]
        assert validate_column_names("gme_library", columns) == columns

    def test_valid_column_names_tracks(self):
        """Test that valid tracks columns pass validation."""
        columns = ["parent_oid", "title", "artist", "duration"]
        assert validate_column_names("tracks", columns) == columns

    def test_invalid_column_name(self):
        """Test that invalid column names are rejected."""
        with pytest.raises(ValueError) as exc:
            validate_column_names("gme_library", ["oid", "malicious_column"])
        assert "Invalid column name" in str(exc.value)

    def test_sql_injection_in_column_name(self):
        """Test that SQL injection attempts in column names are rejected."""
        with pytest.raises(ValueError):
            validate_column_names("gme_library", ["oid; DROP TABLE users--"])


class TestAlbumUpdateModelSanitization:
    """Test AlbumUpdateModel sanitizes user input."""

    def test_normal_album_update(self):
        """Test that normal album data passes validation."""
        data = {
            "oid": 920,
            "album_title": "My Album",
            "album_artist": "Artist Name",
        }
        model = AlbumUpdateModel(**data)
        assert model.oid == 920
        assert model.album_title == "My Album"
        assert model.album_artist == "Artist Name"

    def test_sql_injection_in_title(self):
        """Test that SQL injection in album title is rejected."""
        with pytest.raises(ValidationError) as exc:
            AlbumUpdateModel(oid=920, album_title="Album'; DROP TABLE gme_library; --")
        assert "suspicious SQL patterns" in str(exc.value)

    def test_sql_injection_in_artist(self):
        """Test that SQL injection in artist name is rejected."""
        with pytest.raises(ValidationError) as exc:
            AlbumUpdateModel(
                oid=920,
                album_title="Album",
                album_artist="' OR 1=1--",
            )
        assert "suspicious SQL patterns" in str(exc.value)

    def test_xss_in_album_fields(self):
        """Test that XSS attempts are sanitized."""
        model = AlbumUpdateModel(
            oid=920,
            album_title="<script>alert('xss')</script>Album",
            album_artist="<b>Artist</b>",
        )
        # Script tags should be removed
        assert "<script>" not in model.album_title
        assert "<b>" not in model.album_artist


class TestAlbumMetadataModelSanitization:
    """Test AlbumMetadataModel sanitizes ID3 tag data."""

    def test_normal_id3_data(self):
        """Test that normal ID3 tag data passes validation."""
        data = {
            "oid": 920,
            "album_title": "Album from ID3",
            "album_artist": "ID3 Artist",
            "num_tracks": 10,
            "path": "/path/to/album",
        }
        model = AlbumMetadataModel(**data)
        assert model.album_title == "Album from ID3"
        assert model.album_artist == "ID3 Artist"

    def test_sql_injection_in_id3_tags(self):
        """Test that SQL injection in ID3 tags is rejected."""
        with pytest.raises(ValidationError) as exc:
            AlbumMetadataModel(
                oid=920,
                album_title="Album'; DELETE FROM tracks; --",
                num_tracks=10,
                path="/path",
            )
        assert "suspicious SQL patterns" in str(exc.value)

    def test_malicious_id3_artist(self):
        """Test that malicious data in artist field is rejected."""
        with pytest.raises(ValidationError) as exc:
            AlbumMetadataModel(
                oid=920,
                album_title="Album",
                album_artist="' UNION SELECT password FROM users--",
                num_tracks=10,
                path="/path",
            )
        assert "suspicious SQL patterns" in str(exc.value)


class TestTrackMetadataModelSanitization:
    """Test TrackMetadataModel sanitizes track metadata."""

    def test_normal_track_data(self):
        """Test that normal track data passes validation."""
        data = {
            "parent_oid": 920,
            "title": "Track Title",
            "artist": "Track Artist",
            "duration": 180000,
            "track": 1,
            "filename": "track01.mp3",
        }
        model = TrackMetadataModel(**data)
        assert model.title == "Track Title"
        assert model.artist == "Track Artist"

    def test_sql_injection_in_track_title(self):
        """Test that SQL injection in track title is rejected."""
        with pytest.raises(ValidationError) as exc:
            TrackMetadataModel(
                parent_oid=920,
                title="Track'; DROP TABLE tracks; --",
                duration=180000,
                track=1,
                filename="track.mp3",
            )
        assert "suspicious SQL patterns" in str(exc.value)

    def test_sql_injection_in_track_artist(self):
        """Test that SQL injection in track artist is rejected."""
        with pytest.raises(ValidationError) as exc:
            TrackMetadataModel(
                parent_oid=920,
                title="Track",
                artist="' OR 1=1--",
                duration=180000,
                track=1,
                filename="track.mp3",
            )
        assert "suspicious SQL patterns" in str(exc.value)

    def test_lyrics_with_safe_html(self):
        """Test that lyrics can contain safe HTML formatting."""
        data = {
            "parent_oid": 920,
            "title": "Track",
            "lyrics": "<b>Verse 1</b><br>Line 1<br>Line 2",
            "duration": 180000,
            "track": 1,
            "filename": "track.mp3",
        }
        model = TrackMetadataModel(**data)
        # Basic tags should be allowed in lyrics
        assert "Verse 1" in model.lyrics

    def test_lyrics_with_malicious_script(self):
        """Test that malicious scripts in lyrics are removed."""
        data = {
            "parent_oid": 920,
            "title": "Track",
            "lyrics": "<script>alert('xss')</script>Lyrics",
            "duration": 180000,
            "track": 1,
            "filename": "track.mp3",
        }
        model = TrackMetadataModel(**data)
        # Script should be removed
        assert "<script>" not in model.lyrics


class TestDBHandlerSQLInjectionProtection:
    """Test DBHandler methods prevent SQL injection."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = DBHandler(str(db_path))
            db.initialize()
            yield db
            db.close()

    def test_write_to_database_with_valid_data(self, temp_db):
        """Test that write_to_database works with valid data."""
        data = {
            "oid": 920,
            "album_title": "Test Album",
            "album_artist": "Test Artist",
            "num_tracks": 10,
            "path": "/test/path",
        }
        temp_db.write_to_database("gme_library", data)

        # Verify data was written
        result = temp_db.fetchone("SELECT * FROM gme_library WHERE oid=?", (920,))
        assert result["album_title"] == "Test Album"

    def test_write_to_database_with_invalid_table(self, temp_db):
        """Test that write_to_database rejects invalid table names."""
        with pytest.raises(ValueError) as exc:
            temp_db.write_to_database("malicious_table", {"field": "value"})
        assert "Invalid table name" in str(exc.value)

    def test_write_to_database_with_invalid_column(self, temp_db):
        """Test that write_to_database rejects invalid column names."""
        with pytest.raises(ValueError) as exc:
            temp_db.write_to_database(
                "gme_library", {"oid": 920, "malicious_column": "value"}
            )
        assert "Invalid column name" in str(exc.value)

    def test_write_to_database_with_sql_injection_in_column(self, temp_db):
        """Test that column names with SQL injection are rejected."""
        with pytest.raises(ValueError):
            temp_db.write_to_database("gme_library", {"oid; DROP TABLE users--": 920})

    def test_update_table_entry_with_valid_data(self, temp_db):
        """Test that update_table_entry works with valid data."""
        # First insert data
        temp_db.write_to_database(
            "gme_library",
            {
                "oid": 920,
                "album_title": "Old Title",
                "num_tracks": 10,
                "path": "/test",
            },
        )

        # Update data
        temp_db.update_table_entry(
            "gme_library", "oid=?", [920], {"album_title": "New Title"}
        )

        # Verify update
        result = temp_db.fetchone("SELECT * FROM gme_library WHERE oid=?", (920,))
        assert result["album_title"] == "New Title"

    def test_update_table_entry_with_invalid_table(self, temp_db):
        """Test that update_table_entry rejects invalid table names."""
        with pytest.raises(ValueError) as exc:
            temp_db.update_table_entry(
                "malicious_table", "oid=?", [920], {"field": "value"}
            )
        assert "Invalid table name" in str(exc.value)

    def test_update_table_entry_with_invalid_column(self, temp_db):
        """Test that update_table_entry rejects invalid column names."""
        with pytest.raises(ValueError) as exc:
            temp_db.update_table_entry(
                "gme_library", "oid=?", [920], {"malicious_column": "value"}
            )
        assert "Invalid column name" in str(exc.value)


class TestConfigUpdateModelSanitization:
    """Test ConfigUpdateModel sanitizes configuration input."""

    def test_normal_config_update(self):
        """Test that normal config data passes validation."""
        data = {
            "host": "localhost",
            "port": 10020,
            "pen_language": "ENGLISH",
        }
        model = ConfigUpdateModel(**data)
        assert model.host == "localhost"
        assert model.port == 10020
        assert model.pen_language == "ENGLISH"

    def test_sql_injection_in_pen_language(self):
        """Test that SQL injection in pen_language is rejected."""
        with pytest.raises(ValidationError) as exc:
            ConfigUpdateModel(pen_language="ENGLISH'; DROP TABLE config; --")
        assert "suspicious SQL patterns" in str(exc.value)

    def test_sql_injection_in_library_path(self):
        """Test that SQL injection in library_path is rejected."""
        with pytest.raises(ValidationError) as exc:
            ConfigUpdateModel(library_path="/path'; DELETE FROM config; --")
        assert "suspicious SQL patterns" in str(exc.value)
