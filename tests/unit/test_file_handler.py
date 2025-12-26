"""Unit tests for build.file_handler module."""

import os
import tempfile
from pathlib import Path

import pytest

from ttmp32gme.build.file_handler import (
    get_local_storage, get_default_library_path, make_temp_album_dir,
    make_new_album_dir, cleanup_filename, get_executable_path
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
        assert library.name == 'library'
    
    def test_make_temp_album_dir(self):
        """Test creating temporary album directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            library_path = Path(tmpdir)
            album_dir = make_temp_album_dir(1, library_path)
            
            assert album_dir.exists()
            assert album_dir.is_dir()
            assert 'temp' in str(album_dir)
            assert '1' in str(album_dir)
    
    def test_make_new_album_dir(self):
        """Test creating new album directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            library_path = Path(tmpdir)
            album_dir = make_new_album_dir('Test Album', library_path)
            
            assert album_dir.exists()
            assert album_dir.is_dir()
            assert 'Test Album' in album_dir.name or 'Test_Album' in album_dir.name
    
    def test_make_new_album_dir_unique(self):
        """Test that duplicate album names get unique directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            library_path = Path(tmpdir)
            
            # Create first album
            album_dir1 = make_new_album_dir('Test Album', library_path)
            assert album_dir1.exists()
            
            # Create second album with same name
            album_dir2 = make_new_album_dir('Test Album', library_path)
            assert album_dir2.exists()
            
            # Should be different directories
            assert album_dir1 != album_dir2
    
    def test_cleanup_filename(self):
        """Test filename cleaning."""
        # Test with invalid characters
        assert cleanup_filename('test<file>name') == 'test_file_name'
        assert cleanup_filename('test:file|name') == 'test_file_name'
        assert cleanup_filename('normal_filename.mp3') == 'normal_filename.mp3'
    
    def test_get_executable_path_python(self):
        """Test finding Python executable (should always exist)."""
        python_path = get_executable_path('python3')
        # Python should be found in PATH
        assert python_path is not None or get_executable_path('python') is not None
    
    def test_get_executable_path_nonexistent(self):
        """Test with non-existent executable."""
        result = get_executable_path('nonexistent_executable_12345')
        assert result is None
