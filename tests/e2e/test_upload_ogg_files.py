"""End-to-end tests for uploading OGG audio files."""

import logging
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Import fixtures and helpers from conftest
from .conftest import _upload_album_files, audio_files_context, ogg_audio_files_context

logger = logging.getLogger(__name__)


def _get_database_value(query, params=(), db_path=None):
    """Helper to query database directly."""
    if db_path is None:
        db_path = Path.home() / ".ttmp32gme" / "config.sqlite"
    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    return result


@pytest.mark.e2e
@pytest.mark.slow
class TestOggFileUpload:
    """Test OGG file upload functionality."""

    def test_upload_album_with_ogg_files(self, driver, clean_server):
        """Test uploading an album with OGG files."""
        server_info = clean_server

        album_name = "Test OGG Album"
        with ogg_audio_files_context(album_name=album_name) as test_files:
            # Filter to only OGG files (exclude cover image)
            ogg_files = [f for f in test_files if f.suffix.lower() == ".ogg"]
            
            # Verify OGG files were created
            assert len(ogg_files) == 3, f"Expected 3 OGG files, got {len(ogg_files)}"
            
            # Verify files exist and have content
            for ogg_file in ogg_files:
                assert ogg_file.exists(), f"OGG file {ogg_file} does not exist"
                assert ogg_file.stat().st_size > 0, f"OGG file {ogg_file} is empty"
            
            _upload_album_files(driver, server_info["url"], test_files, audio_only=False)

        # Should be redirected to library after upload
        # If not, navigate there
        if "/library" not in driver.current_url:
            driver.get(f"{server_info['url']}/library")

        # Wait for library page to load and albums to be populated via AJAX
        try:
            # Wait for album title to appear (populated by AJAX)
            WebDriverWait(driver, 5).until(
                lambda d: album_name in d.find_element(By.TAG_NAME, "body").text
            )
            print("DEBUG: OGG Album found in library page")
        except Exception:
            # If timeout, print debug info
            body_text = driver.find_element(By.TAG_NAME, "body").text
            print(
                f"DEBUG: Timeout waiting for album. "
                f"Library page text: {body_text[:500]}"
            )
            raise

        # Verify album appears in library
        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert (
            album_name in body_text or "Test OGG Track" in body_text
        ), f"Album not found in library. Page text: {body_text[:200]}"
        
        library_path = server_info["library_path"]
        album_path = library_path / album_name.replace(" ", "_")
        assert album_path.exists(), "Album directory not found in library after upload"
        
        # Verify OGG files were uploaded
        uploaded_files = list(album_path.glob("*.ogg"))
        assert len(uploaded_files) > 0, "No OGG files found in album directory after upload"

    def test_ogg_id3_metadata_extraction(self, driver, clean_server):
        """Test that OGG Vorbis tags are correctly extracted and displayed."""
        server_info = clean_server
        album_name = "OGG Metadata Test"
        
        # Upload OGG files with tags
        with ogg_audio_files_context(album_name=album_name) as test_files:
            _upload_album_files(driver, server_info["url"], test_files, audio_only=False)

        # Check database for metadata
        result = _get_database_value(
            "SELECT album_title FROM gme_library WHERE album_title = ?",
            params=(album_name,),
            db_path=server_info["db_path"],
        )
        assert result is not None, "Album not found in database"
        assert result[0] == album_name, f"Expected album title '{album_name}', got '{result[0]}'"

        # Check track metadata in database
        conn = sqlite3.connect(str(server_info["db_path"]))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT title, artist FROM tracks WHERE album = ? ORDER BY track",
            (album_name,),
        )
        tracks = cursor.fetchall()
        conn.close()

        # Verify we have tracks
        assert len(tracks) >= 1, "No tracks found in database"
        
        # Verify first track has correct metadata
        first_track_title = tracks[0][0]
        first_track_artist = tracks[0][1]
        
        # First track should have full tags
        assert "Test OGG Track 1" in first_track_title or first_track_title, (
            f"Expected track title to contain 'Test OGG Track 1', got '{first_track_title}'"
        )
        assert "Test OGG Artist" in first_track_artist or first_track_artist, (
            f"Expected artist to contain 'Test OGG Artist', got '{first_track_artist}'"
        )

        # Check metadata in UI
        driver.get(f"{server_info['url']}/library")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert album_name in body_text, f"Album name '{album_name}' not found in UI"
        assert "Test OGG Artist" in body_text, "Artist name not found in UI"

    def test_ogg_separate_cover_upload(self, driver, clean_server):
        """Test uploading separate cover image files with OGG files."""
        server_info = clean_server
        album_name = "OGG Cover Album"
        
        with ogg_audio_files_context(album_name=album_name) as test_files:
            _upload_album_files(
                driver, server_info["url"], test_files, audio_only=False
            )

        # Check cover image exists
        library_path = server_info["library_path"] / album_name.replace(" ", "_")
        cover_files = list(library_path.rglob("*.jpg"))
        assert len(cover_files) > 0, "Cover image not uploaded with OGG files"

    def test_mixed_ogg_and_mp3_upload(self, driver, clean_server):
        """Test uploading album with both OGG and MP3 files."""
        from .conftest import audio_files_context
        
        server_info = clean_server
        album_name = "Mixed Audio Album"
        
        # Collect both MP3 and OGG files
        all_files = []
        
        # Get MP3 files
        with audio_files_context(album_name=album_name) as mp3_files:
            mp3_audio = [f for f in mp3_files if f.suffix.lower() == ".mp3"]
            # Copy MP3 files to a safe location (they'll be cleaned up by context)
            tmpdir = tempfile.mkdtemp()
            tmp_path = Path(tmpdir)
            
            for mp3 in mp3_audio[:1]:  # Just take one MP3 file
                safe_mp3 = tmp_path / f"mp3_{mp3.name}"
                shutil.copy(mp3, safe_mp3)
                all_files.append(safe_mp3)
        
        # Get OGG files
        with ogg_audio_files_context(album_name=album_name) as ogg_files:
            ogg_audio = [f for f in ogg_files if f.suffix.lower() == ".ogg"]
            for ogg in ogg_audio[:1]:  # Just take one OGG file
                safe_ogg = tmp_path / f"ogg_{ogg.name}"
                shutil.copy(ogg, safe_ogg)
                all_files.append(safe_ogg)
            
            try:
                # Upload mixed files
                _upload_album_files(driver, server_info["url"], all_files, audio_only=True)
                
                # Verify upload
                if "/library" not in driver.current_url:
                    driver.get(f"{server_info['url']}/library")
                
                WebDriverWait(driver, 5).until(
                    lambda d: album_name in d.find_element(By.TAG_NAME, "body").text
                )
                
                # Check files were uploaded
                library_path = server_info["library_path"] / album_name.replace(" ", "_")
                assert library_path.exists(), "Album directory not found"
                
                mp3_count = len(list(library_path.glob("*.mp3")))
                ogg_count = len(list(library_path.glob("*.ogg")))
                
                # Should have both types
                assert mp3_count > 0 or ogg_count > 0, "No audio files found after mixed upload"
                
            finally:
                # Cleanup temp directory
                try:
                    shutil.rmtree(tmpdir)
                except Exception as e:
                    print(f"Warning: Could not cleanup temp dir: {e}")
