from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class AppSettings:
    amap_api_key: str = ""
    amap_security_js_code: str = ""
    default_zoom: int = 17
    auto_locate_on_start: bool = True
    remember_last_point: bool = True
    auto_scan_usb_on_start: bool = True
    last_longitude: float | None = None
    last_latitude: float | None = None
    appearance: str = "light"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AppSettings":
        defaults = asdict(cls())
        data = {**defaults, **(payload or {})}
        data["default_zoom"] = max(3, min(20, int(data.get("default_zoom") or 17)))
        data["appearance"] = "dark" if data.get("appearance") == "dark" else "light"
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
