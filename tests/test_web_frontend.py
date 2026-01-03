"""
Integration tests for ttmp32gme web frontend
These tests verify that the web pages load correctly
"""

import json
import logging
import subprocess
import time

import pytest
import requests

from ttmp32gme.print_handler import PRINT_PDF_FILENAME

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def clean_server_http(tmp_path):
    """Start a new server with clean database and library in temporary directories.

    This is a lightweight version for HTTP-based tests (without Selenium).
    """
    # Create temporary paths
    test_db = tmp_path / "test_config.sqlite"
    test_library = tmp_path / "test_library"
    test_library.mkdir(parents=True, exist_ok=True)

    # Find an available port (use a different port from default to avoid conflicts)
    test_port = 10022
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
    ]

    logger.info(f"Starting test server with command: {' '.join(server_cmd)}")

    # Start the server process in the background
    server_process = subprocess.Popen(
        server_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )

    # Wait for server to start using requests
    server_url = f"http://{test_host}:{test_port}"
    max_wait = 10  # seconds
    start_time = time.time()
    server_ready = False

    while time.time() - start_time < max_wait:
        try:
            response = requests.get(server_url, timeout=1)
            if response.status_code in [200, 302, 303]:
                server_ready = True
                logger.info(f"Test server is ready at {server_url}")
                break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass
        time.sleep(0.5)

    if not server_ready:
        server_process.terminate()
        stdout, stderr = server_process.communicate(timeout=5)
        raise RuntimeError(
            f"Server failed to start within {max_wait} seconds.\n"
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

    logger.info("Test server cleanup complete")


class TestWebPages:
    """Test that web pages are accessible and return valid responses"""

    def test_library_page_exists(self, clean_server_http):
        """Test that library page exists and returns 200"""
        server_info = clean_server_http
        response = requests.get(f"{server_info['url']}/library", timeout=5)
        # If server is running, should return 200 or redirect
        assert response.status_code in [
            200,
            302,
            303,
        ], f"Expected status 200/302/303, got {response.status_code}"

    def test_upload_page_exists(self, clean_server_http):
        """Test that upload (root) page exists"""
        server_info = clean_server_http
        response = requests.get(f"{server_info['url']}/", timeout=5)
        assert response.status_code in [
            200,
            302,
            303,
        ], f"Expected status 200/302/303, got {response.status_code}"

    def test_config_page_exists(self, clean_server_http):
        """Test that config page exists"""
        server_info = clean_server_http
        response = requests.get(f"{server_info['url']}/config", timeout=5)
        assert response.status_code in [
            200,
            302,
            303,
        ], f"Expected status 200/302/303, got {response.status_code}"

    def test_help_page_exists(self, clean_server_http):
        """Test that help page exists"""
        server_info = clean_server_http
        response = requests.get(f"{server_info['url']}/help", timeout=5)
        assert response.status_code in [
            200,
            302,
            303,
        ], f"Expected status 200/302/303, got {response.status_code}"


class TestStaticAssets:
    """Test that static assets are accessible"""

    def test_jquery_library_exists(self, clean_server_http):
        """Test that jQuery library is accessible"""
        server_info = clean_server_http
        response = requests.get(
            f"{server_info['url']}/assets/js/jquery-3.1.1.min.js", timeout=5
        )
        assert (
            response.status_code == 200
        ), f"Expected status 200, got {response.status_code}"
        assert (
            "jquery" in response.text.lower() or "jQuery" in response.text
        ), "Response doesn't appear to be jQuery"

    def test_print_js_exists(self, clean_server_http):
        """Test that print.js is accessible"""
        server_info = clean_server_http
        response = requests.get(f"{server_info['url']}/assets/js/print.js", timeout=5)
        assert (
            response.status_code == 200
        ), f"Expected status 200, got {response.status_code}"
        # Check for known function names from print.js
        assert (
            "cssPagedMedia" in response.text or "notify" in response.text
        ), "Response doesn't appear to be print.js"

    def test_bootstrap_css_exists(self, clean_server_http):
        """Test that Bootstrap CSS is accessible"""
        server_info = clean_server_http
        response = requests.get(
            f"{server_info['url']}/assets/css/bootstrap.min.css", timeout=5
        )
        assert (
            response.status_code == 200
        ), f"Expected status 200, got {response.status_code}"


class TestPageContent:
    """Test that pages contain expected content"""

    def test_library_page_has_title(self, clean_server_http):
        """Test that library page contains expected title"""
        server_info = clean_server_http
        response = requests.get(f"{server_info['url']}/library.html", timeout=5)
        if response.status_code == 200:
            assert (
                "ttmp32gme" in response.text
            ), "Library page should contain ttmp32gme title"


class TestOIDImagesDownload:
    """Test OID images download functionality via HTTP"""

    def test_download_oid_images_endpoint_exists(self, clean_server_http):
        """Test that download endpoint exists and returns valid response"""
        server_info = clean_server_http
        response = requests.get(f"{server_info['url']}/download_oid_images", timeout=5)
        # Should return either 404 (no images) or 200 (has images)
        assert response.status_code in [
            200,
            404,
        ], f"Expected 200 or 404, got {response.status_code}"
        if response.status_code == 404:
            assert (
                "No OID images available" in response.text
            ), "Should indicate no images available"
        elif response.status_code == 200:
            # Should be a ZIP file
            assert (
                response.headers.get("Content-Type") == "application/zip"
            ), "Should return ZIP file"

    def test_config_page_has_download_button(self, clean_server_http):
        """Test that config page contains the download OID images button"""
        server_info = clean_server_http
        response = requests.get(f"{server_info['url']}/config", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert (
            "Download OID Images" in response.text
        ), "Config page should have download button"
        assert (
            "download-oid-images" in response.text
        ), "Config page should have button ID"
        assert (
            "downloadOidImages" in response.text
        ), "Config page should have JavaScript function"


class TestPrintPDFDownload:
    """Test print PDF download functionality via HTTP"""

    def test_print_pdf_generation_and_download(self, clean_server_http):
        """Test that save_pdf action generates and returns PDF directly"""
        server_info = clean_server_http

        # Test data for PDF generation
        test_content = "<div>Test PDF Content</div>"

        # Post to /print with save_pdf action
        response = requests.post(
            f"{server_info['url']}/print",
            data={"action": "save_pdf", "data": json.dumps({"content": test_content})},
            timeout=30,  # Increased timeout for PDF generation
        )

        # Should return PDF file directly
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert (
            response.headers.get("Content-Type") == "application/pdf"
        ), "Should return PDF file"
        assert "attachment" in response.headers.get(
            "Content-Disposition", ""
        ), "Should be an attachment"
        assert PRINT_PDF_FILENAME in response.headers.get(
            "Content-Disposition", ""
        ), f"Filename should be {PRINT_PDF_FILENAME}"

        # Verify PDF content is not empty
        assert len(response.content) > 100, "PDF content should not be empty"

        # Note: PDF is created in a temporary file and automatically cleaned up
        # after being sent, so there's no file to check in the library folder
