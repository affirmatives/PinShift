from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWebEngineCore import QWebEnginePage

from utils.sanitizer import sanitize_log_text
from utils.logger import get_logger


logger = get_logger(__name__)


class PinShiftWebPage(QWebEnginePage):
    consoleMessage = Signal(str)

    def javaScriptConsoleMessage(
        self,
        level: QWebEnginePage.JavaScriptConsoleMessageLevel,
        message: str,
        line_number: int,
        source_id: str,
    ) -> None:
        clean_source = sanitize_log_text(source_id)
        clean_message = sanitize_log_text(message)
        logger.info("JS[%s] %s:%s %s", level.name, clean_source, line_number, clean_message)
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            self.consoleMessage.emit(f"地图错误：{clean_message}")
