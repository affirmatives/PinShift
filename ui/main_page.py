from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from bridges.map_bridge import MapBridge
from config.app_config import AppConfig
from models.device_info import DeviceInfo
from services.device_service import DeviceService
from services.location_service import LocationService
from services.mac_location_service import MacLocationService
from ui.widgets.log_panel import LogPanel
from ui.widgets.status_bar_widget import StatusBarWidget
from ui.web_page import PinShiftWebPage
from utils.coord_transform import wgs84_to_gcj02
from utils.paths import web_dir


class MainPage(QWidget):
    logMessage = Signal(str)
    scanFinished = Signal(bool, str, object)
    actionFinished = Signal(str, bool, str)

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="pinshift")
        self.device_service = DeviceService()
        self.location_service = LocationService()
        self.location_service_mac = MacLocationService()
        self.device: DeviceInfo | None = None
        self.longitude: float | None = config.settings.last_longitude
        self.latitude: float | None = config.settings.last_latitude
        self.current_longitude: float | None = None
        self.current_latitude: float | None = None

        self.bridge = MapBridge()
        self.bridge.pointSelected.connect(self.on_point_selected)
        self.bridge.logMessage.connect(self.add_log)
        self.bridge.currentLocationReceived.connect(self.on_current_location)
        self.bridge.currentLocationRequested.connect(self.request_current_location)

        self.web_channel = QWebChannel()
        self.web_channel.registerObject("pinShiftBridge", self.bridge)

        self.map_view = QWebEngineView()
        self.web_page = PinShiftWebPage(self.map_view)
        self.web_page.consoleMessage.connect(self.add_log)
        self.map_view.setPage(self.web_page)
        self.web_page.setWebChannel(self.web_channel)
        self.web_page.featurePermissionRequested.connect(self._grant_web_permission)
        self.map_view.loadFinished.connect(self._on_map_loaded)
        self.map_view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )

        self.scan_button = QPushButton("扫描设备")
        self.set_button = QPushButton("设置虚拟定位")
        self.set_button.setObjectName("primaryButton")
        self.clear_button = QPushButton("清除虚拟定位")
        self.copy_button = QPushButton("复制")
        self.copy_button.setProperty("compact", True)
        self.copy_button.setFixedWidth(58)

        self.longitude_label = QLabel("经度：-")
        self.latitude_label = QLabel("纬度：-")
        self.status_widget = StatusBarWidget()
        self.log_panel = LogPanel()

        self._build_layout()
        self._connect_signals()
        self._update_coordinate_labels()
        self.load_map()
        if self.config.settings.auto_locate_on_start:
            self.request_current_location()

        if self.config.settings.auto_scan_usb_on_start:
            self.scan_device()

    def _build_layout(self) -> None:
        coord_box = QFrame()
        coord_box.setObjectName("coordBox")
        coord_box.setMinimumHeight(78)
        coord_box.setCursor(Qt.CursorShape.PointingHandCursor)
        coord_box.mousePressEvent = lambda event: self.copy_coordinates()
        coord_layout = QGridLayout(coord_box)
        coord_layout.addWidget(self.longitude_label, 0, 0)
        coord_layout.addWidget(self.latitude_label, 1, 0)
        coord_layout.addWidget(self.copy_button, 0, 1, 2, 1)

        actions = QVBoxLayout()
        actions.setContentsMargins(16, 16, 16, 16)
        actions.setSpacing(12)
        def section(title: str) -> QLabel:
            label = QLabel(title)
            label.setObjectName("sectionTitle")
            return label
        actions.addWidget(section("选点坐标"))
        actions.addWidget(coord_box)
        actions.addWidget(self.scan_button)
        actions.addSpacing(8)
        actions.addWidget(section("虚拟定位"))
        actions.addWidget(self.set_button)
        actions.addWidget(self.clear_button)
        actions.addSpacing(8)
        actions.addWidget(section("活动日志"))
        actions.addWidget(self.log_panel, 1)

        side = QWidget()
        side.setObjectName("sidebar")
        side.setMinimumWidth(340)
        side.setMaximumWidth(430)
        side.setLayout(actions)

        splitter = QSplitter()
        splitter.setHandleWidth(12)
        splitter.addWidget(side)
        splitter.addWidget(self.map_view)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter, 1)

    def _connect_signals(self) -> None:
        self.scan_button.clicked.connect(self.scan_device)
        self.set_button.clicked.connect(self.set_virtual_location)
        self.clear_button.clicked.connect(self.clear_virtual_location)
        self.copy_button.clicked.connect(self.copy_coordinates)
        self.logMessage.connect(self.log_panel.append_log)
        self.scanFinished.connect(self._on_scan_finished)
        self.actionFinished.connect(self._on_action_finished)
        self.location_service_mac.locationUpdated.connect(self.on_current_location)
        self.location_service_mac.locationFailed.connect(self.on_current_location_failed)

    def load_map(self) -> None:
        key = self.config.settings.amap_api_key.strip()
        security_js_code = self.config.settings.amap_security_js_code.strip()
        if not key:
            self.add_log("高德地图 Key 未配置，请先到配置页填写。")
        elif not security_js_code:
            self.add_log("高德地图安全密钥未配置，地图可能无法通过鉴权。")

        query = {
            "key": key,
            "securityJsCode": security_js_code,
            "zoom": self.config.settings.default_zoom,
            "autoLocate": "1" if self.config.settings.auto_locate_on_start else "0",
            "theme": self.config.settings.appearance,
        }
        if self.longitude is not None and self.latitude is not None:
            query["lastLng"] = self.longitude
            query["lastLat"] = self.latitude

        map_file = Path(web_dir() / "map.html")
        url = QUrl.fromLocalFile(str(map_file))
        url.setQuery(urlencode(query))
        self.map_view.load(url)

    def apply_map_theme(self) -> None:
        import json
        self.map_view.page().runJavaScript(
            self._map_call_js("setTheme", json.dumps(self.config.settings.appearance))
        )

    def scan_device(self) -> None:
        self.status_widget.set_device("设备初始化中")
        self.add_log("开始扫描 USB 设备。")
        future = self.executor.submit(self.device_service.scan)
        future.add_done_callback(self._emit_scan_result)

    def _emit_scan_result(self, future) -> None:
        try:
            ok, message, device = future.result()
        except Exception as exc:
            ok, message, device = False, f"设备扫描失败：{exc}", None
        self.scanFinished.emit(ok, message, device)

    def _on_scan_finished(self, ok: bool, message: str, device: object) -> None:
        self.add_log(message)
        self.device = device if ok and isinstance(device, DeviceInfo) else None
        self.status_widget.set_device("已连接" if ok else "未检测到设备", self.device)

    def on_point_selected(self, longitude: float, latitude: float) -> None:
        self.longitude = longitude
        self.latitude = latitude
        self._update_coordinate_labels()
        if self.config.settings.remember_last_point:
            self.config.settings.last_longitude = longitude
            self.config.settings.last_latitude = latitude
            self.config.save()
        self.add_log(f"地图点击选点：{longitude:.6f}, {latitude:.6f}")

    def on_current_location(self, longitude: float, latitude: float) -> None:
        self.current_longitude = longitude
        self.current_latitude = latitude
        map_longitude, map_latitude = wgs84_to_gcj02(longitude, latitude)
        self.map_view.page().runJavaScript(
            self._map_call_js("setCurrentLocation", f"{map_longitude!r}, {map_latitude!r}, true")
        )
        self.add_log(f"获取当前位置成功：{longitude:.6f}, {latitude:.6f}")

    def on_current_location_failed(self, message: str) -> None:
        self.add_log(f"获取当前位置失败：{message}")
        self.map_view.page().runJavaScript(self._map_call_js("showDefaultCenter", ""))

    def request_current_location(self) -> None:
        self.add_log("正在请求 Mac 当前位置。")
        self.location_service_mac.request_location()

    def set_virtual_location(self) -> None:
        self.add_log("开始设置虚拟定位。")
        future = self.executor.submit(self.location_service.set_location, self.device, self.longitude, self.latitude)
        future.add_done_callback(lambda f: self._emit_action_result("set", f))

    def clear_virtual_location(self) -> None:
        self.add_log("开始清除虚拟定位。")
        future = self.executor.submit(self.location_service.clear_location, self.device)
        future.add_done_callback(lambda f: self._emit_action_result("clear", f))

    def _emit_action_result(self, action: str, future) -> None:
        try:
            ok, message = future.result()
        except Exception as exc:
            ok, message = False, f"操作失败：{exc}"
        self.actionFinished.emit(action, ok, message)

    def _on_action_finished(self, action: str, ok: bool, message: str) -> None:
        self.add_log(message)
        if action == "set":
            self.status_widget.set_device("定位设置成功" if ok else "定位设置失败", self.device)
            if not ok:
                QMessageBox.warning(self, "设置虚拟定位失败", message)
        else:
            self.status_widget.set_device("定位已清除" if ok else "清除定位失败", self.device)
            if not ok:
                QMessageBox.warning(self, "清除虚拟定位失败", message)

    def copy_coordinates(self) -> None:
        if self.longitude is None or self.latitude is None:
            self.add_log("当前没有可复制的坐标。")
            return
        text = f"{self.longitude:.6f},{self.latitude:.6f}"
        QGuiApplication.clipboard().setText(text)
        self.add_log(f"坐标已复制：{text}")

    def add_log(self, message: str) -> None:
        self.logMessage.emit(message)

    def _update_coordinate_labels(self) -> None:
        lng = "-" if self.longitude is None else f"{self.longitude:.6f}"
        lat = "-" if self.latitude is None else f"{self.latitude:.6f}"
        self.longitude_label.setText(f"经度：{lng}")
        self.latitude_label.setText(f"纬度：{lat}")

    def _grant_web_permission(self, security_origin: QUrl, feature: QWebEnginePage.Feature) -> None:
        if feature == QWebEnginePage.Feature.Geolocation:
            self.map_view.page().setFeaturePermission(
                security_origin,
                feature,
                QWebEnginePage.PermissionPolicy.PermissionGrantedByUser,
            )

    def _on_map_loaded(self, ok: bool) -> None:
        if ok:
            self.apply_map_theme()
            self.add_log("地图页面加载完成。")
            if self.current_longitude is not None and self.current_latitude is not None:
                self.on_current_location(self.current_longitude, self.current_latitude)
        else:
            self.add_log("地图加载失败，请检查高德地图 Key 或网络。")

    def _map_call_js(self, method: str, args: str) -> str:
        return f"""
        (function retryPinShiftMapCall(attempt) {{
          if (window.PinShiftMap && typeof window.PinShiftMap.{method} === 'function') {{
            window.PinShiftMap.{method}({args});
            return;
          }}
          if (attempt < 40) {{
            setTimeout(function () {{ retryPinShiftMapCall(attempt + 1); }}, 150);
          }}
        }})(0);
        """

    def close(self) -> bool:
        self.executor.shutdown(wait=False, cancel_futures=True)
        return super().close()
