from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QTextEdit

from utils.logger import get_logger
from utils.sanitizer import sanitize_log_text


logger = get_logger(__name__)


class LogPanel(QTextEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setMinimumHeight(120)
        self.setPlaceholderText("操作日志")

    def append_log(self, message: str) -> None:
        message = sanitize_log_text(message)
        timestamp = datetime.now().strftime("%H:%M:%S")
        logger.info(message)
        self.append(f"[{timestamp}] {message}")
