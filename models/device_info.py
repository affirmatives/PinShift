from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DeviceInfo:
    udid: str
    name: str = "Unknown iPhone"
    product_version: str = "Unknown"
    connection_type: str = "USB"

    @property
    def summary(self) -> str:
        return f"{self.name} | iOS {self.product_version} | {self.connection_type}"
