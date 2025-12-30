"""Unit tests for custom database and library paths."""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add src to path to import ttmp32gme
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_custom_db_path_variable():
    """Test that custom_db_path variable can be set."""
    from ttmp32gme import ttmp32gme
    
    original_value = ttmp32gme.custom_db_path
    try:
        test_path = Path("/tmp/test_db.sqlite")
        ttmp32gme.custom_db_path = test_path
        assert ttmp32gme.custom_db_path == test_path
    finally:
        ttmp32gme.custom_db_path = original_value


def test_custom_library_path_variable():
    """Test that custom_library_path variable can be set."""
    from ttmp32gme import ttmp32gme
    
    original_value = ttmp32gme.custom_library_path
    try:
        test_path = Path("/tmp/test_library")
        ttmp32gme.custom_library_path = test_path
        assert ttmp32gme.custom_library_path == test_path
    finally:
        ttmp32gme.custom_library_path = original_value


def test_get_db_with_custom_path():
    """Test that get_db creates database at custom path."""
    from ttmp32gme import ttmp32gme
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        custom_db = tmpdir / "custom.sqlite"
        
        # Reset the global db_handler to force recreation
        original_db = ttmp32gme.db_handler
        original_custom_path = ttmp32gme.custom_db_path
        
        try:
            ttmp32gme.db_handler = None
            ttmp32gme.custom_db_path = custom_db
            
            # Get database - should create at custom path
            db = ttmp32gme.get_db()
            
            # Verify database was created at custom path
            assert custom_db.exists(), f"Database not created at {custom_db}"
            assert db is not None
            assert db.db_path == str(custom_db)
            
        finally:
            # Restore original state
            ttmp32gme.db_handler = original_db
            ttmp32gme.custom_db_path = original_custom_path


def test_fetch_config_with_custom_library():
    """Test that fetch_config uses custom library path."""
    from ttmp32gme import ttmp32gme
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        custom_db = tmpdir / "custom.sqlite"
        custom_lib = tmpdir / "custom_library"
        custom_lib.mkdir()
        
        # Reset global state
        original_db = ttmp32gme.db_handler
        original_config = ttmp32gme.config
        original_db_path = ttmp32gme.custom_db_path
        original_lib_path = ttmp32gme.custom_library_path
        
        try:
            ttmp32gme.db_handler = None
            ttmp32gme.custom_db_path = custom_db
            ttmp32gme.custom_library_path = custom_lib
            
            # Fetch config
            config = ttmp32gme.fetch_config()
            
            # Verify custom library path is in config
            assert config["library_path"] == str(custom_lib)
            
        finally:
            # Restore original state
            ttmp32gme.db_handler = original_db
            ttmp32gme.config = original_config
            ttmp32gme.custom_db_path = original_db_path
            ttmp32gme.custom_library_path = original_lib_path


def test_cli_arguments_parsing():
    """Test that CLI arguments are parsed correctly."""
    from ttmp32gme.ttmp32gme import main
    import sys
    
    # Test --database and --library arguments
    original_argv = sys.argv
    try:
        sys.argv = [
            "ttmp32gme",
            "--database", "/tmp/test.db",
            "--library", "/tmp/test_lib",
            "--version"  # Use version to exit early without starting server
        ]
        
        # Should not raise exception
        main()
        
    finally:
        sys.argv = original_argv
