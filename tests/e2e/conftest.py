"""Pytest configuration for end-to-end tests."""

import io
import logging
import shutil
import sqlite3
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC
from mutagen.mp3 import MP3
from PIL import Image
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

# Fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="session")
def ttmp32gme_server():
    """Return server URL (assumes server is already running from script)."""
    # When run via run_e2e_tests_locally.sh, server is already started
    # Just return the URL
    return "http://localhost:10020"


@pytest.fixture
def chrome_options():
    """Chrome options for headless testing."""
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.BinaryLocation = "/usr/bin/chromium"
    return options


@pytest.fixture
def driver(chrome_options, tmp_path):
    """Create a Chrome WebDriver instance with download directory configured."""
    from selenium import webdriver

    # Create a temporary download directory for this test session
    download_dir = tmp_path / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)

    # Configure Chrome to download PDFs automatically to the download directory
    prefs = {
        "download.default_directory": str(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,  # Download PDFs instead of opening in viewer
        "profile.default_content_settings.popups": 0,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)

    # Store download directory on driver for tests to access
    driver.download_dir = download_dir

    yield driver

    driver.quit()


@contextmanager
def audio_files_context(album_name="Test Album"):
    """Context manager to create and cleanup test MP3 files with various ID3 tags."""
    files = []

    # Use bundled test audio file
    base_mp3 = FIXTURES_DIR / "test_audio.mp3"

    if not base_mp3.exists():
        raise FileNotFoundError("Test audio file not available.")

    # Create temporary directory for test files (will be cleaned up by this context manager)
    tmpdir = tempfile.mkdtemp()
    tmp_path = Path(tmpdir)

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
            test_file = tmp_path / test_case["filename"]
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
        cover_img = tmp_path / "separate_cover.jpg"
        img = Image.new("RGB", (200, 200), color="blue")
        img.save(cover_img, "JPEG")
        files.append(cover_img)

        yield files

    finally:
        # Cleanup: remove temporary directory
        try:
            shutil.rmtree(tmpdir)
        except Exception as e:
            print(f"Warning: Could not remove temporary directory {tmpdir}: {e}")


@contextmanager
def ogg_audio_files_context(album_name="Test OGG Album"):
    """Context manager to create and cleanup test OGG files with various tags.

    Reuses audio_files_context to generate MP3 files with tags, then converts them to OGG
    using ffmpeg with the same arguments as tttool_handler.py. FFmpeg preserves the tags
    during conversion.
    """
    # Check if ffmpeg is available
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg not found, cannot convert to OGG format")

    # Create temporary directory for OGG files
    tmpdir = tempfile.mkdtemp()
    tmp_path = Path(tmpdir)
    ogg_files = []

    try:
        # Use the existing audio_files_context to generate MP3 files with tags
        with audio_files_context(album_name=album_name) as mp3_files:
            # Convert each MP3 file to OGG
            for mp3_file in mp3_files:
                if mp3_file.suffix.lower() == ".mp3":
                    # Create OGG file with same base name
                    ogg_file = tmp_path / mp3_file.with_suffix(".ogg").name

                    # Convert MP3 to OGG using ffmpeg with same arguments as tttool_handler.py
                    # From tttool_handler.py lines 141-155
                    cmd = [
                        ffmpeg_path,
                        "-y",
                        "-i",
                        str(mp3_file),
                        "-map",
                        "0:a",
                        "-ar",
                        "22050",
                        "-ac",
                        "1",
                        str(ogg_file),
                    ]

                    subprocess.run(cmd, check=True, capture_output=True)
                    ogg_files.append(ogg_file)
                elif mp3_file.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    # Copy image files directly
                    img_file = tmp_path / mp3_file.name
                    shutil.copy(mp3_file, img_file)
                    ogg_files.append(img_file)

        yield ogg_files

    finally:
        # Cleanup: remove temporary directory
        try:
            shutil.rmtree(tmpdir)
        except Exception as e:
            print(f"Warning: Could not remove temporary directory {tmpdir}: {e}")


@pytest.fixture(scope="function")
def clean_server(tmp_path, driver, monkeypatch):
    """Start a new server with clean database and library in temporary directories.

    This fixture creates temporary database and library paths, starts a server with
    those paths, and cleans up everything after the test completes.
    """
    import os
    import subprocess

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
        "--no-browser",
        "-vv",
    ]

    logger.info(f"Starting test server with command: {' '.join(server_cmd)}")

    # Create log files for server output
    server_log_file = tmp_path / "server.log"
    server_err_file = tmp_path / "server_err.log"

    # Start the server process in the background with output redirected to files
    with open(server_log_file, "w") as stdout_f, open(server_err_file, "w") as stderr_f:
        server_process = subprocess.Popen(
            server_cmd,
            stdout=stdout_f,
            stderr=stderr_f,
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
        server_process.wait(timeout=5)

        # Read log files for error reporting
        stdout_content = ""
        stderr_content = ""
        try:
            if server_log_file.exists():
                stdout_content = server_log_file.read_text()
            if server_err_file.exists():
                stderr_content = server_err_file.read_text()
        except Exception:
            pass

        raise RuntimeError(
            f"Server failed to start within timeout.\n"
            f"Error: {e}\n"
            f"Stdout: {stdout_content}\nStderr: {stderr_content}"
        )

    # Yield fixture data
    yield {
        "url": server_url,
        "db_path": test_db,
        "library_path": test_library,
        "port": test_port,
        "host": test_host,
        "log_file": server_log_file,
        "err_file": server_err_file,
        "process": server_process,
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

    # Clean up environment variable
    os.environ.pop("TTMP32GME_TEST_TEMP_DIR", None)

    # Clean up temporary files (tmp_path is automatically cleaned up by pytest)
    logger.info("Test server cleanup complete")


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
            # Include both .mp3 and .ogg files (case-insensitive, using set for efficient membership testing)
            upload_files = [
                str(f) for f in test_audio_files if f.suffix.lower() in {".mp3", ".ogg"}
            ]
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


@pytest.fixture(scope="function")
def base_config_with_album(driver, clean_server):
    """Base configuration with one album uploaded."""
    server_info = clean_server
    # Upload album with files using context manager
    with audio_files_context() as test_files:
        _upload_album_files(driver, server_info["url"], test_files)

    yield server_info
