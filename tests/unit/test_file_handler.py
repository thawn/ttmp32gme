"""Unit tests for build.file_handler module."""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from ttmp32gme.build.file_handler import (
    get_local_storage,
    get_default_library_path,
    make_temp_album_dir,
    make_new_album_dir,
    cleanup_filename,
    get_executable_path,
    move_to_album,
    remove_temp_dir,
    clear_album,
    remove_album,
    get_oid_cache,
    delete_gme_tiptoi,
    get_gmes_already_on_tiptoi,
    open_browser,
)


class TestFileHandler:
    """Test file handler utilities."""

    def test_get_local_storage(self):
        """Test getting local storage directory."""
        storage = get_local_storage()
        assert isinstance(storage, Path)
        assert storage.exists()

    def test_get_default_library_path(self):
        """Test getting default library path."""
        library = get_default_library_path()
        assert isinstance(library, Path)
        assert library.exists()
        assert library.name == "library"

    def test_make_temp_album_dir(self):
        """Test creating temporary album directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            library_path = Path(tmpdir)
            album_dir = make_temp_album_dir(1, library_path)

            assert album_dir.exists()
            assert album_dir.is_dir()
            assert "temp" in str(album_dir)
            assert "1" in str(album_dir)

    def test_make_new_album_dir(self):
        """Test creating new album directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            library_path = Path(tmpdir)
            album_dir = make_new_album_dir("Test Album", library_path)

            assert album_dir.exists()
            assert album_dir.is_dir()
            assert "Test Album" in album_dir.name or "Test_Album" in album_dir.name

    def test_make_new_album_dir_unique(self):
        """Test that duplicate album names get unique directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            library_path = Path(tmpdir)

            # Create first album
            album_dir1 = make_new_album_dir("Test Album", library_path)
            assert album_dir1.exists()

            # Create second album with same name
            album_dir2 = make_new_album_dir("Test Album", library_path)
            assert album_dir2.exists()

            # Should be different directories
            assert album_dir1 != album_dir2

    def test_cleanup_filename(self):
        """Test filename cleaning."""
        # Test with invalid characters
        assert cleanup_filename("test<file>name") == "test_file_name"
        assert cleanup_filename("test:file|name") == "test_file_name"
        assert cleanup_filename("normal_filename.mp3") == "normal_filename.mp3"
        assert cleanup_filename("Test<>File") == "Test__File"
        assert cleanup_filename("Normal_File.mp3") == "Normal_File.mp3"
        assert cleanup_filename("File:With|Invalid?Chars") == "File_With_Invalid_Chars"

    def test_get_executable_path_python(self):
        """Test finding Python executable (should always exist)."""
        python_path = get_executable_path("python3")
        # Python should be found in PATH
        assert python_path is not None or get_executable_path("python") is not None

    def test_get_executable_path_nonexistent(self):
        """Test with non-existent executable."""
        result = get_executable_path("nonexistent_executable_12345")
        assert result is None

    def test_move_to_album(self):
        """Test moving files from temp to album directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir) / "temp"
            album_dir = Path(tmpdir) / "album"
            
            temp_dir.mkdir()
            album_dir.mkdir()
            
            # Create some files in temp dir
            (temp_dir / "file1.txt").write_text("content1")
            (temp_dir / "file2.txt").write_text("content2")
            
            result = move_to_album(temp_dir, album_dir)
            
            assert result is True
            assert (album_dir / "file1.txt").exists()
            assert (album_dir / "file2.txt").exists()
            # Temp dir still exists but should be empty
            assert temp_dir.exists()
            assert len(list(temp_dir.iterdir())) == 0

    def test_remove_temp_dir(self):
        """Test removing temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir) / "temp_test"
            temp_dir.mkdir()
            
            (temp_dir / "file.txt").write_text("test")
            
            result = remove_temp_dir(temp_dir)
            
            assert result is True
            assert not temp_dir.exists()

    def test_remove_temp_dir_nonexistent(self):
        """Test removing non-existent directory."""
        result = remove_temp_dir(Path("/nonexistent/path"))
        assert result is False

    def test_clear_album(self):
        """Test clearing album directory contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            album_dir = Path(tmpdir) / "album"
            album_dir.mkdir()
            
            # Create some files
            (album_dir / "file1.txt").write_text("content")
            (album_dir / "file2.txt").write_text("content")
            
            result = clear_album(album_dir)
            
            assert result is True
            assert album_dir.exists()  # Directory still exists
            assert len(list(album_dir.iterdir())) == 0  # But is empty

    def test_remove_album(self):
        """Test removing album directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            album_dir = Path(tmpdir) / "album_to_remove"
            album_dir.mkdir()
            
            (album_dir / "file.txt").write_text("content")
            
            result = remove_album(album_dir)
            
            assert result is True
            assert not album_dir.exists()

    def test_get_oid_cache(self):
        """Test getting OID cache directory."""
        cache_dir = get_oid_cache()
        
        assert isinstance(cache_dir, Path)
        assert cache_dir.exists()
        assert cache_dir.is_dir()

    @patch('ttmp32gme.build.file_handler.get_tiptoi_dir')
    def test_get_gmes_already_on_tiptoi(self, mock_get_tiptoi):
        """Test getting list of GMEs on TipToi."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tiptoi_dir = Path(tmpdir)
            mock_get_tiptoi.return_value = tiptoi_dir
            
            # Create some GME files
            (tiptoi_dir / "album1.gme").write_bytes(b"fake gme")
            (tiptoi_dir / "album2.gme").write_bytes(b"fake gme")
            (tiptoi_dir / "readme.txt").write_text("not a gme")
            
            result = get_gmes_already_on_tiptoi()
            
            assert len(result) == 2
            assert "album1.gme" in result
            assert "album2.gme" in result
            assert "readme.txt" not in result

    @patch('ttmp32gme.build.file_handler.get_tiptoi_dir')
    def test_get_gmes_no_tiptoi(self, mock_get_tiptoi):
        """Test getting GMEs when TipToi not found."""
        mock_get_tiptoi.return_value = None
        
        result = get_gmes_already_on_tiptoi()
        
        assert result == []

    @patch('ttmp32gme.build.file_handler.get_tiptoi_dir')
    def test_delete_gme_tiptoi_success(self, mock_get_tiptoi):
        """Test deleting GME from TipToi."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tiptoi_dir = Path(tmpdir)
            mock_get_tiptoi.return_value = tiptoi_dir
            
            gme_file = tiptoi_dir / "album.gme"
            gme_file.write_bytes(b"fake gme")
            
            result = delete_gme_tiptoi("album.gme")
            
            assert result is True
            assert not gme_file.exists()

    @patch('ttmp32gme.build.file_handler.get_tiptoi_dir')
    def test_delete_gme_tiptoi_not_found(self, mock_get_tiptoi):
        """Test deleting GME when TipToi not found."""
        mock_get_tiptoi.return_value = None
        
        result = delete_gme_tiptoi("album.gme")
        
        assert result is False

    @patch('ttmp32gme.build.file_handler.subprocess.run')
    @patch('ttmp32gme.build.file_handler.platform.system')
    def test_open_browser_linux(self, mock_system, mock_run):
        """Test opening browser on Linux."""
        mock_system.return_value = "Linux"
        
        result = open_browser("localhost", 8080)
        
        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "xdg-open" in args
        assert "http://localhost:8080/" in args

    @patch('ttmp32gme.build.file_handler.subprocess.run')
    @patch('ttmp32gme.build.file_handler.platform.system')
    def test_open_browser_failure(self, mock_system, mock_run):
        """Test browser opening failure."""
        mock_system.return_value = "Linux"
        mock_run.side_effect = Exception("Failed")
        
        result = open_browser("localhost", 8080)
        
        assert result is False

