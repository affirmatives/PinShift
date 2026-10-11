from __future__ import annotations

import json
from dataclasses import dataclass

from models.app_settings import AppSettings
from utils.paths import config_file


@dataclass(slots=True)
class AppConfig:
    settings: AppSettings

    @classmethod
    def load(cls) -> "AppConfig":
        path = config_file()
        if not path.exists():
            return cls(AppSettings())
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return cls(AppSettings.from_dict(payload))
        except Exception:
            return cls(AppSettings())

    def save(self) -> None:
        config_file().write_text(
            json.dumps(self.settings.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @property
    def path(self) -> str:
        return str(config_file())
