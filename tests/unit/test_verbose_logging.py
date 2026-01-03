"""Unit tests for verbose logging functionality."""

import logging
import sys
from pathlib import Path

# Add src to path to import ttmp32gme
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_no_verbose_flag_uses_warning_logging():
    """Test that without -v flags, WARNING level is used."""
    from ttmp32gme.ttmp32gme import main

    root_logger = logging.getLogger()
    original_level = root_logger.level

    try:
        # Reset to WARNING level
        root_logger.setLevel(logging.WARNING)

        # Test without -v flag
        original_argv = sys.argv
        sys.argv = ["ttmp32gme", "--version"]

        main()

        # Logger should be at WARNING level
        assert root_logger.level == logging.WARNING

    finally:
        # Restore original state
        sys.argv = original_argv
        root_logger.setLevel(original_level)


def test_single_verbose_flag_enables_info_logging(caplog):
    """Test that -v flag enables INFO level logging."""
    from ttmp32gme.ttmp32gme import main

    # Test with single -v flag
    original_argv = sys.argv

    try:
        sys.argv = ["ttmp32gme", "-v", "--version"]

        with caplog.at_level(logging.INFO):
            main()

        # Should see info message in logs
        assert any(
            "Verbose mode enabled (INFO level)" in record.message
            for record in caplog.records
        ), f"Expected 'Verbose mode enabled (INFO level)' in logs, got: {[r.message for r in caplog.records]}"

        # Should have INFO level records
        assert any(
            record.levelno == logging.INFO for record in caplog.records
        ), "Expected INFO level records in logs"

    finally:
        # Restore original state
        sys.argv = original_argv


def test_double_verbose_flag_enables_debug_logging(caplog):
    """Test that -vv flag enables DEBUG level logging."""
    from ttmp32gme.ttmp32gme import main

    # Test with double -v flag
    original_argv = sys.argv

    try:
        sys.argv = ["ttmp32gme", "-vv", "--version"]

        with caplog.at_level(logging.DEBUG):
            main()

        # Should see debug message in logs
        assert any(
            "Verbose mode enabled (DEBUG level)" in record.message
            for record in caplog.records
        ), f"Expected 'Verbose mode enabled (DEBUG level)' in logs, got: {[r.message for r in caplog.records]}"

        # Should have DEBUG level records
        assert any(
            record.levelno == logging.DEBUG for record in caplog.records
        ), "Expected DEBUG level records in logs"

    finally:
        # Restore original state
        sys.argv = original_argv


def test_multiple_v_flags_work(caplog):
    """Test that multiple -v flags work correctly."""
    from ttmp32gme.ttmp32gme import main

    # Test with two separate -v flags
    original_argv = sys.argv

    try:
        sys.argv = ["ttmp32gme", "-v", "-v", "--version"]

        with caplog.at_level(logging.DEBUG):
            main()

        # Should see debug message in logs
        assert any(
            "Verbose mode enabled (DEBUG level)" in record.message
            for record in caplog.records
        ), "Expected 'Verbose mode enabled (DEBUG level)' in logs"

    finally:
        # Restore original state
        sys.argv = original_argv


def test_logger_used_in_fetch_config(caplog):
    """Test that logger.debug is called in fetch_config when debug mode is enabled."""
    import tempfile

    from ttmp32gme import ttmp32gme

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        custom_db = tmpdir / "custom.sqlite"

        # Reset global state
        original_db = ttmp32gme.db_handler
        original_db_path = ttmp32gme.custom_db_path

        logger = logging.getLogger("ttmp32gme.ttmp32gme")
        original_level = logger.level

        try:
            # Set up debug logging
            logger.setLevel(logging.DEBUG)

            ttmp32gme.db_handler = None
            ttmp32gme.custom_db_path = custom_db

            # Fetch config (should log debug message)
            with caplog.at_level(logging.DEBUG, logger="ttmp32gme.ttmp32gme"):
                ttmp32gme.fetch_config()

            # Should see debug message about fetched config
            assert any("Fetched config" in record.message for record in caplog.records)

        finally:
            # Restore original state
            ttmp32gme.db_handler = original_db
            ttmp32gme.custom_db_path = original_db_path
            logger.setLevel(original_level)
