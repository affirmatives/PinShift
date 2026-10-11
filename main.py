from __future__ import annotations

import argparse
import json
import sys

from utils.logger import configure_logging


def run_location_helper(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="PinShift location helper")
    parser.add_argument("--action", choices=["set", "clear"], required=True)
    parser.add_argument("--udid", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--name", default="iPhone")
    parser.add_argument("--longitude", type=float)
    parser.add_argument("--latitude", type=float)
    parser.add_argument("--hold", action="store_true")
    parser.add_argument("--status-file")
    parser.add_argument("--command-file")
    args = parser.parse_args(argv)

    configure_logging()
    from models.device_info import DeviceInfo
    from services.location_service import LocationService

    device = DeviceInfo(
        udid=args.udid,
        name=args.name,
        product_version=args.version,
        connection_type="USB",
    )
    service = LocationService()
    if args.action == "set" and args.hold:
        ok, message = service.hold_location_until_stopped(
            device,
            args.longitude,
            args.latitude,
            args.status_file,
            args.command_file,
        )
    elif args.action == "set":
        ok, message = service.set_location(device, args.longitude, args.latitude)
    else:
        ok, message = service.clear_location(device)
    print(json.dumps({"ok": ok, "message": message}, ensure_ascii=False), flush=True)
    return 0


def run_gui() -> int:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from config.app_config import AppConfig
    from config.app_info import APP_NAME, APP_VERSION
    from ui.main_window import MainWindow

    configure_logging()
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, False)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_NAME)

    config = AppConfig.load()
    window = MainWindow(config)
    window.resize(1280, 820)
    window.show()

    return app.exec()


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--location-helper":
        return run_location_helper(sys.argv[2:])
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
