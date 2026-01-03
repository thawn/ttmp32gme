"""Unit tests for verbose logging functionality."""

import logging
import sys
from pathlib import Path

# Add src to path to import ttmp32gme
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_verbose_flag_enables_debug_logging(caplog):
    """Test that --verbose flag enables DEBUG level logging."""
    from ttmp32gme.ttmp32gme import main

    # Test with --verbose flag
    original_argv = sys.argv

    try:
        sys.argv = ["ttmp32gme", "--verbose", "--version"]

        with caplog.at_level(logging.DEBUG):
            main()

        # Should see verbose message in logs
        assert any(
            "Verbose mode enabled" in record.message for record in caplog.records
        ), f"Expected 'Verbose mode enabled' in logs, got: {[r.message for r in caplog.records]}"

        # Should have DEBUG level records
        assert any(
            record.levelno == logging.DEBUG for record in caplog.records
        ), "Expected DEBUG level records in logs"

    finally:
        # Restore original state
        sys.argv = original_argv


def test_without_verbose_flag_uses_info_logging():
    """Test that without --verbose flag, INFO level is used."""
    from ttmp32gme.ttmp32gme import main

    root_logger = logging.getLogger()
    original_level = root_logger.level

    try:
        # Reset to INFO level
        root_logger.setLevel(logging.INFO)

        # Test without --verbose flag
        original_argv = sys.argv
        sys.argv = ["ttmp32gme", "--version"]

        main()

        # Logger should remain at INFO or above (not DEBUG)
        assert root_logger.level >= logging.INFO

    finally:
        # Restore original state
        sys.argv = original_argv
        root_logger.setLevel(original_level)


def test_logger_used_in_fetch_config(caplog):
    """Test that logger.debug is called in fetch_config when verbose mode is enabled."""
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
