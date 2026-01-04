"""E2E tests for GME file download functionality."""

import logging
import time

import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Import fixtures and helpers from conftest
from .conftest import _upload_album_files, audio_files_context

logger = logging.getLogger(__name__)


def _create_gme(server_url, driver, element_number=0):
    """Helper to create GME file for an album."""
    driver.get(f"{server_url}/library")
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Find the library row and click edit button
    library_row = driver.find_element(By.ID, f"el{element_number}")
    edit_button = library_row.find_element(By.CLASS_NAME, "edit-button")

    # Scroll element into view to ensure it's interactable (especially on Windows)
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", edit_button
    )
    time.sleep(0.1)  # Brief pause to ensure scrolling completes

    # Wait for button to be clickable before clicking
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "edit-button"))
    )
    edit_button.click()

    # Wait for edit panel to be visible and clickable
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "make-gme"))
    )

    # Click the "Create GME" button
    create_button = library_row.find_element(By.CLASS_NAME, "make-gme")

    # Scroll button into view to ensure it's interactable
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", create_button
    )
    time.sleep(0.1)  # Brief pause to ensure scrolling completes

    create_button.click()

    # Wait for GME creation to complete (this may take a few seconds)
    time.sleep(5)

    return library_row


@pytest.mark.e2e
@pytest.mark.slow
class TestGMEDownload:
    """Test GME file download functionality."""

    def test_download_button_appears_after_gme_creation(self, driver, clean_server):
        """Test that download button appears after GME file is created."""
        server_info = clean_server

        # Upload an album
        album_name = "Download Test Album"
        with audio_files_context(album_name=album_name) as test_files:
            _upload_album_files(driver, server_info["url"], test_files)

        # Navigate to library page
        driver.get(f"{server_info['url']}/library")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Wait for album to appear
        WebDriverWait(driver, 5).until(
            lambda d: album_name in d.find_element(By.TAG_NAME, "body").text
        )

        # Open the edit panel for the first album
        library_row = driver.find_element(By.ID, "el0")
        edit_button = library_row.find_element(By.CLASS_NAME, "edit-button")

        # Scroll element into view to ensure it's interactable (especially on Windows)
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", edit_button
        )
        time.sleep(0.1)  # Brief pause to ensure scrolling completes

        # Wait for button to be clickable before clicking
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "edit-button"))
        )
        edit_button.click()

        # Wait for edit panel to open
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "make-gme"))
        )

        # Verify download button is disabled before GME creation
        download_buttons = library_row.find_elements(By.CLASS_NAME, "download-gme")
        assert len(download_buttons) > 0, "Download button element not found"
        download_button = download_buttons[0]

        # Button should be visible but disabled initially
        assert download_button.is_displayed(), "Download button should be visible"
        assert (
            not download_button.is_enabled()
        ), "Download button should be disabled before GME creation"

        # Create GME file
        create_button = library_row.find_element(By.CLASS_NAME, "make-gme")
        create_button.click()
        time.sleep(5)  # Wait for GME creation

        # Verify download button is now enabled and active
        assert (
            download_button.is_displayed()
        ), "Download button should still be visible after GME creation"
        assert (
            download_button.is_enabled()
        ), "Download button should be enabled after GME creation"

    def test_download_gme_file(self, driver, clean_server):
        """Test that GME file can be downloaded through the web interface."""
        server_info = clean_server

        # Upload an album
        album_name = "GME Download Album"
        with audio_files_context(album_name=album_name) as test_files:
            _upload_album_files(driver, server_info["url"], test_files)

        # Create GME file
        library_row = _create_gme(server_info["url"], driver, element_number=0)

        # Verify GME file was created in filesystem
        library_path = server_info["library_path"]
        gme_files = list(library_path.rglob("*.gme"))
        assert len(gme_files) > 0, "No GME file created in filesystem"
        gme_file = gme_files[0]
        assert gme_file.exists(), "GME file does not exist"

        # Get the GME file size for verification later
        original_gme_size = gme_file.stat().st_size
        logger.info(
            f"Original GME file: {gme_file.name}, size: {original_gme_size} bytes"
        )

        # Find and click the download button
        download_button = library_row.find_element(By.CLASS_NAME, "download-gme")
        assert download_button.is_displayed(), "Download button should be visible"

        # Get the OID for constructing the download URL
        oid_input = library_row.find_element(By.NAME, "old_oid")
        oid = oid_input.get_attribute("value")

        # Verify the download URL is correct
        download_url = f"{server_info['url']}/download_gme/{oid}"
        logger.info(f"Download URL: {download_url}")

        # Test direct download via URL (Selenium can't easily test file downloads,
        # but we can verify the endpoint returns 200 OK)
        response = requests.get(download_url)
        assert (
            response.status_code == 200
        ), f"Download endpoint returned {response.status_code}"
        assert response.headers.get("Content-Type") in [
            "application/octet-stream",
            "audio/mpeg",
            "audio/x-mpeg",
        ], f"Unexpected content type: {response.headers.get('Content-Type')}"

        # Verify the response contains file data
        downloaded_content = response.content
        assert len(downloaded_content) > 0, "Downloaded file is empty"
        assert (
            len(downloaded_content) == original_gme_size
        ), f"Downloaded file size ({len(downloaded_content)}) doesn't match original ({original_gme_size})"

        logger.info(
            f"Successfully downloaded GME file: {len(downloaded_content)} bytes"
        )

    def test_download_without_gme_returns_404(self, driver, clean_server):
        """Test that attempting to download non-existent GME returns 404."""
        server_info = clean_server

        # Upload an album but don't create GME
        album_name = "No GME Album"
        with audio_files_context(album_name=album_name) as test_files:
            _upload_album_files(driver, server_info["url"], test_files)

        # Navigate to library
        driver.get(f"{server_info['url']}/library")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Wait for album to appear
        WebDriverWait(driver, 5).until(
            lambda d: album_name in d.find_element(By.TAG_NAME, "body").text
        )

        # Open edit panel
        library_row = driver.find_element(By.ID, "el0")
        edit_button = library_row.find_element(By.CLASS_NAME, "edit-button")
        edit_button.click()

        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "make-gme"))
        )

        # Get OID
        oid_input = library_row.find_element(By.NAME, "old_oid")
        oid = oid_input.get_attribute("value")

        # Try to download (should fail)
        download_url = f"{server_info['url']}/download_gme/{oid}"

        response = requests.get(download_url)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        assert (
            "not created" in response.text.lower()
            or "not found" in response.text.lower()
        ), "Error message should indicate GME file was not created"

    def test_download_invalid_oid_returns_404(self, driver, clean_server):
        """Test that attempting to download with invalid OID returns 404."""
        server_info = clean_server

        # Try to download with invalid OID
        download_url = f"{server_info['url']}/download_gme/99999"

        response = requests.get(download_url)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        assert (
            "not found" in response.text.lower()
        ), "Error message should indicate album was not found"
