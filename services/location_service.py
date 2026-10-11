from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import shlex
import subprocess
import sys
import time
import uuid
from contextlib import suppress
from pathlib import Path
from packaging.version import Version

from models.device_info import DeviceInfo
from services.tunnel_service import TunnelService
from utils.coord_transform import gcj02_to_wgs84
from utils.paths import config_dir


logger = logging.getLogger(__name__)


class LocationService:
    def __init__(
        self,
        tunnel_service: TunnelService | None = None,
    ) -> None:
        self.tunnel_service = tunnel_service or TunnelService()

    def set_location(self, device: DeviceInfo | None, longitude: float | None, latitude: float | None) -> tuple[bool, str]:
        if device is None:
            return False, "未检测到 iPhone，无法设置虚拟定位。"
        if longitude is None or latitude is None:
            return False, "请先在地图上选择一个位置。"
        map_longitude, map_latitude = longitude, latitude
        longitude, latitude = gcj02_to_wgs84(map_longitude, map_latitude)
        if (abs(map_longitude - longitude) > 0.000001) or (abs(map_latitude - latitude) > 0.000001):
            logger.info(
                "Converted selected location GCJ-02 %.6f, %.6f to WGS-84 %.6f, %.6f",
                map_longitude,
                map_latitude,
                longitude,
                latitude,
            )
        try:
            asyncio.run(self._set_location_async(device, latitude, longitude))
            return True, "虚拟定位设置成功。"
        except Exception as exc:
            helper_message = None
            if self._can_retry_with_privileged_helper(device, str(exc)):
                logger.info("Retrying set location with privileged helper because tunnel creation failed.")
                ok, message = self._run_privileged_helper(device, "set", longitude, latitude)
                if ok:
                    return True, message
                helper_message = message
                logger.error("Privileged helper failed: %s", message)
            logger.exception("Set virtual location failed")
            return False, helper_message or self._location_error(str(exc), device)

    def clear_location(self, device: DeviceInfo | None) -> tuple[bool, str]:
        if device is None:
            return False, "未检测到 iPhone，无法清除虚拟定位。"
        try:
            asyncio.run(self._clear_location_async(device))
            return True, "清除虚拟定位成功。"
        except Exception as exc:
            helper_message = None
            if self._can_retry_with_privileged_helper(device, str(exc)):
                logger.info("Retrying clear location with privileged helper because tunnel creation failed.")
                ok, message = self._run_privileged_helper(device, "clear")
                if ok:
                    return True, message
                helper_message = message
                logger.error("Privileged helper failed: %s", message)
            logger.exception("Clear virtual location failed")
            return False, helper_message or self._location_error(str(exc), device)

    async def _create_lockdown(self, device: DeviceInfo):
        from pymobiledevice3.lockdown import create_using_usbmux

        return await create_using_usbmux(serial=device.udid, autopair=True, pair_timeout=15)

    async def _set_location_async(self, device: DeviceInfo, latitude: float, longitude: float) -> None:
        lockdown = await self._create_lockdown(device)
        try:
            if self._is_ios_17_or_newer(device.product_version):
                await self._with_ios17_location_service(lockdown, device, "set", latitude, longitude)
            else:
                from pymobiledevice3.services.simulate_location import DtSimulateLocation

                await DtSimulateLocation(lockdown).set(latitude, longitude)
        finally:
            if hasattr(lockdown, "close"):
                await lockdown.close()

    async def _clear_location_async(self, device: DeviceInfo) -> None:
        lockdown = await self._create_lockdown(device)
        try:
            if self._is_ios_17_or_newer(device.product_version):
                await self._with_ios17_location_service(lockdown, device, "clear")
            else:
                from pymobiledevice3.services.simulate_location import DtSimulateLocation

                await DtSimulateLocation(lockdown).clear()
        finally:
            if hasattr(lockdown, "close"):
                await lockdown.close()

    async def _with_ios17_location_service(
        self,
        lockdown,
        device: DeviceInfo,
        action: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> None:
        from pymobiledevice3.remote.common import TunnelProtocol
        from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
        from pymobiledevice3.remote.tunnel_service import CoreDeviceTunnelProxy, start_tunnel
        from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
        from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation
        from pymobiledevice3.tunneld.api import get_tunneld_device_by_udid

        rsd = await self._get_existing_tunneld_rsd(device.udid)
        if rsd is not None:
            logger.info("Using existing tunneld RSD for %s", device.udid)
            try:
                await self._run_dvt_location_action(rsd, action, latitude, longitude)
                return
            finally:
                await rsd.close()

        logger.info("Creating USB CoreDevice tunnel for iOS %s device %s", device.product_version, device.udid)
        proxy = await CoreDeviceTunnelProxy.create(lockdown)
        try:
            async with start_tunnel(proxy, protocol=TunnelProtocol.TCP) as tunnel:
                logger.info("USB CoreDevice tunnel ready: %s %s", tunnel.address, tunnel.port)
                rsd = RemoteServiceDiscoveryService((tunnel.address, tunnel.port), name=tunnel.interface)
                try:
                    await rsd.connect()
                    await self._run_dvt_location_action(rsd, action, latitude, longitude)
                finally:
                    with suppress(Exception):
                        await rsd.close()
        finally:
            with suppress(Exception):
                await proxy.close()

    async def _get_existing_tunneld_rsd(self, udid: str):
        from pymobiledevice3.exceptions import TunneldConnectionError
        from pymobiledevice3.tunneld.api import get_tunneld_device_by_udid

        try:
            return await get_tunneld_device_by_udid(udid)
        except TunneldConnectionError:
            logger.info("No existing tunneld server found; will create an in-app USB tunnel.")
            return None
        except Exception:
            logger.exception("Failed to query existing tunneld; will create an in-app USB tunnel.")
            return None

    async def _run_dvt_location_action(
        self,
        service_provider,
        action: str,
        latitude: float | None,
        longitude: float | None,
    ) -> None:
        from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
        from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation

        async with DvtProvider(service_provider) as dvt, LocationSimulation(dvt) as location_simulation:
            if action == "set":
                if latitude is None or longitude is None:
                    raise ValueError("missing latitude or longitude")
                await location_simulation.set(latitude, longitude)
            elif action == "clear":
                await location_simulation.clear()
            else:
                raise ValueError(f"unsupported location action: {action}")

    def hold_location_until_stopped(
        self,
        device: DeviceInfo,
        longitude: float,
        latitude: float,
        status_file: str | None = None,
        command_file: str | None = None,
    ) -> tuple[bool, str]:
        try:
            asyncio.run(self._hold_location_until_stopped_async(device, latitude, longitude, status_file, command_file))
            return True, "虚拟定位会话已结束。"
        except Exception as exc:
            logger.exception("Hold virtual location failed")
            message = self._location_error(str(exc), device)
            if status_file:
                self._write_helper_status(status_file, False, message)
            return False, message

    async def _hold_location_until_stopped_async(
        self,
        device: DeviceInfo,
        latitude: float,
        longitude: float,
        status_file: str | None,
        command_file: str | None,
    ) -> None:
        if not self._is_ios_17_or_newer(device.product_version):
            await self._set_location_async(device, latitude, longitude)
            if status_file:
                self._write_helper_status(status_file, True, "虚拟定位设置成功。")
            return

        from pymobiledevice3.remote.common import TunnelProtocol
        from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
        from pymobiledevice3.remote.tunnel_service import CoreDeviceTunnelProxy, start_tunnel
        from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
        from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation

        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            with suppress(NotImplementedError):
                loop.add_signal_handler(sig, stop_event.set)

        lockdown = await self._create_lockdown(device)
        try:
            proxy = await CoreDeviceTunnelProxy.create(lockdown)
            try:
                async with start_tunnel(proxy, protocol=TunnelProtocol.TCP) as tunnel:
                    rsd = RemoteServiceDiscoveryService((tunnel.address, tunnel.port), name=tunnel.interface)
                    try:
                        await rsd.connect()
                        async with DvtProvider(rsd) as dvt, LocationSimulation(dvt) as location_simulation:
                            await location_simulation.set(latitude, longitude)
                            if status_file:
                                self._write_helper_status(status_file, True, "虚拟定位设置成功。")
                            if command_file:
                                await self._watch_location_commands(
                                    location_simulation,
                                    command_file,
                                    status_file,
                                    stop_event,
                                )
                            else:
                                await stop_event.wait()
                    finally:
                        with suppress(Exception):
                            await rsd.close()
            finally:
                with suppress(Exception):
                    await proxy.close()
        finally:
            if hasattr(lockdown, "close"):
                await lockdown.close()

    def _write_helper_status(self, status_file: str, ok: bool, message: str) -> None:
        self._write_helper_status_payload(status_file, {"ok": ok, "message": message})

    def _write_helper_status_payload(self, status_file: str, payload: dict) -> None:
        Path(status_file).write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )

    async def _watch_location_commands(
        self,
        location_simulation,
        command_file: str,
        status_file: str | None,
        stop_event: asyncio.Event,
    ) -> None:
        command_path = Path(command_file)
        last_request_id = ""
        while not stop_event.is_set():
            if command_path.exists():
                try:
                    payload = json.loads(command_path.read_text(encoding="utf-8"))
                    request_id = str(payload.get("request_id") or "")
                    if request_id and request_id != last_request_id:
                        last_request_id = request_id
                        action = payload.get("action")
                        if action == "set":
                            latitude = float(payload["latitude"])
                            longitude = float(payload["longitude"])
                            await location_simulation.set(latitude, longitude)
                            message = "虚拟定位设置成功。"
                            should_stop = False
                        elif action == "clear":
                            await location_simulation.clear()
                            message = "清除虚拟定位成功。"
                            should_stop = bool(payload.get("stop", True))
                        else:
                            raise ValueError(f"unsupported helper command: {action}")
                        if status_file:
                            self._write_helper_status_payload(
                                status_file,
                                {"ok": True, "message": message, "request_id": request_id, "action": action},
                            )
                        with suppress(FileNotFoundError):
                            command_path.unlink()
                        if should_stop:
                            stop_event.set()
                            break
                except Exception as exc:
                    logger.exception("Failed to process location helper command")
                    if status_file:
                        self._write_helper_status_payload(
                            status_file,
                            {
                                "ok": False,
                                "message": self._location_error(str(exc), DeviceInfo("", "iPhone", "", "USB")),
                                "request_id": str(payload.get("request_id") or "") if "payload" in locals() else "",
                            },
                        )
                    with suppress(FileNotFoundError):
                        command_path.unlink()
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=0.5)
            except asyncio.TimeoutError:
                pass

    def _is_ios_17_or_newer(self, version: str) -> bool:
        try:
            return Version(str(version)) >= Version("17.0")
        except Exception:
            return False

    def _location_error(self, message: str, device: DeviceInfo) -> str:
        lowered = message.lower()
        if "operation not permitted" in lowered or "permission" in lowered:
            return "定位设置失败：macOS 拒绝创建 iOS tunnel 或访问 USB 设备，请重新打开应用后重试。"
        if "accessdenied" in lowered or "requires root" in lowered or "sudo" in lowered:
            return "定位设置失败：创建 iOS tunnel 需要更高权限。当前版本会自动尝试应用内 tunnel，但 macOS 拒绝了该操作。"
        if "developer" in lowered:
            return "定位设置失败：请确认 iPhone 已开启开发者模式。"
        if "no such service" in lowered and "dtservicehub" in lowered:
            return "定位设置失败：iOS tunnel 已建立，但设备未开放 DVT 定位服务。请确认 iPhone 已开启开发者模式并解锁。"
        if "tunnel" in lowered or "rsd" in lowered or self.tunnel_service.is_required(device.product_version):
            hint = self.tunnel_service.check_hint(device.product_version)
            return f"定位设置失败：可能需要建立 iOS tunnel。{hint}\n原始错误：{message}"
        if "not paired" in lowered or "trust" in lowered:
            return "定位设置失败：请解锁 iPhone 并信任当前 Mac。"
        return f"定位设置失败：{message or '未知错误'}"

    def _can_retry_with_privileged_helper(self, device: DeviceInfo, message: str) -> bool:
        if os.environ.get("PINSHIFT_PRIVILEGED_HELPER") == "1":
            return False
        if not self._is_ios_17_or_newer(device.product_version):
            return False
        lowered = message.lower()
        return "failed to create any utun interface" in lowered or "pytun" in lowered

    def _run_privileged_helper(
        self,
        device: DeviceInfo,
        action: str,
        longitude: float | None = None,
        latitude: float | None = None,
    ) -> tuple[bool, str]:
        if action == "set":
            return self._start_privileged_location_session(device, longitude, latitude)
        if action == "clear":
            ok, message = self._send_helper_command("clear", stop=True)
            if ok:
                return True, message
        command = self._helper_command(device, action, longitude, latitude)
        shell_command = " ".join(shlex.quote(part) for part in command)
        shell_command = self._kill_previous_session_command() + shell_command
        try:
            result = self._run_admin_shell(shell_command, timeout=180)
        except subprocess.TimeoutExpired:
            return False, "管理员权限定位 helper 执行超时。"
        except Exception as exc:
            logger.exception("Failed to run privileged helper")
            return False, f"无法启动管理员权限定位 helper：{exc}"

        output = (result.stdout or "").strip()
        error = (result.stderr or "").strip()
        if result.returncode != 0:
            if result.returncode == 1 and "User canceled" in error:
                return False, "已取消管理员授权，无法创建 iOS tunnel。"
            return False, error or output or f"管理员权限定位 helper 失败，退出码 {result.returncode}。"

        try:
            payload = json.loads(output.splitlines()[-1])
        except Exception:
            logger.error("Unexpected privileged helper output: stdout=%r stderr=%r", output, error)
            return False, output or error or "管理员权限定位 helper 未返回有效结果。"

        if payload.get("ok"):
            return True, str(payload.get("message") or ("虚拟定位设置成功。" if action == "set" else "清除虚拟定位成功。"))
        return False, str(payload.get("message") or "管理员权限定位 helper 执行失败。")

    def _start_privileged_location_session(
        self,
        device: DeviceInfo,
        longitude: float | None,
        latitude: float | None,
    ) -> tuple[bool, str]:
        status_file = config_dir() / "location_helper_status.json"
        pid_file = config_dir() / "location_helper.pid"
        command_file = config_dir() / "location_helper_command.json"
        output_file = config_dir() / "logs" / "location_helper.log"
        for path in (status_file,):
            with suppress(FileNotFoundError):
                path.unlink()

        ok, message = self._send_helper_command("set", longitude=longitude, latitude=latitude)
        if ok:
            return True, message
        restart_existing_helper = "未响应" in message

        command = self._helper_command(device, "set", longitude, latitude)
        command.extend(["--hold", "--status-file", str(status_file), "--command-file", str(command_file)])
        shell_command = " ".join(shlex.quote(part) for part in command)
        prefix_command = self._kill_previous_session_command() if restart_existing_helper else self._cleanup_stale_session_command()
        launch_command = (
            prefix_command
            + f"( {shell_command} </dev/null > {shlex.quote(str(output_file))} 2>&1 ) & echo $! > {shlex.quote(str(pid_file))}"
        )
        try:
            result = self._run_admin_shell(launch_command, timeout=60)
        except subprocess.TimeoutExpired:
            logger.exception("Privileged location helper launch timed out")
            return False, "管理员授权窗口等待超时。若已输入密码，请稍等几秒后再点一次设置；如果仍失败，请退出 PinShift 后重新打开。"
        except Exception as exc:
            logger.exception("Failed to launch privileged location helper")
            return False, f"无法启动管理员权限定位 helper：{exc}"
        if result.returncode != 0:
            error = (result.stderr or result.stdout or "").strip()
            if "User canceled" in error:
                return False, "已取消管理员授权，无法创建 iOS tunnel。"
            return False, error or "启动管理员权限定位 helper 失败。"

        deadline = time.monotonic() + 75
        while time.monotonic() < deadline:
            if status_file.exists():
                try:
                    payload = json.loads(status_file.read_text(encoding="utf-8"))
                    return bool(payload.get("ok")), str(payload.get("message") or "管理员权限定位 helper 已返回。")
                except Exception:
                    logger.exception("Failed to read helper status")
                    return False, "无法读取管理员权限定位 helper 状态。"
            time.sleep(0.5)
        return False, "管理员权限定位 helper 启动超时，请查看日志 location_helper.log。"

    def _send_helper_command(
        self,
        action: str,
        longitude: float | None = None,
        latitude: float | None = None,
        stop: bool = False,
        timeout: float = 12,
    ) -> tuple[bool, str]:
        pid_file = config_dir() / "location_helper.pid"
        if not self._is_helper_alive(pid_file):
            return False, "管理员权限定位 helper 尚未运行。"

        status_file = config_dir() / "location_helper_status.json"
        command_file = config_dir() / "location_helper_command.json"
        request_id = uuid.uuid4().hex
        payload = {"action": action, "request_id": request_id, "stop": stop}
        if action == "set":
            if longitude is None or latitude is None:
                return False, "缺少定位坐标。"
            payload.update({"longitude": longitude, "latitude": latitude})

        with suppress(FileNotFoundError):
            status_file.unlink()
        command_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if status_file.exists():
                try:
                    response = json.loads(status_file.read_text(encoding="utf-8"))
                except Exception:
                    logger.exception("Failed to read helper command status")
                    return False, "无法读取管理员权限定位 helper 状态。"
                if response.get("request_id") == request_id:
                    return bool(response.get("ok")), str(response.get("message") or "管理员权限定位 helper 已返回。")
            time.sleep(0.25)
        logger.warning("Existing privileged helper did not respond to %s command; will restart it.", action)
        return False, "管理员权限定位 helper 未响应。"

    def _is_helper_alive(self, pid_file: Path) -> bool:
        if not pid_file.exists():
            return False
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            with suppress(FileNotFoundError):
                pid_file.unlink()
            return False
        except PermissionError:
            return True
        except Exception:
            with suppress(FileNotFoundError):
                pid_file.unlink()
            return False

    def _cleanup_stale_session_command(self) -> str:
        pid_file = config_dir() / "location_helper.pid"
        if not pid_file.exists():
            return ""
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
        except Exception:
            with suppress(FileNotFoundError):
                pid_file.unlink()
            return ""
        if self._is_helper_alive(pid_file):
            return ""
        return f"kill {pid} >/dev/null 2>&1 || true; rm -f {shlex.quote(str(pid_file))}; "

    def _kill_previous_session_command(self) -> str:
        pid_file = config_dir() / "location_helper.pid"
        command_file = config_dir() / "location_helper_command.json"
        if not pid_file.exists():
            return f"rm -f {shlex.quote(str(command_file))}; "
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
        except Exception:
            return f"rm -f {shlex.quote(str(pid_file))} {shlex.quote(str(command_file))}; "
        return (
            f"kill {pid} >/dev/null 2>&1 || true; "
            f"rm -f {shlex.quote(str(pid_file))} {shlex.quote(str(command_file))}; "
        )

    def _run_admin_shell(self, shell_command: str, timeout: int) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "osascript",
                "-e",
                f"do shell script {self._applescript_string(shell_command)} with administrator privileges",
            ],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )

    def _applescript_string(self, value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def _helper_command(
        self,
        device: DeviceInfo,
        action: str,
        longitude: float | None,
        latitude: float | None,
    ) -> list[str]:
        env_prefix = [
            "/usr/bin/env",
            "PINSHIFT_PRIVILEGED_HELPER=1",
            f"PINSHIFT_APP_SUPPORT_DIR={config_dir()}",
        ]
        if getattr(sys, "frozen", False):
            command = [sys.executable]
        else:
            command = [sys.executable, str(Path(__file__).resolve().parents[1] / "main.py")]

        command.extend([
            "--location-helper",
            "--action",
            action,
            "--udid",
            device.udid,
            "--version",
            device.product_version,
            "--name",
            "iPhone",
        ])
        if action == "set":
            command.extend([
                "--longitude",
                str(longitude),
                "--latitude",
                str(latitude),
            ])
        return env_prefix + command
