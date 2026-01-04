"""Integration test for print_handler with None tt_script values."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ttmp32gme.db_handler import DBHandler
from ttmp32gme.print_handler import format_tracks


class TestFormatTracksIntegration:
    """Integration tests for format_tracks with real database."""

    @pytest.fixture
    def db_with_tracks(self):
        """Create a database with tracks that have None tt_script."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db = DBHandler(db_path)
        db.initialize()

        # Insert album
        db.write_to_database(
            table="gme_library",
            data={
                "oid": 920,
                "album_title": "Test Album",
                "num_tracks": 3,
                "path": "/tmp/test",
            },
        )

        # Insert tracks with None tt_script (simulating pre-GME state)
        for i in range(3):
            db.write_to_database(
                table="tracks",
                data={
                    "parent_oid": 920,
                    "title": f"Track {i + 1}",
                    "track": i + 1,
                    "duration": 180000,
                    "filename": f"track{i + 1}.mp3",
                    "tt_script": None,
                },
            )

        db.commit()

        yield db

        db.close()
        Path(db_path).unlink(missing_ok=True)

    @patch("ttmp32gme.print_handler.create_oids")
    def test_format_tracks_with_real_db_none_tt_script(
        self, mock_create_oids, db_with_tracks
    ):
        """Test format_tracks with real database where tt_script is None."""

        # Mock create_oids to avoid calling tttool
        def create_oids_side_effect(oids, *args):
            return [
                Mock(spec=["name"], **{"name": f"{oid}-24-1200-2.png"}) for oid in oids
            ]

        mock_create_oids.side_effect = create_oids_side_effect

        # Get album from database
        album = db_with_tracks.get_album(920)

        # Build oid_map from script_codes table
        script_codes = db_with_tracks.fetchall("SELECT script, code FROM script_codes")
        oid_map = {row[0]: {"code": row[1]} for row in script_codes}

        # Format tracks
        result = format_tracks(album, oid_map, db_with_tracks)

        # Verify tracks are rendered with correct OID codes
        assert "Track 1" in result
        assert "Track 2" in result
        assert "Track 3" in result

        # Verify OID codes are NOT 0 (the bug we're fixing)
        assert (
            "0-24-1200-2.png" not in result
        ), "Bug: OID code is 0 instead of correct code"

        # Verify correct OID codes are used (t0=2663, t1=2664, t2=2665)
        assert "2663-24-1200-2.png" in result, "Expected t0 code 2663"
        assert "2664-24-1200-2.png" in result, "Expected t1 code 2664"
        assert "2665-24-1200-2.png" in result, "Expected t2 code 2665"
