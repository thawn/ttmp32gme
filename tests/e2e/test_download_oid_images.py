"""E2E tests for OID images download functionality."""

import io
import logging
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
    import time

    time.sleep(5)


@pytest.mark.e2e
@pytest.mark.slow
class TestOIDImagesDownload:
    """Test OID images download functionality."""

    def test_download_button_exists_on_config_page(self, driver, clean_server):
        """Test that the download OID images button exists on config page."""
        server_info = clean_server

        # Navigate to config page
        driver.get(f"{server_info['url']}/config")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Check for the download button
        download_button = driver.find_element(By.ID, "download-oid-images")
        assert download_button is not None, "Download OID images button not found"
        assert download_button.is_displayed(), "Download button should be visible"

        # Check button text contains "Download OID Images"
        button_text = download_button.text
        assert (
            "Download" in button_text and "OID" in button_text
        ), f"Button text incorrect: {button_text}"

    def test_download_oid_images_without_oid_cache(self, driver, clean_server):
        """Test downloading OID images when cache is empty returns 404."""
        server_info = clean_server

        # Try to download directly via URL without creating any OID images
        download_url = f"{server_info['url']}/download_oid_images"

        response = requests.get(download_url)
        # Should return 404 when no OID images exist
        assert (
            response.status_code == 404
        ), f"Expected 404 when no OID images exist, got {response.status_code}"

    def test_download_oid_images_after_gme_creation(self, driver, clean_server):
        """Test downloading OID images after creating GME files."""
        server_info = clean_server

        # Upload an album to create OID images
        album_name = "OID Test Album"
        with audio_files_context(album_name=album_name) as test_files:
            _upload_album_files(driver, server_info["url"], test_files)

        # Create GME file which generates OID images
        _create_gme_for_test(server_info["url"], driver, element_number=0)

        # Verify OID images were created in the cache
        oid_cache = server_info["library_path"].parent / "oid_cache"
        assert oid_cache.exists(), "OID cache directory should exist"

        png_files = list(oid_cache.glob("*.png"))
        assert len(png_files) > 0, "OID images should have been created"

        logger.info(f"Found {len(png_files)} OID images in cache")

        # Now test downloading via the web interface
        download_url = f"{server_info['url']}/download_oid_images"

        response = requests.get(download_url)
        assert (
            response.status_code == 200
        ), f"Download failed with status {response.status_code}"

        # Verify content type is ZIP
        assert (
            response.headers.get("Content-Type") == "application/zip"
        ), f"Expected ZIP content type, got {response.headers.get('Content-Type')}"

        # Verify we can open the ZIP file
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content, "r") as zipf:
            file_list = zipf.namelist()
            assert len(file_list) > 0, "ZIP file should contain files"

            # All files should be PNG files
            for filename in file_list:
                assert filename.endswith(
                    ".png"
                ), f"ZIP should only contain PNG files, found: {filename}"

            logger.info(f"ZIP file contains {len(file_list)} PNG files: {file_list}")

    def test_download_button_click_initiates_download(self, driver, clean_server):
        """Test that clicking the download button initiates a download."""
        server_info = clean_server

        # Upload an album and create GME to generate OID images
        album_name = "Button Test Album"
        with audio_files_context(album_name=album_name) as test_files:
            _upload_album_files(driver, server_info["url"], test_files)

        # Create GME file which generates OID images
        _create_gme_for_test(server_info["url"], driver, element_number=0)

        # Navigate to config page
        driver.get(f"{server_info['url']}/config")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "download-oid-images"))
        )

        # Find and verify the download button is clickable
        download_button = driver.find_element(By.ID, "download-oid-images")
        assert download_button.is_displayed(), "Download button should be visible"
        assert download_button.is_enabled(), "Download button should be enabled"

        # Click the button (this will trigger download but Selenium won't capture the file)
        # We just verify the button is clickable and doesn't cause errors
        download_button.click()

        # Wait a moment for any JavaScript errors to surface
        import time

        time.sleep(1)

        # Verify we're still on the config page and no errors occurred
        assert (
            "/config" in driver.current_url
        ), "Should remain on config page after clicking download"
