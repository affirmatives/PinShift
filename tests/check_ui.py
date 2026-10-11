from __future__ import annotations

import os
import sys
import tempfile
from concurrent.futures import Future
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from config.app_config import AppConfig
from models.app_settings import AppSettings
from models.device_info import DeviceInfo
from ui.main_window import MainWindow

support = tempfile.TemporaryDirectory(prefix='pinshift-theme-check-')
os.environ['PINSHIFT_APP_SUPPORT_DIR'] = support.name
app = QApplication([])
window = MainWindow(AppConfig(AppSettings(auto_locate_on_start=False, auto_scan_usb_on_start=False)))
window.resize(1280, 820)
window.show()
errors = []


def guarded(action):
    def run():
        try:
            action()
        except Exception as exc:
            errors.append(exc)
            app.quit()
    return run


def inspect_dark(theme):
    try:
        assert theme == 'dark', theme
        assert AppConfig.load().settings.appearance == 'dark'
        assert window.night_button.property('active')
        assert window.main_page.longitude == 121.5
        assert window.main_page.latitude == 31.2
        status = window.main_page.status_widget
        status.set_device('已连接', DeviceInfo('00008101-0012345678901234', '测试 iPhone', '18.0'))
        assert status.udid_toggle.isEnabled()
        status.udid_toggle.click()
        assert '00008101-0012345678901234' in status.udid_label.text()
        window.grab().save('/private/tmp/pinshift-dark.png')
        window._switch_page(window.settings_page)
        window.grab().save('/private/tmp/pinshift-settings-dark.png')
        window._switch_page(window.main_page)
        window.day_button.click()
        QTimer.singleShot(400, guarded(finish))
    except Exception as exc:
        errors.append(exc)
        app.quit()


def finish():
    assert AppConfig.load().settings.appearance == 'light'
    assert window.day_button.property('active')
    assert window.main_page.longitude == 121.5
    window.grab().save('/private/tmp/pinshift-light-connected.png')
    app.quit()


def start():
    page = window.main_page
    original_executor = page.executor
    calls = []
    class MockExecutor:
        def submit(self, method, *args):
            calls.append(args)
            result = Future()
            result.set_result((True, '模拟定位成功'))
            return result
    page.executor = MockExecutor()
    original_warning = QMessageBox.warning
    warnings = []
    QMessageBox.warning = lambda *args: warnings.append(args)
    try:
        page.longitude_input.setText('-77.036546')
        page.latitude_input.setText('38.897660')
        page.set_button.click()
        assert calls == [(None, -77.036546, 38.897660)]
        assert AppConfig.load().settings.last_longitude == -77.036546
        for longitude, latitude in [('', '0'), ('nan', '0'), ('181', '0'), ('0', '-91'), ('0', 'inf')]:
            page.longitude_input.setText(longitude)
            page.latitude_input.setText(latitude)
            page.set_button.click()
        assert len(calls) == 1
        assert len(warnings) == 5
        page.longitude_input.setText('0')
        page.latitude_input.setText('0')
        page.set_button.click()
        assert calls[-1] == (None, 0.0, 0.0)
    finally:
        page.executor = original_executor
        QMessageBox.warning = original_warning
    window.grab().save('/private/tmp/pinshift-light.png')
    window.main_page.on_point_selected(121.5, 31.2)
    assert page.longitude_input.text() == '121.5'
    assert page.latitude_input.text() == '31.2'
    window.night_button.click()
    QTimer.singleShot(400, lambda: window.main_page.web_page.runJavaScript(
        'document.documentElement.dataset.theme', inspect_dark))

QTimer.singleShot(2000, guarded(start))
QTimer.singleShot(12000, lambda: (errors.append(RuntimeError('UI check timed out')), app.quit()))
app.exec()
window.main_page.executor.shutdown(wait=True)
if errors:
    raise errors[0]
assert Path('/private/tmp/pinshift-dark.png').exists()
print('UI checks passed: saved day/night mode, web theme, preserved selection, connected-device controls.')
support.cleanup()
