"""Unit tests for Unicode/encoding fix in legacy databases."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from ttmp32gme.db_handler import DBHandler


class TestUnicodeFix:
    """Test Unicode encoding fixes for legacy Perl databases."""

    @pytest.fixture
    def legacy_db(self):
        """Create a database with encoding issues similar to legacy Perl databases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "legacy.db")

            # Create a fresh database
            db = DBHandler(db_path)
            db.initialize()
            db.close()

            # Now corrupt it by inserting non-UTF-8 data using raw SQLite
            # This simulates what legacy Perl code might have done
            conn = sqlite3.connect(db_path)

            # Disable text encoding to insert raw bytes
            conn.text_factory = bytes
            cursor = conn.cursor()

            # Insert album with Latin-1 encoded German text (like "erklärt" and "Körper")
            # Latin-1 bytes for "Albert E erklärt den menschlichen Körper"
            # 'ä' in Latin-1 is 0xE4, 'ö' is 0xF6
            bad_title = b"Albert E erkl\xe4rt den menschlichen K\xf6rper"
            bad_artist = b"Test Artist with \xfcmlaut"  # 'ü' in Latin-1 is 0xFC

            cursor.execute(
                "INSERT INTO gme_library (oid, album_title, album_artist, num_tracks, path) VALUES (?, ?, ?, ?, ?)",
                (920, bad_title, bad_artist, 1, b"/tmp/test"),
            )

            # Insert track with encoding issues
            bad_track_title = (
                b"Track with special chars \xe4\xf6\xfc\xdf"  # äöüß in Latin-1
            )
            cursor.execute(
                "INSERT INTO tracks (parent_oid, title, track, duration, filename) VALUES (?, ?, ?, ?, ?)",
                (920, bad_track_title, 1, 180000, b"track01.mp3"),
            )

            conn.commit()
            cursor.close()
            conn.close()

            yield db_path

    def test_read_legacy_db_without_fix_returns_garbage(self, legacy_db):
        """Test that reading legacy DB with encoding issues returns incorrect data.

        Note: SQLite 3 may not always raise an error with invalid UTF-8, but the data
        will be corrupted/incorrect. This test verifies the data is wrong before fixing.
        """
        db = DBHandler(legacy_db)
        db.connect()

        # Try to read the album - may not raise error but data will be wrong
        album = db.get_album(920)

        # The title should NOT match the correct German text before fixing
        # because the Latin-1 bytes were interpreted as something else
        correct_title = "Albert E erklärt den menschlichen Körper"

        # Either we get an error, or we get corrupted data
        if album is not None:
            # Data is readable but corrupted
            assert (
                album["album_title"] != correct_title
            ), "Title should be corrupted before fix"

        db.close()

    def test_fix_text_encoding_fixes_gme_library(self, legacy_db):
        """Test that _fix_text_encoding fixes gme_library table."""
        db = DBHandler(legacy_db)
        db.connect()

        # Fix the encoding
        fixed_count = db._fix_text_encoding(
            "gme_library",
            "oid",
            ["album_title", "album_artist", "picture_filename", "gme_file", "path"],
        )
        db.commit()

        # Should have fixed 1 row
        assert fixed_count == 1

        # Now reading should work
        album = db.get_album(920)
        assert album is not None
        assert "Albert E erklärt den menschlichen Körper" in album["album_title"]
        assert "ümlaut" in album["album_artist"]

        db.close()

    def test_fix_text_encoding_fixes_tracks(self, legacy_db):
        """Test that _fix_text_encoding fixes tracks table."""
        db = DBHandler(legacy_db)
        db.connect()

        # First fix gme_library so we can read albums
        db._fix_text_encoding(
            "gme_library",
            "oid",
            ["album_title", "album_artist", "picture_filename", "gme_file", "path"],
        )

        # Fix tracks
        fixed_count = db._fix_text_encoding(
            "tracks",
            "rowid",
            ["album", "artist", "genre", "lyrics", "title", "filename", "tt_script"],
        )
        db.commit()

        # Should have fixed 1 row
        assert fixed_count == 1

        # Now reading should work
        album = db.get_album(920)
        assert album is not None
        track = album.get("track_1")
        assert track is not None
        assert "äöüß" in track["title"]

        db.close()

    def test_update_db_fixes_encoding_for_version_2_0_1(self, legacy_db):
        """Test that update_db fixes encoding issues when upgrading to 2.0.1."""
        db = DBHandler(legacy_db)
        db.connect()

        # Set version to 2.0.0 to trigger 2.0.1 update
        db.execute("UPDATE config SET value='2.0.0' WHERE param='version'")
        db.commit()

        # Run update_db
        result = db.update_db()
        assert result is True

        # Verify version was updated
        version = db.get_config_value("version")
        assert version == "2.0.1"

        # Verify data can now be read
        album = db.get_album(920)
        assert album is not None
        assert "Albert E erklärt den menschlichen Körper" in album["album_title"]

        # Verify track data
        track = album.get("track_1")
        assert track is not None
        assert "äöüß" in track["title"]

        db.close()

    def test_fix_text_encoding_handles_null_values(self):
        """Test that _fix_text_encoding handles NULL values correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            db = DBHandler(db_path)
            db.initialize()

            # Insert album with NULL artist
            db.execute(
                "INSERT INTO gme_library (oid, album_title, album_artist, num_tracks, path) VALUES (?, ?, ?, ?, ?)",
                (920, "Test Album", None, 0, "/tmp/test"),
            )
            db.commit()

            # Fix encoding - should not crash on NULL
            fixed_count = db._fix_text_encoding(
                "gme_library", "oid", ["album_title", "album_artist"]
            )
            db.commit()

            # Should have fixed 0 rows (no encoding issues)
            assert fixed_count == 0

            # Verify data is still readable
            album = db.get_album(920)
            assert album is not None
            assert album["album_title"] == "Test Album"
            assert album["album_artist"] is None

            db.close()

    def test_fix_text_encoding_handles_already_valid_utf8(self):
        """Test that _fix_text_encoding doesn't break valid UTF-8 data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            db = DBHandler(db_path)
            db.initialize()

            # Insert album with proper UTF-8
            good_title = "Albert E erklärt den menschlichen Körper"
            db.execute(
                "INSERT INTO gme_library (oid, album_title, album_artist, num_tracks, path) VALUES (?, ?, ?, ?, ?)",
                (920, good_title, "Good Artist", 0, "/tmp/test"),
            )
            db.commit()

            # Fix encoding - should detect no issues
            fixed_count = db._fix_text_encoding(
                "gme_library", "oid", ["album_title", "album_artist"]
            )
            db.commit()

            # Should have fixed 0 rows (already valid UTF-8)
            assert fixed_count == 0

            # Verify data is unchanged
            album = db.get_album(920)
            assert album is not None
            assert album["album_title"] == good_title

            db.close()
