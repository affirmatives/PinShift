from __future__ import annotations

import asyncio
import inspect
import tempfile
import os
from unittest.mock import AsyncMock, patch

from config.app_config import AppConfig
from models.app_settings import AppSettings
from models.device_info import DeviceInfo
from services.device_service import DeviceService
from services.location_service import LocationService
from utils.coord_transform import gcj02_to_wgs84, wgs84_to_gcj02
from utils.sanitizer import sanitize_log_text

with tempfile.TemporaryDirectory(prefix='pinshift-check-') as directory:
    os.environ['PINSHIFT_APP_SUPPORT_DIR'] = directory
    config = AppConfig(AppSettings(last_longitude=120.1, last_latitude=30.2))
    config.save()
    assert AppConfig.load().settings.last_longitude == 120.1
    assert AppSettings.from_dict({'default_zoom': 100}).default_zoom == 20
    assert sanitize_log_text('?key=secret&securityJsCode=secret2') == '?key=***&securityJsCode=***'
    original = (120.15507, 30.274085)
    converted = gcj02_to_wgs84(*wgs84_to_gcj02(*original))
    assert max(abs(a - b) for a, b in zip(original, converted)) < 0.00002
    assert wgs84_to_gcj02(-73.98, 40.75) == (-73.98, 40.75)
    service = LocationService()
    assert not service.set_location(None, None, None)[0]
    device = DeviceInfo('mock', product_version='18.0')
    assert not service.set_location(device, None, None)[0]
    with patch.object(service, '_set_location_async', new=AsyncMock()) as action:
        assert service.set_location(device, *original)[0]
        expected_lng, expected_lat = gcj02_to_wgs84(*original)
        action.assert_awaited_once_with(device, expected_lat, expected_lng)
    with patch('pymobiledevice3.usbmux.list_devices', new=AsyncMock(return_value=[])):
        ok, message, device = DeviceService().scan()
        assert not ok and device is None and 'USB' in message

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.remote.tunnel_service import CoreDeviceTunnelProxy, start_tunnel
from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation
from pymobiledevice3.services.simulate_location import DtSimulateLocation
assert inspect.iscoroutinefunction(create_using_usbmux)
assert inspect.iscoroutinefunction(LocationSimulation.set)
assert inspect.iscoroutinefunction(DtSimulateLocation.set)
print('Core checks passed: settings, coordinate conversion, error handling, mocked USB scan, dependency APIs.')

from services.mac_location_service import MacLocationService
with patch('CoreLocation.CLLocationManager') as manager_class:
    manager_class.locationServicesEnabled.return_value = True
    manager = manager_class.alloc.return_value.init.return_value
    manager.authorizationStatus.return_value = 4
    services = [MacLocationService(), MacLocationService()]
    for native_service in services:
        errors = []
        native_service.locationFailed.connect(errors.append)
        native_service.request_location()
        first_class = type(native_service._delegate)
        native_service.request_location()
        assert not errors, errors
        assert type(native_service._delegate) is first_class
        assert native_service._delegate.service is native_service
    assert type(services[0]._delegate) is type(services[1]._delegate)
    assert manager.startUpdatingLocation.call_count == 4
print('Repeated native location requests passed, including multiple service instances.')
