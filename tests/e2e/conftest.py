"""Pytest configuration for end-to-end tests."""

import pytest
import subprocess
import time
from pathlib import Path


@pytest.fixture(scope="session")
def ttmp32gme_server():
    """Start ttmp32gme server for testing."""
    # Start server in background
    server_process = subprocess.Popen(
        ["python", "-m", "ttmp32gme.ttmp32gme", "--port", "10021"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(3)
    
    yield "http://localhost:10021"
    
    # Cleanup
    server_process.terminate()
    server_process.wait(timeout=5)


@pytest.fixture
def chrome_options():
    """Chrome options for headless testing."""
    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    return options


@pytest.fixture
def driver(chrome_options):
    """Create a Chrome WebDriver instance."""
    from selenium import webdriver
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    
    yield driver
    
    driver.quit()
