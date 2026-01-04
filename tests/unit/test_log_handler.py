"""Unit tests for MemoryLogHandler."""

import logging
import sys
from pathlib import Path

# Add src to path to import ttmp32gme
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_memory_log_handler_stores_logs():
    """Test that MemoryLogHandler stores log records."""
    from ttmp32gme.ttmp32gme import MemoryLogHandler

    handler = MemoryLogHandler(max_records=10)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    logger = logging.getLogger("test_handler")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Log some messages
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")

    # Get logs
    logs = handler.get_logs()

    assert len(logs) == 3
    assert "Debug message" in logs[0]
    assert "Info message" in logs[1]
    assert "Warning message" in logs[2]


def test_memory_log_handler_respects_max_records():
    """Test that MemoryLogHandler respects max_records limit."""
    from ttmp32gme.ttmp32gme import MemoryLogHandler

    handler = MemoryLogHandler(max_records=5)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger = logging.getLogger("test_max_records")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Log more than max_records
    for i in range(10):
        logger.info(f"Message {i}")

    # Get logs
    logs = handler.get_logs()

    # Should only have last 5 messages
    assert len(logs) == 5
    assert "Message 5" in logs[0]
    assert "Message 9" in logs[4]


def test_memory_log_handler_get_logs_with_limit():
    """Test that get_logs respects num_lines parameter."""
    from ttmp32gme.ttmp32gme import MemoryLogHandler

    handler = MemoryLogHandler(max_records=100)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger = logging.getLogger("test_limit")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Log 20 messages
    for i in range(20):
        logger.info(f"Message {i}")

    # Get only last 5 logs
    logs = handler.get_logs(num_lines=5)

    assert len(logs) == 5
    assert "Message 15" in logs[0]
    assert "Message 19" in logs[4]
