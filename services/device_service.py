from __future__ import annotations

import asyncio
import logging

from models.device_info import DeviceInfo


logger = logging.getLogger(__name__)


class DeviceService:
    def scan(self) -> tuple[bool, str, DeviceInfo | None]:
        try:
            return asyncio.run(self._scan_async())
        except Exception as exc:
            logger.exception("Device scan failed")
            return False, self._friendly_error(str(exc)), None

    async def _scan_async(self) -> tuple[bool, str, DeviceInfo | None]:
        from pymobiledevice3 import usbmux
        from pymobiledevice3.lockdown import create_using_usbmux

        devices = await usbmux.list_devices()
        usb_devices = [device for device in devices if getattr(device, "is_usb", False)]

        if not usb_devices:
            return False, "未检测到通过 USB 连接的 iPhone。请确认数据线连接，并在 iPhone 上信任此电脑。", None
        if len(usb_devices) > 1:
            udids = ", ".join(device.serial for device in usb_devices)
            return False, f"检测到多个设备，请暂时只连接一台 iPhone。UDID：{udids}", None

        device = usb_devices[0]
        lockdown = None
        try:
            lockdown = await create_using_usbmux(
                serial=device.serial,
                autopair=True,
                connection_type=device.connection_type,
                pair_timeout=15,
            )
            name = await self._safe_get_value(lockdown, "DeviceName") or "iPhone"
            version = getattr(lockdown, "product_version", None) or await self._safe_get_value(lockdown, "ProductVersion")
            return True, "检测到设备。", DeviceInfo(
                udid=device.serial,
                name=str(name),
                product_version=str(version or "Unknown"),
                connection_type="USB",
            )
        finally:
            if lockdown is not None and hasattr(lockdown, "close"):
                await lockdown.close()

    async def _safe_get_value(self, lockdown, key: str):
        try:
            return await lockdown.get_value(key=key)
        except TypeError:
            return await lockdown.get_value(None, key)
        except Exception:
            logger.exception("Failed to read lockdown value: %s", key)
            return None

    def _friendly_error(self, message: str) -> str:
        lowered = message.lower()
        if "operation not permitted" in lowered or "permission" in lowered:
            return "USB 访问被 macOS 拒绝。请重新打开应用，必要时在系统设置中允许此应用访问设备。"
        if "pair" in lowered or "trust" in lowered or "user refused" in lowered:
            return "iPhone 尚未信任当前 Mac，请解锁手机并点击“信任”。"
        if "developer" in lowered:
            return "iPhone 可能未开启开发者模式，请在设置中开启后重试。"
        if "no device" in lowered or "not connected" in lowered:
            return "未检测到通过 USB 连接的 iPhone。请确认数据线连接，并在 iPhone 上信任此电脑。"
        if "usbmux" in lowered:
            return f"连接 usbmuxd 失败，请重新插拔 iPhone 后重试。原始错误：{message}"
        return message or "设备扫描失败。"
