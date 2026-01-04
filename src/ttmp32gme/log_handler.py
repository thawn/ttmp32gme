"""Log handler for capturing logs in memory for frontend display."""

import logging
from collections import deque
from threading import Lock
from typing import List

# Get logger for this module
logger = logging.getLogger(__name__)


def apply_log_level(level_str: str) -> None:
    """Apply log level to all relevant loggers.

    Args:
        level_str: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = getattr(logging, level_str, logging.WARNING)

    # Set root logger level
    logging.getLogger().setLevel(level)

    # Set werkzeug logger level
    # When not in DEBUG/INFO mode, suppress werkzeug's INFO logs to reduce clutter
    werkzeug_logger = logging.getLogger("werkzeug")
    if level_str in ["DEBUG", "INFO"]:
        werkzeug_logger.setLevel(level)
    else:
        # Suppress werkzeug's INFO logs (like request logs) when not in verbose mode
        werkzeug_logger.setLevel(logging.WARNING)

    # Set waitress logger level (for production server)
    waitress_logger = logging.getLogger("waitress")
    if level_str in ["DEBUG", "INFO"]:
        waitress_logger.setLevel(level)
    else:
        waitress_logger.setLevel(logging.WARNING)

    logger.info(f"Log level changed to {level_str}")


class MemoryLogHandler(logging.Handler):
    """Custom log handler that stores recent log records in memory."""

    def __init__(self, max_records: int = 1000):
        super().__init__()
        self.max_records = max_records
        self.records: deque[str] = deque(maxlen=max_records)
        self._lock: Lock = Lock()

    def emit(self, record: logging.LogRecord) -> None:
        """Store log record in memory."""
        try:
            msg = self.format(record)
            with self._lock:
                self.records.append(msg)
        except Exception:
            self.handleError(record)

    def get_logs(self, num_lines: int = 100) -> List[str]:
        """Get recent log entries.

        Args:
            num_lines: Number of recent log lines to return

        Returns:
            List of formatted log messages
        """
        with self._lock:
            return list(self.records)[-num_lines:]
