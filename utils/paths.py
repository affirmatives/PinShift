from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "PinShift"


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[1]


def config_dir() -> Path:
    override = os.environ.get("PINSHIFT_APP_SUPPORT_DIR")
    base = Path(override) if override else Path.home() / "Library" / "Application Support" / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def config_file() -> Path:
    return config_dir() / "settings.json"


def log_dir() -> Path:
    base = config_dir() / "logs"
    base.mkdir(parents=True, exist_ok=True)
    return base


def log_file() -> Path:
    return log_dir() / "pinshift.log"


def web_dir() -> Path:
    return project_root() / "web"


def resource_path(*parts: str) -> Path:
    return project_root().joinpath(*parts)


def merged_env() -> dict[str, str]:
    env = os.environ.copy()
    local_bins = [
        str(Path.home() / ".local" / "bin"),
        "/opt/homebrew/bin",
        "/usr/local/bin",
    ]
    env["PATH"] = os.pathsep.join(local_bins + [env.get("PATH", "")])
    return env
