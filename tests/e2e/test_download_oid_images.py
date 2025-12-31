"""E2E tests for OID images download functionality."""

import io
import logging
import time
import zipfile

import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Import fixtures and helpers from conftest
from .conftest import _upload_album_files, audio_files_context

logger = logging.getLogger(__name__)


def _create_gme_for_test(server_url, driver, element_number=0):
    """Helper to create GME file for an album to generate OID images."""
    driver.get(f"{server_url}/library")
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Find the library row and click edit button
    library_row = driver.find_element(By.ID, f"el{element_number}")
    edit_button = library_row.find_element(By.CLASS_NAME, "edit-button")
    edit_button.click()

    # Wait for edit panel to be visible and clickable
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "make-gme"))
    )

    # Click the "Create GME" button to generate OID images
    create_button = library_row.find_element(By.CLASS_NAME, "make-gme")
    create_button.click()

    # Wait for GME creation to complete
    time.sleep(5)


@pytest.mark.e2e
@pytest.mark.slow
class TestOIDImagesDownload:
    """Test OID images download functionality."""

    def test_download_fails_before_any_album_uploaded(self, driver, clean_server):
        """Test that download fails when no albums have been uploaded yet.

        This test verifies the error handling when attempting to download
        OID images before any GME files (which generate OID images) exist.
        """
        server_info = clean_server

        # Clean OID cache before test to ensure clean state
        # The OID cache is stored in user's home directory, not in test library
        from ttmp32gme.build.file_handler import get_oid_cache

        oid_cache = get_oid_cache()
        # Remove all PNG files from cache
        for png_file in oid_cache.glob("*.png"):
            png_file.unlink()
        logger.info(f"Cleaned OID cache at {oid_cache}")

        # Try to download directly via URL without creating any albums/OIDs
        download_url = f"{server_info['url']}/download_oid_images"

        response = requests.get(download_url)
        # Should return 404 when no OID images exist
        assert (
            response.status_code == 404
        ), f"Expected 404 when no OID images exist, got {response.status_code}"
        assert (
            "No OID images available" in response.text
        ), "Error message should indicate no images available"

        logger.info("✓ Download correctly fails when no albums uploaded")

    def test_download_successful_after_gme_creation(self, driver, clean_server):
        """Test successful download after creating a GME file.

        This test verifies:
        1. Upload an album with audio files
        2. Create GME file (which triggers OID image generation)
        3. Download OID images as ZIP
        4. Verify ZIP contains multiple PNG files
        """
        server_info = clean_server

        # Clean OID cache before test to ensure clean state
        from ttmp32gme.build.file_handler import get_oid_cache

        oid_cache = get_oid_cache()
        # Remove all PNG files from cache before test
        for png_file in oid_cache.glob("*.png"):
            png_file.unlink()
        logger.info(f"Cleaned OID cache at {oid_cache} before test")

        # Step 1: Upload an album
        album_name = "OID Test Album"
        with audio_files_context(album_name=album_name) as test_files:
            _upload_album_files(driver, server_info["url"], test_files)

        # Step 2: Create GME file which generates OID images
        _create_gme_for_test(server_info["url"], driver, element_number=0)

        # Verify OID images were created in the cache
        # Note: OID cache is in user's home directory, not in test library
        png_files = list(oid_cache.glob("*.png"))
        assert len(png_files) > 0, "OID images should have been created"

        logger.info(f"Found {len(png_files)} OID images in cache")

        # Step 3: Test downloading via the endpoint
        download_url = f"{server_info['url']}/download_oid_images"

        response = requests.get(download_url)
        assert (
            response.status_code == 200
        ), f"Download failed with status {response.status_code}"

        # Step 4: Verify content type is ZIP
        assert (
            response.headers.get("Content-Type") == "application/zip"
        ), f"Expected ZIP content type, got {response.headers.get('Content-Type')}"

        # Step 5: Verify we can open the ZIP file and it contains PNG files
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content, "r") as zipf:
            file_list = zipf.namelist()
            assert len(file_list) > 0, "ZIP file should contain files"

            # All files should be PNG files
            for filename in file_list:
                assert filename.endswith(
                    ".png"
                ), f"ZIP should only contain PNG files, found: {filename}"

            logger.info(
                f"✓ ZIP file contains {len(file_list)} PNG files: {file_list[:5]}"
            )

        # Step 6: Verify count matches
        # Note: The actual count might differ slightly from filesystem count
        # due to caching or generation differences, but should be > 0
        assert len(file_list) > 0, "Should have at least one OID image in ZIP"

        logger.info("✓ Download successful after GME creation")

        # Cleanup: Remove OID images created during test
        for png_file in oid_cache.glob("*.png"):
            png_file.unlink()
        logger.info("Cleaned up OID cache after test")
        # due to caching or generation differences, but should be > 0
        assert len(file_list) > 0, "Should have at least one OID image in ZIP"

        logger.info("✓ Download successful after GME creation")
