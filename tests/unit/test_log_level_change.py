"""Unit tests for log level change functionality."""

import logging
import sys
from pathlib import Path

# Add src to path to import ttmp32gme
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_apply_log_level_sets_root_logger():
    """Test that apply_log_level sets the root logger level."""
    from ttmp32gme.log_handler import apply_log_level

    root_logger = logging.getLogger()
    original_level = root_logger.level

    try:
        # Test DEBUG level
        apply_log_level("DEBUG")
        assert root_logger.level == logging.DEBUG

        # Test INFO level
        apply_log_level("INFO")
        assert root_logger.level == logging.INFO

        # Test WARNING level
        apply_log_level("WARNING")
        assert root_logger.level == logging.WARNING

    finally:
        # Restore original state
        root_logger.setLevel(original_level)


def test_apply_log_level_sets_werkzeug_logger():
    """Test that apply_log_level sets werkzeug logger appropriately."""
    from ttmp32gme.log_handler import apply_log_level

    werkzeug_logger = logging.getLogger("werkzeug")
    root_logger = logging.getLogger()
    original_level = root_logger.level
    original_werkzeug_level = werkzeug_logger.level

    try:
        # When DEBUG, werkzeug should be DEBUG
        apply_log_level("DEBUG")
        assert werkzeug_logger.level == logging.DEBUG

        # When INFO, werkzeug should be INFO
        apply_log_level("INFO")
        assert werkzeug_logger.level == logging.INFO

        # When WARNING, werkzeug should be WARNING (to suppress INFO logs)
        apply_log_level("WARNING")
        assert werkzeug_logger.level == logging.WARNING

        # When ERROR, werkzeug should be WARNING (to suppress INFO logs)
        apply_log_level("ERROR")
        assert werkzeug_logger.level == logging.WARNING

    finally:
        # Restore original state
        root_logger.setLevel(original_level)
        werkzeug_logger.setLevel(original_werkzeug_level)


def test_apply_log_level_sets_waitress_logger():
    """Test that apply_log_level sets waitress logger appropriately."""
    from ttmp32gme.log_handler import apply_log_level

    waitress_logger = logging.getLogger("waitress")
    root_logger = logging.getLogger()
    original_level = root_logger.level
    original_waitress_level = waitress_logger.level

    try:
        # When DEBUG, waitress should be DEBUG
        apply_log_level("DEBUG")
        assert waitress_logger.level == logging.DEBUG

        # When INFO, waitress should be INFO
        apply_log_level("INFO")
        assert waitress_logger.level == logging.INFO

        # When WARNING, waitress should be WARNING
        apply_log_level("WARNING")
        assert waitress_logger.level == logging.WARNING

        # When ERROR, waitress should be WARNING (to suppress INFO logs)
        apply_log_level("ERROR")
        assert waitress_logger.level == logging.WARNING

    finally:
        # Restore original state
        root_logger.setLevel(original_level)
        waitress_logger.setLevel(original_waitress_level)


def test_apply_log_level_logs_info_message(caplog):
    """Test that apply_log_level logs an info message."""
    from ttmp32gme.log_handler import apply_log_level

    root_logger = logging.getLogger()
    original_level = root_logger.level

    try:
        # Set to DEBUG first so INFO messages are captured
        root_logger.setLevel(logging.DEBUG)

        # Clear any previous log records
        caplog.clear()

        # Now capture the log level change to INFO
        with caplog.at_level(logging.INFO):
            apply_log_level("INFO")

        # Should see log level change message
        assert any(
            "Log level changed to INFO" in record.message for record in caplog.records
        ), f"Expected 'Log level changed to INFO' in logs, got: {[r.message for r in caplog.records]}"

    finally:
        # Restore original state
        root_logger.setLevel(original_level)
