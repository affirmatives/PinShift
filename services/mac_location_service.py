from __future__ import annotations

import logging
from functools import lru_cache

from PySide6.QtCore import QObject, Signal


logger = logging.getLogger(__name__)


class MacLocationService(QObject):
    locationUpdated = Signal(float, float)
    locationFailed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._manager = None
        self._delegate = None
        self._has_success = False

    def request_location(self) -> None:
        try:
            import CoreLocation
        except Exception as exc:
            logger.exception("CoreLocation imports failed")
            self.locationFailed.emit(f"CoreLocation 不可用：{exc}")
            return

        try:
            if not CoreLocation.CLLocationManager.locationServicesEnabled():
                self.locationFailed.emit("macOS 定位服务未开启。")
                return

            if self._manager is not None:
                self._manager.stopUpdatingLocation()
            self._has_success = False
            self._delegate = _location_delegate_class().alloc().init()
            self._delegate.service = self
            self._manager = CoreLocation.CLLocationManager.alloc().init()
            self._manager.setDelegate_(self._delegate)
            self._manager.setDesiredAccuracy_(CoreLocation.kCLLocationAccuracyBest)

            if hasattr(self._manager, "requestWhenInUseAuthorization"):
                self._manager.requestWhenInUseAuthorization()

            status = self._manager.authorizationStatus() if hasattr(self._manager, "authorizationStatus") else None
            if status in (
                CoreLocation.kCLAuthorizationStatusDenied,
                CoreLocation.kCLAuthorizationStatusRestricted,
            ):
                self.locationFailed.emit("macOS 定位权限被拒绝或受限。")
                return

            self._manager.startUpdatingLocation()
        except Exception as exc:
            logger.exception("CoreLocation request failed")
            self.locationFailed.emit(f"获取 Mac 当前位置失败：{exc}")


@lru_cache(maxsize=1)
def _location_delegate_class():
    import CoreLocation
    from Foundation import NSObject

    class LocationDelegate(NSObject):
        def locationManager_didUpdateLocations_(self, manager, locations):
            if not locations:
                return
            location = locations[-1]
            coordinate = location.coordinate()
            manager.stopUpdatingLocation()
            self.service._has_success = True
            self.service.locationUpdated.emit(float(coordinate.longitude), float(coordinate.latitude))

        def locationManager_didFailWithError_(self, manager, error):
            status = manager.authorizationStatus()
            if status in (
                CoreLocation.kCLAuthorizationStatusDenied,
                CoreLocation.kCLAuthorizationStatusRestricted,
            ):
                manager.stopUpdatingLocation()
                self.service.locationFailed.emit("macOS 定位权限被拒绝或受限。")
                return
            if self.service._has_success:
                return
            logger.warning("CoreLocation transient failure ignored: %s", error)

        def locationManagerDidChangeAuthorization_(self, manager):
            status = manager.authorizationStatus()
            if status in (
                CoreLocation.kCLAuthorizationStatusAuthorizedAlways,
                CoreLocation.kCLAuthorizationStatusAuthorizedWhenInUse,
            ):
                manager.startUpdatingLocation()
            elif status in (
                CoreLocation.kCLAuthorizationStatusDenied,
                CoreLocation.kCLAuthorizationStatusRestricted,
            ):
                self.service.locationFailed.emit("macOS 定位权限被拒绝或受限。")

    return LocationDelegate
