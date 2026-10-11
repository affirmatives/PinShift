from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from utils.paths import log_file


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    try:
        file_handler = RotatingFileHandler(
            log_file(),
            maxBytes=2 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
        root.info("PinShift logging initialized: %s", log_file())
    except OSError:
        root.exception("PinShift file logging is unavailable: %s", log_file())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
