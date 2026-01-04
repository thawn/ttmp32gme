"""Unit tests for tttool_handler module."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ttmp32gme.db_handler import DBHandler
from ttmp32gme.tttool_handler import (
    generate_codes_yaml,
    get_sorted_tracks,
    get_tttool_command,
    get_tttool_parameters,
    run_tttool,
)


class TestGetSortedTracks:
    """Test get_sorted_tracks function."""

    def test_get_sorted_tracks_basic(self):
        """Test basic track sorting."""
        album = {
            "track_3": {"title": "Track 3"},
            "track_1": {"title": "Track 1"},
            "track_2": {"title": "Track 2"},
            "album_title": "Test Album",
        }

        result = get_sorted_tracks(album)

        assert result == ["track_1", "track_2", "track_3"]

    def test_get_sorted_tracks_with_gaps(self):
        """Test track sorting with non-sequential numbers."""
        album = {
            "track_10": {"title": "Track 10"},
            "track_2": {"title": "Track 2"},
            "track_5": {"title": "Track 5"},
        }

        result = get_sorted_tracks(album)

        assert result == ["track_2", "track_5", "track_10"]

    def test_get_sorted_tracks_empty(self):
        """Test with no tracks."""
        album = {"album_title": "Test Album"}

        result = get_sorted_tracks(album)

        assert result == []


class TestGetTttoolParameters:
    """Test get_tttool_parameters function."""

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

    def test_get_tttool_parameters_basic(self, db: DBHandler):
        """Test retrieving tttool parameters."""
        # Add some tt_ parameters
        db.set_config_value("tt_dpi", "1200")
        db.set_config_value("tt_pixel-size", "2")

        result = get_tttool_parameters(db)

        assert "dpi" in result
        assert result["dpi"] == "1200"
        assert "pixel-size" in result
        assert result["pixel-size"] == "2"

    def test_get_tttool_parameters_empty(self, db: DBHandler):
        """Test with no tt_ parameters."""
        db.execute_and_commit("DELETE FROM config WHERE param LIKE 'tt_%'")

        result = get_tttool_parameters(db)

        assert result == {}


class TestGetTttoolCommand:
    """Test get_tttool_command function."""

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

    @patch("ttmp32gme.tttool_handler.get_executable_path")
    def test_get_tttool_command_basic(self, mock_get_exec, db):
        """Test building tttool command."""
        mock_get_exec.return_value = "/usr/bin/tttool"

        # Add some parameters
        db.execute_and_commit("UPDATE config SET value='1200' WHERE param='tt_dpi'")

        result = get_tttool_command(db)

        assert result[0] == "/usr/bin/tttool"
        assert "--dpi" in result
        assert "1200" in result

    @patch("ttmp32gme.tttool_handler.get_executable_path")
    def test_get_tttool_command_not_found(self, mock_get_exec, db):
        """Test when tttool is not found."""
        mock_get_exec.return_value = None

        with pytest.raises(RuntimeError, match="tttool not found"):
            get_tttool_command(db)


class TestGenerateCodesYaml:
    """Test generate_codes_yaml function."""

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

    def test_generate_codes_yaml_basic(self, db):
        """Test generating codes YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "album.yaml"

            # Create a simple YAML file with scripts
            yaml_file.write_text(
                """
product-id: 920
scripts:
  play:
  - P(0) C
  next:
  - P(1) C
"""
            )

            result = generate_codes_yaml(yaml_file, db)

            assert result.exists()
            assert result.name == "album.codes.yaml"

            # Check contents
            content = result.read_text()
            assert "scriptcodes:" in content
            assert "play:" in content
            assert "next:" in content

    def test_generate_codes_yaml_reuses_existing(self, db):
        """Test that existing codes are reused."""
        # Add existing code - delete first in case it exists
        db.execute_and_commit("DELETE FROM script_codes WHERE script='play'")
        db.execute_and_commit(
            "INSERT INTO script_codes (script, code) VALUES ('play', 2000)"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "album.yaml"
            yaml_file.write_text(
                """
scripts:
  play:
  - P(0) C
"""
            )

            result = generate_codes_yaml(yaml_file, db)

            content = result.read_text()
            assert "play: 2000" in content


class TestRunTttool:
    """Test run_tttool function."""

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

    @patch("ttmp32gme.tttool_handler.get_tttool_command")
    @patch("ttmp32gme.tttool_handler.subprocess.run")
    def test_run_tttool_success(self, mock_run, mock_get_cmd, db):
        """Test successful tttool execution."""
        mock_get_cmd.return_value = ["/usr/bin/tttool"]
        mock_result = Mock()
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_tttool("assemble album.yaml", None, db)

        assert result is True
        assert mock_run.called

    @patch("ttmp32gme.tttool_handler.get_tttool_command")
    @patch("ttmp32gme.tttool_handler.subprocess.run")
    def test_run_tttool_failure(self, mock_run, mock_get_cmd, db):
        """Test tttool execution failure."""
        mock_get_cmd.return_value = ["/usr/bin/tttool"]
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "tttool", stderr="Error"
        )

        result = run_tttool("assemble album.yaml", None, db)

        assert result is False

    @patch("ttmp32gme.tttool_handler.get_tttool_command")
    @patch("ttmp32gme.tttool_handler.subprocess.run")
    @patch("ttmp32gme.tttool_handler.os.chdir")
    def test_run_tttool_with_path(self, mock_chdir, mock_run, mock_get_cmd, db):
        """Test tttool execution with working directory."""
        mock_get_cmd.return_value = ["/usr/bin/tttool"]
        mock_result = Mock()
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with tempfile.TemporaryDirectory() as tmpdir:
            work_dir = Path(tmpdir)
            result = run_tttool("assemble album.yaml", work_dir, db)

            assert result is True
            # Check that chdir was called
            assert mock_chdir.called
