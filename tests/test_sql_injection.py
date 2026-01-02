"""Tests for SQL injection vulnerabilities."""

import tempfile
from pathlib import Path

import pytest

from ttmp32gme.db_handler import DBHandler


class TestSQLInjection:
    """Test SQL injection vulnerabilities in database operations."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sqlite", delete=False) as f:
            db_path = f.name

        db = DBHandler(db_path)
        db.initialize()
        yield db
        db.close()
        Path(db_path).unlink(missing_ok=True)

    def test_write_to_database_field_injection(self, temp_db):
        """Test that malicious field names cannot inject SQL."""
        # Attempt to inject SQL via field name
        malicious_data = {
            "oid": 920,
            "album_title": "Test Album",
            "num_tracks": 1,
            "path": "/test",
            # Attempt SQL injection via field name
            "album_artist' OR '1'='1": "malicious",
        }

        # This should raise a ValueError due to invalid field name
        with pytest.raises(ValueError, match="Invalid field names"):
            temp_db.write_to_database("gme_library", malicious_data)

    def test_update_table_entry_field_injection(self, temp_db):
        """Test that malicious field names in updates cannot inject SQL."""
        # First, create a valid album
        valid_data = {
            "oid": 920,
            "album_title": "Test Album",
            "num_tracks": 1,
            "path": "/test",
        }
        temp_db.write_to_database("gme_library", valid_data)
        temp_db.commit()

        # Attempt to inject SQL via field name in update
        malicious_update = {
            "album_title": "Updated Title",
            # Attempt SQL injection via field name
            "album_artist' OR '1'='1": "malicious",
        }

        # This should raise a ValueError due to invalid field name
        with pytest.raises(ValueError, match="Invalid field names"):
            temp_db.update_table_entry("gme_library", "oid=?", [920], malicious_update)

    def test_album_update_with_malicious_fields(self, temp_db):
        """Test that album updates reject malicious field names."""
        from ttmp32gme.db_handler import AlbumUpdateModel

        # Create a test album first
        valid_data = {
            "oid": 920,
            "album_title": "Test Album",
            "num_tracks": 1,
            "path": "/test",
        }
        temp_db.write_to_database("gme_library", valid_data)
        temp_db.commit()

        # Attempt to inject SQL via field names through the Pydantic model
        malicious_input = {
            "oid": 920,
            "album_title": "Updated Title",
            # Try to inject via field name
            "album_artist'; DROP TABLE gme_library; --": "attacker",
        }

        # Pydantic allows this due to extra="allow"
        validated = AlbumUpdateModel(**malicious_input)
        validated_dict = validated.model_dump(exclude_none=True)

        # The update should raise ValueError due to invalid field name
        with pytest.raises(ValueError, match="Invalid field names"):
            temp_db.update_table_entry("gme_library", "oid=?", [920], validated_dict)

    def test_metadata_extraction_sql_injection(self, temp_db):
        """Test that metadata from audio files cannot inject SQL."""
        # This tests the scenario where malicious ID3 tags are in audio files
        # We simulate the data that would come from malicious ID3 tags
        malicious_album_data = {
            "oid": 920,
            "album_title": "'; DROP TABLE gme_library; --",
            "album_artist": "Artist'; DELETE FROM tracks WHERE '1'='1",
            "num_tracks": 1,
            "path": "/test/path",
        }

        # This data should be written safely
        temp_db.write_to_database("gme_library", malicious_album_data)
        temp_db.commit()

        # Verify the table still exists and contains the data
        albums = temp_db.fetchall("SELECT * FROM gme_library")
        assert len(albums) == 1
        assert albums[0]["album_title"] == "'; DROP TABLE gme_library; --"

        # Verify tracks table still exists
        tracks = temp_db.fetchall("SELECT * FROM tracks")
        assert isinstance(tracks, list)  # Table should still exist

    def test_value_injection_is_prevented(self, temp_db):
        """Test that values are properly parameterized and cannot inject SQL."""
        malicious_data = {
            "oid": 920,
            "album_title": "Test' OR '1'='1",  # SQL injection in value
            "album_artist": "'); DROP TABLE tracks; --",  # SQL injection in value
            "num_tracks": 1,
            "path": "/test",
        }

        # Values should be safely parameterized
        temp_db.write_to_database("gme_library", malicious_data)
        temp_db.commit()

        # Verify the malicious strings were stored as literal values
        album = temp_db.fetchone("SELECT * FROM gme_library WHERE oid=?", (920,))
        assert album["album_title"] == "Test' OR '1'='1"
        assert album["album_artist"] == "'); DROP TABLE tracks; --"

        # Verify tracks table still exists
        tracks = temp_db.fetchall("SELECT * FROM tracks")
        assert isinstance(tracks, list)

    def test_invalid_table_name_rejected(self, temp_db):
        """Test that invalid table names are rejected."""
        malicious_data = {
            "id": 1,
            "value": "test",
        }

        # Attempt to use a non-whitelisted table name
        with pytest.raises(ValueError, match="Invalid table name"):
            temp_db.write_to_database("malicious_table", malicious_data)

        # Attempt SQL injection via table name
        with pytest.raises(ValueError, match="Invalid table name"):
            temp_db.write_to_database(
                "gme_library; DROP TABLE tracks; --", malicious_data
            )

    def test_valid_operations_still_work(self, temp_db):
        """Test that valid database operations still work after security fixes."""
        # Insert valid data
        valid_data = {
            "oid": 920,
            "album_title": "Test Album",
            "album_artist": "Test Artist",
            "num_tracks": 2,
            "path": "/test/path",
        }
        temp_db.write_to_database("gme_library", valid_data)
        temp_db.commit()

        # Verify insertion
        album = temp_db.fetchone("SELECT * FROM gme_library WHERE oid=?", (920,))
        assert album is not None
        assert album["album_title"] == "Test Album"
        assert album["album_artist"] == "Test Artist"

        # Update valid data
        update_data = {
            "album_title": "Updated Album",
            "num_tracks": 3,
        }
        temp_db.update_table_entry("gme_library", "oid=?", [920], update_data)
        temp_db.commit()

        # Verify update
        album = temp_db.fetchone("SELECT * FROM gme_library WHERE oid=?", (920,))
        assert album["album_title"] == "Updated Album"
        assert album["num_tracks"] == 3
