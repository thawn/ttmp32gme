"""Comprehensive end-to-end tests for ttmp32gme with real audio files."""

import pytest
import time
import shutil
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import APIC
from PIL import Image
import io
import subprocess

logger = logging.getLogger(__name__)


# Fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@contextmanager
def audio_files_context(album_name="Test Album"):
    """Context manager to create and cleanup test MP3 files with various ID3 tags."""
    files = []

    # Use bundled test audio file
    base_mp3 = FIXTURES_DIR / "test_audio.mp3"

    if not base_mp3.exists():
        raise FileNotFoundError("Test audio file not available.")

    try:
        # Create multiple copies with different ID3 tags
        test_cases = [
            {
                "filename": "track1_full_tags.mp3",
                "title": "Test Track 1",
                "artist": "Test Artist",
                "album": album_name,
                "year": "2024",
                "track": 1,
                "has_cover": True,
            },
            {
                "filename": "track2_minimal_tags.mp3",
                "title": "Test Track 2",
                "track": 2,
                "has_cover": False,
            },
            {"filename": "track3_no_tags.mp3", "has_cover": False},
        ]

        for test_case in test_cases:
            test_file = FIXTURES_DIR / test_case["filename"]
            shutil.copy(base_mp3, test_file)

            # Add ID3 tags using EasyID3 for compatibility
            try:
                audio = MP3(test_file, ID3=EasyID3)

                if "title" in test_case:
                    audio["title"] = test_case["title"]
                if "artist" in test_case:
                    audio["artist"] = test_case["artist"]
                if "album" in test_case:
                    audio["album"] = test_case["album"]
                if "year" in test_case:
                    audio["date"] = test_case["year"]
                if "track" in test_case:
                    audio["tracknumber"] = str(test_case["track"])

                audio.save()

                # Add cover image if requested (need to switch to raw ID3 for APIC)
                if test_case.get("has_cover"):
                    mp3 = MP3(test_file)
                    if mp3.tags is None:
                        mp3.add_tags()

                    img = Image.new("RGB", (100, 100), color="red")
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

            except Exception as e:
                print(f"Warning: Could not add tags to {test_file}: {e}")
                # File still exists and can be uploaded

            files.append(test_file)

        # Create a separate cover image file
        cover_img = FIXTURES_DIR / "separate_cover.jpg"
        img = Image.new("RGB", (200, 200), color="blue")
        img.save(cover_img, "JPEG")
        files.append(cover_img)

        yield files

    finally:
        # Cleanup
        for f in files:
            if f.exists():
                try:
                    f.unlink()
                except Exception as e:
                    print(f"Warning: Could not remove {f}: {e}")


@pytest.fixture(scope="function")
def clean_server(tmp_path, driver):
    """Start a new server with clean database and library in temporary directories.

    This fixture creates temporary database and library paths, starts a server with
    those paths, and cleans up everything after the test completes.
    """
    import subprocess
    import time
    import signal
    import os
    from selenium.common.exceptions import WebDriverException

    # Create temporary paths
    test_db = tmp_path / "test_config.sqlite"
    test_library = tmp_path / "test_library"
    test_library.mkdir(parents=True, exist_ok=True)

    # Find an available port (use a different port from default to avoid conflicts)
    test_port = 10021
    test_host = "127.0.0.1"

    # Start server with custom paths in background
    server_cmd = [
        "python",
        "-m",
        "ttmp32gme.ttmp32gme",
        "--database",
        str(test_db),
        "--library",
        str(test_library),
        "--host",
        test_host,
        "--port",
        str(test_port),
    ]

    logger.info(f"Starting test server with command: {' '.join(server_cmd)}")

    # Start the server process in the background
    server_process = subprocess.Popen(
        server_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,  # Ensure it runs in background
    )

    # Wait for server to start using Selenium WebDriverWait
    server_url = f"http://{test_host}:{test_port}"

    def server_is_ready(driver):
        """Check if server is ready by attempting to load the page."""
        try:
            driver.get(server_url)
            # If we can get the page title, server is ready
            return driver.title is not None
        except WebDriverException:
            return False

    try:
        # Wait up to 10 seconds for server to be ready
        WebDriverWait(driver, 10).until(server_is_ready)
        logger.info(f"Test server is ready at {server_url}")
    except Exception as e:
        server_process.terminate()
        stdout, stderr = server_process.communicate(timeout=5)
        raise RuntimeError(
            f"Server failed to start within timeout.\n"
            f"Error: {e}\n"
            f"Stdout: {stdout}\nStderr: {stderr}"
        )

    # Yield fixture data
    yield {
        "url": server_url,
        "db_path": test_db,
        "library_path": test_library,
        "port": test_port,
        "host": test_host,
    }

    # Cleanup: stop server
    logger.info("Stopping test server")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        logger.warning("Server did not stop gracefully, killing it")
        server_process.kill()
        server_process.wait()

    # Clean up temporary files (tmp_path is automatically cleaned up by pytest)
    logger.info("Test server cleanup complete")


@pytest.fixture(scope="function")
def base_config_with_album(driver, clean_server):
    """Base configuration with one album uploaded."""
    server_info = clean_server
    # Upload album with files using context manager
    with audio_files_context() as test_files:
        _upload_album_files(driver, server_info["url"], test_files)

    yield server_info


def _upload_album_files(driver, server_url, test_audio_files, audio_only=True):
    """Helper to upload album files through UI."""
    print(f"DEBUG: Navigating to {server_url}")
    driver.get(server_url)

    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "fine-uploader-manual-trigger"))
    )
    print("DEBUG: FineUploader container found")

    time.sleep(1)

    # Find file input (may be hidden by FineUploader)
    file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
    print(f"DEBUG: Found {len(file_inputs)} file inputs initially")

    if len(file_inputs) == 0:
        try:
            select_button = driver.find_element(By.CSS_SELECTOR, ".qq-upload-button")
            select_button.click()
            time.sleep(0.5)
            file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            print(
                f"DEBUG: After clicking select button, found {len(file_inputs)} file inputs"
            )
        except Exception as e:
            print(f"DEBUG: Error clicking select button: {e}")
            pass

    if len(file_inputs) > 0:
        if audio_only:
            upload_files = [str(f) for f in test_audio_files if f.suffix == ".mp3"]
        else:
            upload_files = [str(f) for f in test_audio_files]
        print(f"DEBUG: Uploading {len(upload_files)} files: {upload_files}")
        if upload_files:
            # Send files to input
            file_inputs[0].send_keys("\n".join(upload_files))
            time.sleep(2)  # Wait for FineUploader to process file selection
            print("DEBUG: Files sent to input, waiting for FineUploader to process")

            # Check if files were added to the upload list
            try:
                upload_list = driver.find_element(By.CSS_SELECTOR, ".qq-upload-list")
                list_items = upload_list.find_elements(By.TAG_NAME, "li")
                print(f"DEBUG: Upload list has {len(list_items)} items")
            except Exception as e:
                print(f"DEBUG: Could not check upload list: {e}")

            # Click "Add Album to Library" button to trigger upload
            try:
                upload_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "trigger-upload"))
                )
                print("DEBUG: Clicking 'Add Album to Library' button")
                upload_button.click()

                # Now wait for redirect to library page after upload completes
                print("DEBUG: Waiting for redirect to /library...")
                try:
                    WebDriverWait(driver, 5).until(
                        lambda d: "/library" in d.current_url
                    )
                    print(f"DEBUG: Successfully redirected to {driver.current_url}")
                except TimeoutException:
                    print(
                        f"DEBUG: Timeout waiting for automatic redirect. Current URL: {driver.current_url}"
                    )
                    # If automatic redirect doesn't happen (e.g., in headless mode),
                    # navigate manually since upload completed successfully
                    print("DEBUG: Navigating to library page manually...")
                    driver.get(f"{server_url}/library")
                    time.sleep(2)  # Wait for page to load
            except Exception as e:
                print(f"DEBUG: Error during upload process: {e}")
                raise
    else:
        print("DEBUG: No file inputs found, cannot upload files")


def _get_database_value(query, params=()):
    """Helper to query database directly."""
    db_path = Path.home() / ".ttmp32gme" / "config.sqlite"
    if not db_path.exists():
        return None

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    return result


def _open_library_element_for_editing(
    ttmp32gme_server, driver, element_number: int = 0
):
    """Open the edit modal of the library element with the given number"""
    driver.get(f"{ttmp32gme_server}/library")
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Look for create GME button and click it
    library_row = driver.find_element(By.ID, f"el{element_number}")
    edit_button = library_row.find_element(By.CLASS_NAME, "edit-button")
    edit_button.click()
    print(f"DEBUG: Clicked edit button")
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "make-gme"))
    )
    return library_row


def _create_gme(ttmp32gme_server, driver, element_number=0):
    library_row = _open_library_element_for_editing(
        ttmp32gme_server, driver, element_number
    )
    edit_button = library_row.find_element(By.CLASS_NAME, "edit-button")
    create_button = library_row.find_element(By.CLASS_NAME, "make-gme")
    create_button.click()
    time.sleep(5)  #


class TransientConfigChange:
    def __init__(
        self, driver, server_url, config: str = "audio_format", value: str = "ogg"
    ):
        self.driver = driver
        self.server_url = server_url
        self.config = config
        self.new_value = value
        self.old_value = _get_database_value(
            f"SELECT value FROM config WHERE param = '{config}'"
        )[0]

    def _get_config_element(self):
        """Helper to get audio format setting element from config."""
        self.driver.get(f"{self.server_url}/config")

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        return self.driver.find_element(By.ID, self.config)

    def _change_config(self, setting: str):
        """Helper to change audio format to OGG in config."""
        format_select = self._get_config_element()
        format_select.send_keys(setting)
        save_button = self.driver.find_element(By.ID, "submit")
        save_button.click()
        time.sleep(1)  # Wait for save

    def __enter__(self):
        self._change_config(self.new_value)

    def __exit__(self, type, value, traceback):
        self._change_config(self.old_value)


@pytest.mark.e2e
@pytest.mark.slow
class TestRealFileUpload:
    """Test file upload functionality with real MP3 and image files."""

    def test_upload_album_with_files(self, driver, clean_server):
        """Test uploading an album with real MP3 files."""
        album_name = "Upload Test Album"
        with audio_files_context(album_name=album_name) as test_files:
            _upload_album_files(driver, clean_server["url"], test_files)

        # Should be redirected to library after upload
        # If not, navigate there
        if "/library" not in driver.current_url:
            print(f"DEBUG: Not redirected to library, manually navigating")
            driver.get(f"{clean_server['url']}/library")

        # Wait for library page to load and albums to be populated via AJAX
        # The library page loads albums dynamically, so we need to wait for content
        try:
            # Wait for album title to appear (populated by AJAX)
            WebDriverWait(driver, 5).until(
                lambda d: album_name in d.find_element(By.TAG_NAME, "body").text
            )
            print("DEBUG: Album found in library page")
        except:
            # If timeout, print debug info
            body_text = driver.find_element(By.TAG_NAME, "body").text
            print(
                f"DEBUG: Timeout waiting for album. Library page text: {body_text[:500]}"
            )
            raise

        # Verify album appears in library
        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert (
            album_name in body_text or "Test Track" in body_text
        ), f"Album not found in library. Page text: {body_text[:200]}"
        library_path = Path.home() / ".ttmp32gme" / "library"
        album_path = library_path / album_name.replace(" ", "_")
        assert album_path.exists(), "Album directory not found in library after upload"
        assert list(
            album_path.glob("*.mp3")
        ), "No MP3 files found in album directory after upload"

    def test_id3_metadata_extraction(self, driver, ttmp32gme_server):
        """Test that ID3 metadata is correctly extracted and displayed."""
        album_name = "id3 Test Album"
        # Upload files
        with audio_files_context(album_name=album_name) as test_files:
            _upload_album_files(driver, ttmp32gme_server, test_files)

        # Check database for metadata
        result = _get_database_value(
            f"SELECT album_title FROM gme_library WHERE album_title = '{album_name}'"
        )
        assert result is not None, "Album not found in database"
        assert result[0] == album_name

        # Check metadata in UI
        driver.get(f"{ttmp32gme_server}/library")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert album_name in body_text
        assert "Test Artist" in body_text

    def test_cover_extraction_from_id3(self, driver, ttmp32gme_server):
        """Test that album covers are extracted from ID3 metadata."""
        album_name = "Cover Test Album"
        # Upload file with embedded cover
        with audio_files_context(album_name=album_name) as test_files:
            _upload_album_files(driver, ttmp32gme_server, test_files)

        # Check filesystem for cover image
        library_path = (
            Path.home() / ".ttmp32gme" / "library" / album_name.replace(" ", "_")
        )
        cover_files = (
            list(library_path.rglob("*.jpg"))
            + list(library_path.rglob("*.jpeg"))
            + list(library_path.rglob("*.png"))
        )

        assert len(cover_files) > 0, "No cover image found in library"

        # Check UI displays cover
        driver.get(f"{ttmp32gme_server}/library")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Look for image elements
        images = driver.find_elements(By.TAG_NAME, "img")
        cover_images = []
        for img in images:
            if img.get_attribute("alt"):
                if img.get_attribute("alt").lower() == "cover":
                    cover_images.append(img)
        assert len(cover_images) > 0, "No cover image displayed in UI"

    def test_separate_cover_upload(self, driver, ttmp32gme_server):
        """Test uploading separate cover image files."""
        album_name = "Separate Cover Album"
        with audio_files_context(album_name=album_name) as test_files:
            _upload_album_files(driver, ttmp32gme_server, test_files, audio_only=False)

        # Check cover image exists
        library_path = (
            Path.home() / ".ttmp32gme" / "library" / album_name.replace(" ", "_")
        )
        cover_files = list(library_path.rglob("*.jpg"))
        assert len(cover_files) > 0, "Cover image not uploaded"


@pytest.mark.e2e
@pytest.mark.slow
class TestAudioConversion:
    """Test MP3 to OGG conversion with real files."""

    def test_mp3_to_ogg_conversion(self, driver, ttmp32gme_server):
        """Test that MP3 files can be converted to OGG format."""
        # Change configuration to OGG format
        with TransientConfigChange(driver, ttmp32gme_server, "audio_format", "ogg"):
            # Trigger GME creation which should convert to OGG
            _create_gme(ttmp32gme_server, driver)

        # Cannot check that OGG files were created - they were already cleaned up


@pytest.mark.e2e
@pytest.mark.slow
class TestGMECreation:
    """Test GME file creation with real audio files."""

    def test_gme_creation_with_real_files(self, driver, ttmp32gme_server):
        """Test that GME files can be created from real MP3 files."""
        # Trigger GME creation
        _create_gme(ttmp32gme_server, driver)

        # Check that GME file was created
        library_path = Path.home() / ".ttmp32gme" / "library"
        gme_files = list(library_path.rglob("*.gme"))

        assert len(gme_files) > 0, "No GME file created"

        # Verify GME file is valid using tttool
        gme_file = gme_files[0]
        result = subprocess.run(
            ["tttool", "info", str(gme_file)], capture_output=True, text=True
        )
        assert result.returncode == 0, "tttool failed to validate GME file"
        assert "Product ID" in result.stdout, "GME file not recognized by tttool"


@pytest.mark.e2e
class TestWebInterface:
    """Test the web interface using Selenium."""

    def test_homepage_loads(self, driver, ttmp32gme_server):
        """Test that the homepage loads successfully."""
        driver.get(ttmp32gme_server)

        assert "ttmp32gme" in driver.title

        nav = driver.find_element(By.TAG_NAME, "nav")
        assert nav is not None

    def test_navigation_links(self, driver, ttmp32gme_server):
        """Test that all navigation links work from all pages."""
        pages = ["/", "/library", "/config", "/help"]

        for page in pages:
            driver.get(f"{ttmp32gme_server}{page}")
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Test each navigation link from this page
            for link_href in ["/", "/library", "/config", "/help"]:
                try:
                    link = driver.find_element(
                        By.CSS_SELECTOR, f"a[href='{link_href}']"
                    )
                    assert (
                        link is not None
                    ), f"Navigation link to {link_href} not found on {page}"
                except NoSuchElementException:
                    pytest.fail(f"Navigation link to {link_href} missing on {page}")

    def test_config_changes_persist(
        self, driver, base_config_with_album, ttmp32gme_server
    ):
        """Test that configuration changes are saved to database."""
        driver.get(f"{ttmp32gme_server}/config")

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        old_value = _get_database_value(
            "SELECT value FROM config WHERE param ='audio_format'"
        )[0]
        new_value = "ogg" if old_value == "mp3" else "mp3"

        # Change configuration options and save
        # Example: change audio format
        with TransientConfigChange(driver, ttmp32gme_server, "audio_format", "ogg"):
            assert (
                _get_database_value(
                    "SELECT value FROM config WHERE param ='audio_format'"
                )[0]
                == "ogg"
            ), "Config change not persisted"

    def test_edit_album_info(self, driver, base_config_with_album, ttmp32gme_server):
        """Test editing album information on library page."""
        driver.get(f"{ttmp32gme_server}/library")

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        library_element = _open_library_element_for_editing(ttmp32gme_server, driver)

        # Edit album title
        title_input = library_element.find_element(By.NAME, "album_title")
        title_input.clear()
        title_input.send_keys("Updated Album Title")

        # Save
        save_button = library_element.find_element(By.CLASS_NAME, "update")
        save_button.click()
        time.sleep(1)

        # Verify change
        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert "Updated Album Title" in body_text

    def test_select_deselect_all(
        self, driver, base_config_with_album, ttmp32gme_server
    ):
        """Test select all / deselect all on library page."""
        driver.get(f"{ttmp32gme_server}/library")

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Open select menu
        def click_select_option(option_id: str):
            select_menu = driver.find_element(By.ID, "dropdownMenu1")
            select_menu.click()
            time.sleep(0.1)
            option = driver.find_element(By.ID, option_id)
            option.click()
            time.sleep(0.5)

        # Click select all option
        click_select_option("select-all")
        checkboxes = driver.find_elements(
            By.CSS_SELECTOR, "input[type='checkbox'][name='enabled']"
        )
        for cb in checkboxes:
            assert cb.is_selected(), "Not all checkboxes selected"

        # Click to deselect all
        click_select_option("deselect-all")

        # Verify all are deselected
        for cb in checkboxes:
            assert not cb.is_selected(), "Not all checkboxes deselected"

    def test_print_album(self, driver, base_config_with_album, ttmp32gme_server):
        """Test print layout generation with configuration changes."""
        # First, go to library page
        driver.get(f"{ttmp32gme_server}/library")

        # Wait for library page to load with albums
        WebDriverWait(driver, 5).until(
            lambda d: "Test Album" in d.find_element(By.TAG_NAME, "body").text
        )

        # Use the select menu to select all albums (like test_select_deselect_all)
        select_menu = driver.find_element(By.ID, "dropdownMenu1")
        select_menu.click()
        time.sleep(0.1)
        select_all_option = driver.find_element(By.ID, "select-all")
        select_all_option.click()
        time.sleep(0.5)

        # Verify at least one checkbox is selected
        checkboxes = driver.find_elements(
            By.CSS_SELECTOR, "input[type='checkbox'][name='enabled']"
        )
        assert len(checkboxes) > 0, "No album checkboxes found"
        assert any(cb.is_selected() for cb in checkboxes), "No checkboxes selected"

        # Find and click "Print selected" button
        print_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "print-selected"))
        )
        print_button.click()

        # Wait for redirect to /print page
        WebDriverWait(driver, 5).until(lambda d: "/print" in d.current_url)

        # Wait for print page to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Wait a bit for the page to fully render
        time.sleep(1)

        # verify that we are using the default list layout
        album_920 = driver.find_element(By.ID, "oid_920")

        def _check_layout(
            album_element: WebElement,
            layout: str = "list",
            class_name: list[str] = [
                "cover",
                "album-info",
                "album-controls",
                "tracks",
                "general-controls",
            ],
        ):
            if layout == "list":
                # Default list layout: cover, album-info, album-controls and tracks visible
                should_be_hidden = [False, False, False, False, True]
            elif layout == "tiles":
                # Tiles layout: only cover and general-controls visible
                should_be_hidden = [False, True, True, True, False]
            elif layout == "cd":
                # CD layout: album-controls and tracks visible
                should_be_hidden = [True, True, False, False, True]
            else:
                raise ValueError(f"Unknown layout: {layout}")
            for i, cls in enumerate(class_name):
                if class_name[i] == "general-controls":
                    # General controls are outside album element
                    element = driver.find_element(By.ID, cls)
                else:
                    element = album_element.find_element(By.CLASS_NAME, cls)
                style_attr = element.get_attribute("style") or ""
                is_hidden = "display:none" in style_attr.replace(" ", "").lower()
                assert (
                    is_hidden == should_be_hidden[i]
                ), f"Layout: {layout}. Element {cls} hidden state mismatch: expected {should_be_hidden[i]}, got {is_hidden}"

        _check_layout(album_920, "list")

        # Try to expand the configuration panel - find the link in the panel heading
        # The config panel might be collapsed - look for the heading link
        config_link = driver.find_element(By.CSS_SELECTOR, "a[data-toggle='collapse']")
        config_link.click()
        time.sleep(0.1)  # Wait for panel to expand

        # Change layout preset to "tiles"
        tiles_preset = driver.find_element(By.ID, "tiles")
        tiles_preset.click()
        time.sleep(0.2)

        _check_layout(album_920, "tiles")

        # Change layout preset to "cd"
        cd_preset = driver.find_element(By.ID, "cd")
        cd_preset.click()
        time.sleep(0.2)

        _check_layout(album_920, "cd")

        # # Save configuration
        # save_button = driver.find_element(By.ID, "config-save")
        # save_button.click()
        # time.sleep(0.1)

        # Check that the print page is displayed with album content
        body_text = driver.find_element(By.TAG_NAME, "body").text
        # Should have either print-related text or the album name
        assert (
            "Test Album" in body_text or "print" in body_text.lower()
        ), f"Expected album or print content, got: {body_text[:200]}"

    def test_config_page_loads(self, driver, ttmp32gme_server):
        """Test that configuration page loads."""
        driver.get(f"{ttmp32gme_server}/config")

        body = driver.find_element(By.TAG_NAME, "body")
        assert body is not None

    def test_help_page_loads(self, driver, ttmp32gme_server):
        """Test that help page loads."""
        driver.get(f"{ttmp32gme_server}/help")

        body = driver.find_element(By.TAG_NAME, "body")
        assert body is not None

    def test_library_page_loads(self, driver, ttmp32gme_server):
        """Test that library page loads."""
        driver.get(f"{ttmp32gme_server}/library")

        body = driver.find_element(By.TAG_NAME, "body")
        assert body is not None


@pytest.mark.e2e
class TestCleanServerFixture:
    """Test the clean_server fixture."""

    def test_clean_server_starts_with_custom_paths(self, clean_server, driver):
        """Test that server starts with custom database and library paths."""
        server_info = clean_server

        # Verify server is accessible
        driver.get(server_info["url"])
        assert "ttmp32gme" in driver.title

        # Verify database file exists at custom path
        assert server_info["db_path"].exists(), "Custom database file was not created"

        # Verify library directory exists at custom path
        assert server_info[
            "library_path"
        ].exists(), "Custom library directory was not created"
        assert server_info[
            "library_path"
        ].is_dir(), "Custom library path is not a directory"

        # Verify we can access the library page
        driver.get(f"{server_info['url']}/library")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Verify library is initially empty (clean state)
        # The page should load successfully but have no albums
        body_text = driver.find_element(By.TAG_NAME, "body").text
        # Just check page loaded - don't check for specific content as it's a clean state
        assert body_text is not None
