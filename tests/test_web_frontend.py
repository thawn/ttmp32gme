"""
Integration tests for ttmp32gme web frontend
These tests verify that the web pages load correctly
"""

import pytest
import requests
import os


class TestWebPages:
    """Test that web pages are accessible and return valid responses"""
    
    @pytest.fixture(scope="class")
    def base_url(self):
        """Base URL for the application"""
        # Default to localhost:10020 as per README
        return os.environ.get('TTMP32GME_URL', 'http://localhost:10020')
    
    def test_library_page_exists(self, base_url):
        """Test that library.html page exists and returns 200"""
        # This is a basic test that would run when the server is up
        # In a real scenario, the server should be started before running tests
        # For now, we'll structure the test properly
        try:
            response = requests.get(f"{base_url}/library.html", timeout=5)
            # If server is running, should return 200 or redirect
            assert response.status_code in [200, 302, 303], \
                f"Expected status 200/302/303, got {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running - skipping integration test")
    
    def test_upload_page_exists(self, base_url):
        """Test that upload.html page exists"""
        try:
            response = requests.get(f"{base_url}/upload.html", timeout=5)
            assert response.status_code in [200, 302, 303], \
                f"Expected status 200/302/303, got {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running - skipping integration test")
    
    def test_config_page_exists(self, base_url):
        """Test that config.html page exists"""
        try:
            response = requests.get(f"{base_url}/config.html", timeout=5)
            assert response.status_code in [200, 302, 303], \
                f"Expected status 200/302/303, got {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running - skipping integration test")
    
    def test_help_page_exists(self, base_url):
        """Test that help.html page exists"""
        try:
            response = requests.get(f"{base_url}/help.html", timeout=5)
            assert response.status_code in [200, 302, 303], \
                f"Expected status 200/302/303, got {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running - skipping integration test")


class TestStaticAssets:
    """Test that static assets are accessible"""
    
    @pytest.fixture(scope="class")
    def base_url(self):
        """Base URL for the application"""
        return os.environ.get('TTMP32GME_URL', 'http://localhost:10020')
    
    def test_jquery_library_exists(self, base_url):
        """Test that jQuery library is accessible"""
        try:
            response = requests.get(f"{base_url}/assets/js/jquery-3.1.1.min.js", timeout=5)
            assert response.status_code == 200, \
                f"Expected status 200, got {response.status_code}"
            assert 'jquery' in response.text.lower() or 'jQuery' in response.text, \
                "Response doesn't appear to be jQuery"
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running - skipping integration test")
    
    def test_print_js_exists(self, base_url):
        """Test that print.js is accessible"""
        try:
            response = requests.get(f"{base_url}/assets/js/print.js", timeout=5)
            assert response.status_code == 200, \
                f"Expected status 200, got {response.status_code}"
            # Check for known function names from print.js
            assert 'cssPagedMedia' in response.text or 'notify' in response.text, \
                "Response doesn't appear to be print.js"
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running - skipping integration test")
    
    def test_bootstrap_css_exists(self, base_url):
        """Test that Bootstrap CSS is accessible"""
        try:
            response = requests.get(f"{base_url}/assets/css/bootstrap.min.css", timeout=5)
            assert response.status_code == 200, \
                f"Expected status 200, got {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running - skipping integration test")


class TestPageContent:
    """Test that pages contain expected content"""
    
    @pytest.fixture(scope="class")
    def base_url(self):
        """Base URL for the application"""
        return os.environ.get('TTMP32GME_URL', 'http://localhost:10020')
    
    def test_library_page_has_title(self, base_url):
        """Test that library page contains expected title"""
        try:
            response = requests.get(f"{base_url}/library.html", timeout=5)
            if response.status_code == 200:
                assert 'ttmp32gme' in response.text, \
                    "Library page should contain ttmp32gme title"
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running - skipping integration test")
