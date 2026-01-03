"""Unit tests for print_handler module."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from ttmp32gme.db_handler import DBHandler
from ttmp32gme.print_handler import (
    create_pdf,
    create_print_layout,
    format_controls,
    format_cover,
    format_main_oid,
    format_print_button,
    format_track_control,
    format_tracks,
)


class TestFormatTracks:
    """Test format_tracks function."""

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

    @patch("ttmp32gme.print_handler.get_sorted_tracks")
    @patch("ttmp32gme.print_handler.create_oids")
    def test_format_tracks_basic(self, mock_create_oids, mock_get_sorted_tracks, db):
        """Test basic track formatting."""
        # Setup mocks
        mock_get_sorted_tracks.return_value = ["track_1"]
        mock_oid_file = Mock()
        mock_oid_file.name = "oid_2663.png"
        mock_create_oids.return_value = [mock_oid_file]

        album = {
            "track_1": {
                "title": "Test Track",
                "duration": 180000,  # 3 minutes
                "tt_script": "t0",
            }
        }
        oid_map = {"t0": {"code": 2663}}

        result = format_tracks(album, oid_map, db)

        assert "Test Track" in result
        assert "03:00" in result
        assert "oid_2663.png" in result
        assert '<li class="list-group-item">' in result

    @patch("ttmp32gme.print_handler.get_sorted_tracks")
    @patch("ttmp32gme.print_handler.create_oids")
    def test_format_tracks_multiple(self, mock_create_oids, mock_get_sorted_tracks, db):
        """Test formatting multiple tracks."""
        mock_get_sorted_tracks.return_value = ["track_1", "track_2"]

        def create_oids_side_effect(oids, *args):
            return [Mock(spec=["name"], **{"name": f"oid_{oid}.png"}) for oid in oids]

        mock_create_oids.side_effect = create_oids_side_effect

        album = {
            "track_1": {"title": "Track 1", "duration": 120000, "tt_script": "t0"},
            "track_2": {"title": "Track 2", "duration": 180000, "tt_script": "t1"},
        }
        oid_map = {"t0": {"code": 2663}, "t1": {"code": 2664}}

        result = format_tracks(album, oid_map, db)

        assert "Track 1" in result
        assert "Track 2" in result
        assert result.count('<li class="list-group-item">') == 2

    @patch("ttmp32gme.print_handler.get_sorted_tracks")
    @patch("ttmp32gme.print_handler.create_oids")
    def test_format_tracks_with_none_tt_script(
        self, mock_create_oids, mock_get_sorted_tracks, db
    ):
        """Test track formatting when tt_script is None (before GME generation)."""
        mock_get_sorted_tracks.return_value = ["track_1", "track_2"]

        def create_oids_side_effect(oids, *args):
            return [Mock(spec=["name"], **{"name": f"oid_{oid}.png"}) for oid in oids]

        mock_create_oids.side_effect = create_oids_side_effect

        # Tracks with None tt_script (before GME is generated)
        album = {
            "track_1": {"title": "Track 1", "duration": 120000, "tt_script": None},
            "track_2": {"title": "Track 2", "duration": 180000, "tt_script": None},
        }
        oid_map = {"t0": {"code": 2663}, "t1": {"code": 2664}}

        result = format_tracks(album, oid_map, db)

        # Should fall back to t0, t1 based on index
        assert "Track 1" in result
        assert "Track 2" in result
        assert "oid_2663.png" in result  # t0 -> 2663
        assert "oid_2664.png" in result  # t1 -> 2664
        # Verify create_oids was called with correct codes (not 0)
        calls = mock_create_oids.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == [2663]  # First track: code 2663
        assert calls[1][0][0] == [2664]  # Second track: code 2664


class TestFormatControls:
    """Test format_controls function."""

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

    @patch("ttmp32gme.print_handler.create_oids")
    def test_format_controls(self, mock_create_oids, db):
        """Test playback controls formatting."""
        mock_oid_files = [Mock(name=f"oid_{i}.png") for i in range(4)]
        mock_create_oids.return_value = mock_oid_files

        oid_map = {
            "prev": {"code": 3945},
            "play": {"code": 3947},
            "stop": {"code": 3948},
            "next": {"code": 3949},
        }

        result = format_controls(oid_map, db)

        assert "glyphicon-backward" in result
        assert "glyphicon-play" in result
        assert "glyphicon-stop" in result
        assert "glyphicon-forward" in result
        assert result.count("btn btn-default play-control") == 4


class TestFormatTrackControl:
    """Test format_track_control function."""

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

    @patch("ttmp32gme.print_handler.create_oids")
    def test_format_track_control(self, mock_create_oids, db):
        """Test single track control formatting."""
        mock_oid_file = Mock()
        mock_oid_file.name = "oid_2663.png"
        mock_create_oids.return_value = [mock_oid_file]

        oid_map = {"t0": {"code": 2663}}

        result = format_track_control(1, oid_map, db)

        assert "oid_2663.png" in result
        assert ">1</a>" in result
        assert "btn btn-default play-control" in result


class TestFormatMainOid:
    """Test format_main_oid function."""

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

    @patch("ttmp32gme.print_handler.create_oids")
    def test_format_main_oid(self, mock_create_oids, db):
        """Test main OID image formatting."""
        mock_oid_file = Mock()
        mock_oid_file.name = "oid_920.png"
        mock_create_oids.return_value = [mock_oid_file]

        result = format_main_oid(920, db)

        assert "oid_920.png" in result
        assert 'alt="oid: 920"' in result
        assert '<img class="img-24mm play-img"' in result


class TestFormatCover:
    """Test format_cover function."""

    def test_format_cover_with_image(self):
        """Test cover formatting when image exists."""
        album = {"oid": 920, "picture_filename": "cover.jpg"}

        result = format_cover(album)

        assert "cover.jpg" in result
        assert "/images/920/" in result
        assert '<img class="img-responsive cover-img"' in result

    def test_format_cover_without_image(self):
        """Test cover formatting when no image exists."""
        album = {"oid": 920}

        result = format_cover(album)

        assert result == ""


class TestCreatePrintLayout:
    """Test create_print_layout function."""

    @pytest.fixture
    def db(self):
        """Create a temporary database with album data."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_handler = DBHandler(db_path)
        db_handler.initialize()

        # Add test album
        db_handler.write_to_database(
            "gme_library",
            {
                "oid": 920,
                "album_title": "Test Album",
                "num_tracks": 1,
                "path": "/tmp/test",
                "gme_file": "test.gme",
            },
        )

        # Add test track
        db_handler.write_to_database(
            "tracks",
            {
                "parent_oid": 920,
                "title": "Test Track",
                "track": 1,
                "duration": 180000,
                "filename": "test.mp3",
            },
        )

        # Add script codes - use UPDATE OR INSERT to avoid constraint failures
        for script, code in [("play", 3947), ("t0", 2663)]:
            try:
                db_handler.write_to_database(
                    "script_codes", {"script": script, "code": code}
                )
            except sqlite3.IntegrityError:
                # Already exists, update it
                db_handler.execute(
                    "UPDATE script_codes SET code=? WHERE script=?", (code, script)
                )
                db_handler.commit()

        yield db_handler

        db_handler.close()
        Path(db_path).unlink(missing_ok=True)

    @patch("ttmp32gme.print_handler.render_template")
    @patch("ttmp32gme.print_handler.create_oids")
    @patch("ttmp32gme.print_handler.get_sorted_tracks")
    def test_create_print_layout_basic(
        self, mock_get_sorted_tracks, mock_create_oids, mock_render_template, db
    ):
        """Test basic print layout creation."""
        mock_get_sorted_tracks.return_value = ["track_1"]
        mock_oid_file = Mock()
        mock_oid_file.name = "oid_test.png"
        mock_create_oids.return_value = [mock_oid_file]
        mock_render_template.return_value = "<div>Album Content</div>"

        config = {"print_max_track_controls": 12}

        result = create_print_layout([920], None, config, db)

        assert "<div>Album Content</div>" in result
        assert "general-controls" in result
        assert mock_render_template.called


class TestCreatePdf:
    """Test create_pdf function."""

    @patch("ttmp32gme.print_handler.fcntl.fcntl")
    @patch("ttmp32gme.print_handler.time.sleep")
    @patch("ttmp32gme.print_handler.get_executable_path")
    @patch("ttmp32gme.print_handler.subprocess.Popen")
    def test_create_pdf_success(
        self, mock_popen, mock_get_exec, mock_sleep, mock_fcntl
    ):
        """Test PDF creation with chromium available."""
        mock_get_exec.return_value = "/usr/bin/chromium"

        # Mock the process - poll() returns None (still running)
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stderr.read.return_value = ""  # No errors in stderr
        mock_popen.return_value = mock_process

        with tempfile.TemporaryDirectory() as tmpdir:
            library_path = Path(tmpdir)

            result = create_pdf(10020, library_path)

            assert result is not None
            assert result == library_path / "print.pdf"
            assert mock_popen.called
            # Verify chromium headless arguments
            call_args = mock_popen.call_args[0][0]
            assert "--headless" in call_args
            assert "--no-pdf-header-footer" in call_args

    @patch("ttmp32gme.print_handler.get_executable_path")
    def test_create_pdf_no_chromium(self, mock_get_exec):
        """Test PDF creation when chromium not found."""
        mock_get_exec.return_value = None

        result = create_pdf(10020)

        assert result is None

    @patch("ttmp32gme.print_handler.get_executable_path")
    @patch("ttmp32gme.print_handler.subprocess.Popen")
    def test_create_pdf_exception(self, mock_popen, mock_get_exec):
        """Test PDF creation when subprocess fails."""
        mock_get_exec.return_value = "/usr/bin/chromium"
        mock_popen.side_effect = Exception("Test error")

        result = create_pdf(10020)

        assert result is None

    @patch("ttmp32gme.print_handler.fcntl.fcntl")
    @patch("ttmp32gme.print_handler.time.sleep")
    @patch("ttmp32gme.print_handler.get_executable_path")
    @patch("ttmp32gme.print_handler.subprocess.Popen")
    def test_create_pdf_tries_multiple_names(
        self, mock_popen, mock_get_exec, mock_sleep, mock_fcntl
    ):
        """Test PDF creation tries multiple chromium binary names."""
        # First call returns None (chromium), second returns path (chromium-browser)
        mock_get_exec.side_effect = [None, "/usr/bin/chromium-browser"]

        # Mock the process - poll() returns None (still running)
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stderr.read.return_value = ""  # No errors in stderr
        mock_popen.return_value = mock_process

        with tempfile.TemporaryDirectory() as tmpdir:
            library_path = Path(tmpdir)

            result = create_pdf(10020, library_path)

            assert result is not None
            assert result == library_path / "print.pdf"
            assert mock_popen.called


class TestFormatPrintButton:
    """Test format_print_button function."""

    @patch("ttmp32gme.print_handler.platform.system")
    def test_format_print_button_windows(self, mock_system):
        """Test print button on Windows."""
        mock_system.return_value = "Windows"

        result = format_print_button()

        assert "Save as PDF</button>" in result
        assert 'id="pdf-save"' in result

    @patch("ttmp32gme.print_handler.platform.system")
    @patch("ttmp32gme.print_handler.get_executable_path")
    def test_format_print_button_linux_no_chromium(self, mock_get_exec, mock_system):
        """Test print button on Linux without chromium."""
        mock_system.return_value = "Linux"
        mock_get_exec.return_value = None

        result = format_print_button()

        assert "Print This Page</button>" in result
        assert "Save as PDF" not in result

    @patch("ttmp32gme.print_handler.platform.system")
    @patch("ttmp32gme.print_handler.get_executable_path")
    def test_format_print_button_linux_with_chromium(self, mock_get_exec, mock_system):
        """Test print button on Linux with chromium available."""
        mock_system.return_value = "Linux"
        mock_get_exec.return_value = "/usr/bin/chromium"

        result = format_print_button()

        assert "Print This Page</button>" in result
        assert "Save as PDF</button>" in result
