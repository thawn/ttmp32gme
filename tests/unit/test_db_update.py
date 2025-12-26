"""Unit tests for db_update module."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from ttmp32gme.db_update import update, UPDATES


class TestDbUpdate:
    """Test database update functionality."""
    
    def test_updates_dict_structure(self):
        """Test that UPDATES dictionary has proper structure."""
        assert isinstance(UPDATES, dict)
        assert len(UPDATES) > 0
        for version, sql in UPDATES.items():
            assert isinstance(version, str)
            assert isinstance(sql, str)
            assert len(sql) > 0
    
    def test_update_incremental(self):
        """Test incremental database updates."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            # Create database with basic schema (simplified test)
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE config (param TEXT, value TEXT)')
            cursor.execute('INSERT INTO config VALUES ("version", "1.0.0")')
            conn.commit()
            
            # Update to latest version (should succeed with no actual updates needed)
            result = update("1.0.0", conn)
            assert result is True
            
            # Check version is still valid
            cursor.execute('SELECT value FROM config WHERE param="version"')
            version = cursor.fetchone()[0]
            assert version == "1.0.0"  # No update needed for 1.0.0
            
            conn.close()
        finally:
            db_path.unlink()
    
    def test_update_already_current(self):
        """Test update when database is already at latest version."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE config (param TEXT, value TEXT)')
            # Set to a very high version
            cursor.execute('INSERT INTO config VALUES ("version", "99.0.0")')
            conn.commit()
            
            # Update should succeed (no updates to apply)
            result = update("99.0.0", conn)
            assert result is True
            
            conn.close()
        finally:
            db_path.unlink()
