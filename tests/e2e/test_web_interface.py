"""End-to-end tests for ttmp32gme web interface."""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.mark.e2e
class TestWebInterface:
    """Test the web interface using Selenium."""
    
    def test_homepage_loads(self, driver, ttmp32gme_server):
        """Test that the homepage loads successfully."""
        driver.get(ttmp32gme_server)
        
        # Check title
        assert "ttmp32gme" in driver.title
        
        # Check navigation exists
        nav = driver.find_element(By.TAG_NAME, "nav")
        assert nav is not None
    
    def test_navigation_links(self, driver, ttmp32gme_server):
        """Test that navigation links work."""
        driver.get(ttmp32gme_server)
        
        # Find and test library link
        library_link = driver.find_element(By.LINK_TEXT, "Library")
        library_link.click()
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        assert "/library" in driver.current_url
    
    def test_config_page_loads(self, driver, ttmp32gme_server):
        """Test that configuration page loads."""
        driver.get(f"{ttmp32gme_server}/config")
        
        # Check for config form elements
        body = driver.find_element(By.TAG_NAME, "body")
        assert body is not None
    
    def test_help_page_loads(self, driver, ttmp32gme_server):
        """Test that help page loads."""
        driver.get(f"{ttmp32gme_server}/help")
        
        # Check page loaded
        body = driver.find_element(By.TAG_NAME, "body")
        assert body is not None
    
    def test_library_page_loads(self, driver, ttmp32gme_server):
        """Test that library page loads."""
        driver.get(f"{ttmp32gme_server}/library")
        
        # Check page loaded
        body = driver.find_element(By.TAG_NAME, "body")
        assert body is not None


@pytest.mark.e2e
@pytest.mark.slow
class TestFileUpload:
    """Test file upload functionality (requires test files)."""
    
    def test_upload_page_has_upload_widget(self, driver, ttmp32gme_server):
        """Test that upload page has upload widget."""
        driver.get(ttmp32gme_server)
        
        # Look for upload elements (the specific selectors depend on the upload widget used)
        body_text = driver.find_element(By.TAG_NAME, "body").text
        # Upload page should mention files or drag-drop
        assert "Select files" in body_text or "Drop files" in body_text or "upload" in body_text.lower()
