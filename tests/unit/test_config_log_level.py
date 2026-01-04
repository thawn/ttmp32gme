"""Integration test for log level changes via config page."""

import logging
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path to import ttmp32gme
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def test_app():
    """Create a test Flask app with a temporary database."""
    from ttmp32gme import ttmp32gme

    # Save original state
    original_db = ttmp32gme.db_handler
    original_config = ttmp32gme.config
    original_custom_db_path = ttmp32gme.custom_db_path

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        custom_db = tmpdir / "test.sqlite"

        # Reset global state
        ttmp32gme.db_handler = None
        ttmp32gme.custom_db_path = custom_db
        ttmp32gme.config = {}

        # Initialize database
        ttmp32gme.get_db()
        ttmp32gme.config = ttmp32gme.fetch_config()

        yield ttmp32gme.app

        # Restore original state
        ttmp32gme.db_handler = original_db
        ttmp32gme.config = original_config
        ttmp32gme.custom_db_path = original_custom_db_path


def test_config_log_level_change_via_config_page(test_app):
    """Test that changing log level via config page updates all loggers."""
    client = test_app.test_client()

    # Get initial log level
    response = client.post("/config", data={"action": "load"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

    # Change log level to DEBUG via config update
    response = client.post(
        "/config",
        data={
            "action": "update",
            "data": '{"log_level": "DEBUG"}',
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    # Note: log_level might not be in the response if not all config fields are returned
    # Check the actual logger level instead
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG

    # Verify loggers are set correctly
    root_logger = logging.getLogger()
    werkzeug_logger = logging.getLogger("werkzeug")
    waitress_logger = logging.getLogger("waitress")
    assert root_logger.level == logging.DEBUG
    assert werkzeug_logger.level == logging.DEBUG
    assert waitress_logger.level == logging.DEBUG

    # Change log level to WARNING
    response = client.post(
        "/config",
        data={
            "action": "update",
            "data": '{"log_level": "WARNING"}',
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

    # Verify werkzeug and waitress are set to WARNING when not in verbose mode
    assert root_logger.level == logging.WARNING
    assert werkzeug_logger.level == logging.WARNING
    assert waitress_logger.level == logging.WARNING


def test_log_level_change_via_logs_endpoint(test_app):
    """Test that changing log level via /logs/level endpoint works."""
    client = test_app.test_client()

    # Change log level to INFO
    response = client.post(
        "/logs/level",
        json={"level": "INFO"},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["level"] == "INFO"

    # Verify loggers are set correctly
    root_logger = logging.getLogger()
    werkzeug_logger = logging.getLogger("werkzeug")
    waitress_logger = logging.getLogger("waitress")
    assert root_logger.level == logging.INFO
    assert werkzeug_logger.level == logging.INFO
    assert waitress_logger.level == logging.INFO

    # Change log level to ERROR
    response = client.post(
        "/logs/level",
        json={"level": "ERROR"},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["level"] == "ERROR"

    # Verify werkzeug and waitress are set to WARNING when not in verbose mode
    assert root_logger.level == logging.ERROR
    assert werkzeug_logger.level == logging.WARNING
    assert waitress_logger.level == logging.WARNING


def test_invalid_log_level_rejected(test_app):
    """Test that invalid log levels are rejected."""
    client = test_app.test_client()

    # Try to set invalid log level
    response = client.post(
        "/logs/level",
        json={"level": "INVALID"},
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
