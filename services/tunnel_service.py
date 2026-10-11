from __future__ import annotations

class TunnelService:
    def check_hint(self, ios_version: str) -> str:
        major = self._major_version(ios_version)
        if major >= 17:
            return "iOS 17+ 设备可能需要先建立 tunnel：pymobiledevice3 remote tunneld"
        return "当前系统版本通常不需要额外 tunnel。"

    def is_required(self, ios_version: str) -> bool:
        return self._major_version(ios_version) >= 17

    def _major_version(self, version: str) -> int:
        try:
            return int(str(version).split(".")[0])
        except Exception:
            return 0
