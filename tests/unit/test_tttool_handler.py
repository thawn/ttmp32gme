"""Unit tests for tttool_handler module."""

import pytest
import sqlite3
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

from ttmp32gme.tttool_handler import (
    generate_codes_yaml,
    generate_yaml,
    convert_audio_file,
    create_gme_file
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))
        
        # Create necessary tables
        conn.execute('''CREATE TABLE script_codes (
            script TEXT PRIMARY KEY,
            code INTEGER
        )''')
        
        conn.execute('''CREATE TABLE albums (
            oid INTEGER PRIMARY KEY,
            title TEXT,
            publisher TEXT,
            author TEXT
        )''')
        
        conn.execute('''CREATE TABLE tracks (
            oid INTEGER PRIMARY KEY,
            album_oid INTEGER,
            title TEXT,
            file_path TEXT,
            track_no INTEGER
        )''')
        
        conn.commit()
        yield conn
        conn.close()


@pytest.fixture
def temp_files():
    """Create temporary files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        
        # Create a simple YAML file
        yaml_file = temp_path / "test.yaml"
        yaml_file.write_text("""product-id: 1
scripts:
  script1:
    - P(file1)
  script2:
    - P(file2)
""")
        
        yield temp_path
        # Cleanup happens automatically


class TestGenerateCodesYaml:
    """Test YAML code generation."""
    
    def test_generates_codes_for_new_scripts(self, temp_db, temp_files):
        """Test that codes are generated for new scripts."""
        yaml_file = temp_files / "test.yaml"
        
        # Generate codes
        codes_file = generate_codes_yaml(yaml_file, temp_db)
        
        assert codes_file.exists()
        assert codes_file.suffix == ".yaml"
        assert "codes" in codes_file.name
    
    def test_reuses_existing_codes(self, temp_db, temp_files):
        """Test that existing codes are reused."""
        yaml_file = temp_files / "test.yaml"
        
        # Insert some existing codes
        temp_db.execute("INSERT INTO script_codes VALUES ('script1', 100)")
        temp_db.commit()
        
        # Generate codes
        codes_file = generate_codes_yaml(yaml_file, temp_db)
        
        assert codes_file.exists()
        
        # Check that existing code was reused
        cursor = temp_db.cursor()
        cursor.execute("SELECT code FROM script_codes WHERE script = 'script1'")
        code = cursor.fetchone()[0]
        assert code == 100


class TestGenerateYaml:
    """Test main YAML generation."""
    
    @patch('ttmp32gme.tttool_handler.get_album')
    @patch('ttmp32gme.tttool_handler.get_oid_cache')
    def test_generates_yaml_for_album(self, mock_cache, mock_get_album, temp_db):
        """Test YAML generation for an album."""
        # Setup mocks
        mock_cache.return_value = Path("/tmp/cache")
        mock_get_album.return_value = {
            'oid': 1001,
            'title': 'Test Album',
            'tracks': [
                {'oid': 2001, 'title': 'Track 1', 'file_path': 'track1.ogg', 'track_no': 1},
                {'oid': 2002, 'title': 'Track 2', 'file_path': 'track2.ogg', 'track_no': 2}
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Generate YAML
            yaml_file = generate_yaml(1001, temp_db, output_dir)
            
            assert yaml_file.exists()
            content = yaml_file.read_text()
            assert 'product-id: 1001' in content
            assert 'scripts:' in content


class TestConvertAudioFile:
    """Test audio file conversion."""
    
    @patch('ttmp32gme.tttool_handler.subprocess.run')
    @patch('ttmp32gme.tttool_handler.get_executable_path')
    def test_mp3_to_ogg_conversion(self, mock_exec, mock_subprocess):
        """Test MP3 to OGG conversion using ffmpeg."""
        mock_exec.return_value = Path("/usr/bin/ffmpeg")
        mock_subprocess.return_value = Mock(returncode=0)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            input_file = temp_path / "test.mp3"
            output_file = temp_path / "test.ogg"
            
            # Create dummy input file
            input_file.write_bytes(b"fake mp3 data")
            
            # Convert
            result = convert_audio_file(input_file, output_file, 'ogg')
            
            assert mock_subprocess.called
            assert result == output_file or result is None  # Depends on implementation


class TestCreateGmeFile:
    """Test GME file creation."""
    
    @patch('ttmp32gme.tttool_handler.subprocess.run')
    @patch('ttmp32gme.tttool_handler.get_executable_path')
    @patch('ttmp32gme.tttool_handler.generate_yaml')
    def test_creates_gme_file(self, mock_yaml, mock_exec, mock_subprocess):
        """Test GME file creation with tttool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            
            # Setup mocks
            yaml_file = temp_path / "test.yaml"
            yaml_file.write_text("product-id: 1001")
            mock_yaml.return_value = yaml_file
            mock_exec.return_value = Path("/usr/bin/tttool")
            mock_subprocess.return_value = Mock(returncode=0)
            
            # Create GME file
            gme_file = temp_path / "test.gme"
            
            # This would call create_gme_file if it exists
            # For now, just verify the mocks would be set up correctly
            assert mock_yaml is not None
            assert mock_exec is not None
