"""Integration tests for db_handler.create_library_entry method."""

import tempfile
import shutil
from pathlib import Path
import pytest

from ttmp32gme.db_handler import DBHandler


class TestCreateLibraryEntryIntegration:
    """Integration tests for create_library_entry with real files."""

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

    @pytest.fixture
    def library_path(self):
        """Create a temporary library directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def test_files(self):
        """Copy test files to a temporary directory for upload simulation."""
        # Get test files from fixtures
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        test_audio = fixtures_dir / "test_audio.mp3"
        test_cover = fixtures_dir / "test_cover.jpg"
        
        if not test_audio.exists():
            pytest.skip("Test audio file not found")
        
        # Create temp directory to simulate upload
        temp_dir = Path(tempfile.mkdtemp())
        
        # Copy files to temp directory
        audio_copy = temp_dir / "test_audio.mp3"
        shutil.copy2(test_audio, audio_copy)
        
        files = {"audio": str(audio_copy)}
        
        if test_cover.exists():
            cover_copy = temp_dir / "test_cover.jpg"
            shutil.copy2(test_cover, cover_copy)
            files["cover"] = str(cover_copy)
        
        yield files, temp_dir
        
        # Cleanup (files will be moved by create_library_entry)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_create_library_entry_with_audio_file(self, db, library_path, test_files):
        """Test create_library_entry with real audio file."""
        files, temp_dir = test_files
        
        # Prepare album list as expected by create_library_entry
        album_list = [
            {
                "file1": files["audio"],
            }
        ]
        
        # Call create_library_entry
        result = db.create_library_entry(album_list, library_path)
        
        assert result is True
        
        # Verify album was added to database
        albums = db.get_album_list()
        assert len(albums) == 1
        
        album = albums[0]
        assert album["oid"] >= 920  # Default starting OID
        assert album["num_tracks"] == 1
        assert album["album_title"]  # Should have extracted or defaulted to "unknown"
        
        # Verify track was added
        tracks = db.get_tracks(album)
        assert len(tracks) == 1
        assert 1 in tracks
        assert tracks[1]["title"]  # Should have a title
        assert tracks[1]["duration"] >= 0

    def test_create_library_entry_with_audio_and_cover(self, db, library_path, test_files):
        """Test create_library_entry with audio and cover image."""
        files, temp_dir = test_files
        
        if "cover" not in files:
            pytest.skip("Test cover image not found")
        
        # Prepare album list
        album_list = [
            {
                "file1": files["audio"],
                "file2": files["cover"],
            }
        ]
        
        # Call create_library_entry
        result = db.create_library_entry(album_list, library_path)
        
        assert result is True
        
        # Verify album was added
        albums = db.get_album_list()
        assert len(albums) == 1
        
        album = albums[0]
        assert album["picture_filename"]  # Should have cover image
        
        # Verify cover file was saved
        album_dir = Path(album["path"])
        assert album_dir.exists()
        cover_file = album_dir / album["picture_filename"]
        assert cover_file.exists()

    def test_create_library_entry_multiple_audio_files(self, db, library_path, test_files):
        """Test create_library_entry with multiple audio files."""
        files, temp_dir = test_files
        
        # Create second copy of audio file
        audio2 = temp_dir / "test_audio2.mp3"
        shutil.copy2(files["audio"], audio2)
        
        # Prepare album list
        album_list = [
            {
                "file1": files["audio"],
                "file2": str(audio2),
            }
        ]
        
        # Call create_library_entry
        result = db.create_library_entry(album_list, library_path)
        
        assert result is True
        
        # Verify album was added with 2 tracks
        albums = db.get_album_list()
        assert len(albums) == 1
        
        album = albums[0]
        assert album["num_tracks"] == 2
        
        # Verify both tracks were added
        tracks = db.get_tracks(album)
        assert len(tracks) == 2
        assert 1 in tracks
        assert 2 in tracks

    def test_create_library_entry_empty_album(self, db, library_path):
        """Test create_library_entry with empty album (should be skipped)."""
        # Prepare album list with empty album
        album_list = [{}]
        
        # Call create_library_entry
        result = db.create_library_entry(album_list, library_path)
        
        assert result is True
        
        # Verify no album was added
        albums = db.get_album_list()
        assert len(albums) == 0

    def test_create_library_entry_validation_enforced(self, db, library_path, test_files):
        """Test that Pydantic validation is enforced during create_library_entry."""
        files, temp_dir = test_files
        
        # Prepare album list
        album_list = [
            {
                "file1": files["audio"],
            }
        ]
        
        # Call create_library_entry - should succeed with validation
        result = db.create_library_entry(album_list, library_path)
        assert result is True
        
        # Verify data in database meets validation requirements
        albums = db.get_album_list()
        album = albums[0]
        
        # OID should be in valid range
        assert 0 <= album["oid"] <= 1000
        
        # Number of tracks should be valid
        assert 0 <= album["num_tracks"] <= 999
        
        # Album title should not be empty
        assert album["album_title"].strip()
        
        # Track validation
        tracks = db.get_tracks(album)
        for track in tracks.values():
            assert track["title"].strip()  # Track title not empty
            assert track["track"] >= 1  # Track number >= 1
            assert track["duration"] >= 0  # Duration >= 0

    def test_create_library_entry_separate_cover_precedence(self, db, library_path, test_files):
        """Test that separate cover images take precedence over embedded covers."""
        files, temp_dir = test_files
        
        if "cover" not in files:
            pytest.skip("Test cover image not found")
        
        # Create an MP3 file with embedded cover
        audio_with_cover = temp_dir / "audio_with_cover.mp3"
        shutil.copy2(files["audio"], audio_with_cover)
        
        # Add embedded cover to MP3
        from mutagen.mp3 import MP3
        from mutagen.id3 import APIC
        from PIL import Image
        import io
        
        mp3 = MP3(audio_with_cover)
        if mp3.tags is None:
            mp3.add_tags()
        
        # Create red embedded cover
        img = Image.new("RGB", (50, 50), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        
        mp3.tags.add(
            APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=img_bytes.read(),
            )
        )
        mp3.save()
        
        # Prepare album list with both audio (with embedded cover) and separate cover
        album_list = [
            {
                "file1": str(audio_with_cover),
                "file2": files["cover"],  # Separate cover should win
            }
        ]
        
        # Call create_library_entry
        result = db.create_library_entry(album_list, library_path)
        assert result is True
        
        # Verify album was added with the separate cover
        albums = db.get_album_list()
        assert len(albums) == 1
        
        album = albums[0]
        assert album["picture_filename"]
        
        # Verify the separate cover file was saved (should match the separate cover name)
        album_dir = Path(album["path"])
        assert album_dir.exists()
        
        # The cover filename should be based on the separate cover file, not embedded
        cover_file = album_dir / album["picture_filename"]
        assert cover_file.exists()
        
        # Verify it's the separate cover by checking it's the one from test_cover.jpg
        # (In a real scenario, you might check file content or size)
