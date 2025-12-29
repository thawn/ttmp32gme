"""Pytest configuration for end-to-end tests."""

import pytest
import subprocess
import time
from pathlib import Path


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
    options.BinaryLocation = "/usr/bin/chromium-browser"
    return options


@pytest.fixture
def driver(chrome_options):
    """Create a Chrome WebDriver instance."""
    from selenium import webdriver

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)

    yield driver

    driver.quit()
