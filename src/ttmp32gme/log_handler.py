"""Log handler for capturing logs in memory for frontend display."""

import logging
from collections import deque
from threading import Lock
from typing import List


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
