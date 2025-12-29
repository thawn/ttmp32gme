"""Unit tests for library_handler module."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from ttmp32gme.library_handler import (
    oid_exist,
    new_oid,
    cleanup_filename,
    get_cover_filename,
)


class TestLibraryHandler:
    """Test library handler functions."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Create tables
        cursor.execute(
            """
            CREATE TABLE gme_library (
                oid INTEGER PRIMARY KEY,
                album_title TEXT,
                path TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE tracks (
                parent_oid INTEGER,
                track INTEGER,
                title TEXT
            )
        """
        )
        conn.commit()

        yield conn

        conn.close()
        db_path.unlink()

    def test_oid_exist(self, temp_db):
        """Test checking if OID exists."""
        cursor = temp_db.cursor()
        cursor.execute(
            'INSERT INTO gme_library (oid, album_title, path) VALUES (920, "Test", "/test")'
        )
        temp_db.commit()

        assert oid_exist(920, temp_db) is True
        assert oid_exist(921, temp_db) is False

    def test_new_oid_empty_db(self, temp_db):
        """Test generating new OID in empty database."""
        oid = new_oid(temp_db)
        assert oid == 920

    def test_new_oid_sequential(self, temp_db):
        """Test sequential OID generation."""
        cursor = temp_db.cursor()
        cursor.execute(
            'INSERT INTO gme_library (oid, album_title, path) VALUES (920, "Test1", "/test1")'
        )
        cursor.execute(
            'INSERT INTO gme_library (oid, album_title, path) VALUES (921, "Test2", "/test2")'
        )
        temp_db.commit()

        oid = new_oid(temp_db)
        assert oid == 922

    def test_get_cover_filename_with_mimetype(self):
        """Test cover filename generation with MIME type."""
        result = get_cover_filename("image/jpeg", b"fake_data")
        assert result == "cover.jpeg"

        result = get_cover_filename("image/png", b"fake_data")
        assert result == "cover.png"

    def test_get_cover_filename_no_mimetype(self):
        """Test cover filename generation without MIME type."""
        result = get_cover_filename(None, None)
        assert result is None
