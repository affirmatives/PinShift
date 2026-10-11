from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from config.app_info import (
    APP_AUTHOR,
    APP_COPYRIGHT,
    APP_LICENSE,
    APP_NAME,
    APP_VERSION,
    AUTHOR_URL,
    REPOSITORY_URL,
)


class SettingsPage(QWidget):
    settingsSaved = Signal()
    logMessage = Signal(str)

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("请输入高德地图 JavaScript API Key")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setMinimumWidth(560)

        self.security_input = QLineEdit()
        self.security_input.setPlaceholderText("请输入高德地图安全密钥 securityJsCode")
        self.security_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.security_input.setMinimumWidth(560)

        self.show_key = QCheckBox("显示 Key")
        self.show_key.toggled.connect(self._toggle_key_visible)

        self.zoom_input = QLineEdit()
        self.zoom_input.setValidator(QIntValidator(3, 20, self))
        self.zoom_input.setPlaceholderText("17")
        self.zoom_input.setMaximumWidth(120)
        zoom_row = QHBoxLayout()
        zoom_row.addWidget(self.zoom_input)
        zoom_row.addWidget(QLabel("范围 3-20，默认 17"))
        zoom_row.addStretch()

        self.auto_locate = QCheckBox("启动时自动尝试定位到当前实际位置")
        self.remember_last_point = QCheckBox("记住上次选点")
        self.auto_scan_usb = QCheckBox("启动时自动扫描 USB 设备")

        self.save_button = QPushButton("保存")
        self.save_button.setObjectName("primaryButton")
        self.clear_button = QPushButton("清空 Key")
        self.save_button.clicked.connect(self.save_settings)
        self.clear_button.clicked.connect(self.clear_key)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)
        form.addRow("高德地图 API Key", self.key_input)
        form.addRow("高德地图安全密钥", self.security_input)
        form.addRow("", self.show_key)
        form.addRow("默认地图缩放级别", zoom_row)
        form.addRow("", self.auto_locate)
        form.addRow("", self.remember_last_point)
        actions = QHBoxLayout()
        actions.addWidget(self.clear_button)
        actions.addWidget(self.save_button)
        actions.addStretch()
        scan_and_actions = QVBoxLayout()
        scan_and_actions.setSpacing(10)
        scan_and_actions.addWidget(self.auto_scan_usb)
        scan_and_actions.addLayout(actions)
        form.addRow("", scan_and_actions)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("配置")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addSpacing(24)
        about_title = QLabel("关于 PinShift")
        about_title.setObjectName("sectionTitle")
        layout.addWidget(about_title)

        about_form = QFormLayout()
        about_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        about_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        about_form.setHorizontalSpacing(18)
        about_form.setVerticalSpacing(8)
        self.version_label = QLabel(f"{APP_NAME} {APP_VERSION}")
        self.author_label = self._link_label(APP_AUTHOR, AUTHOR_URL)
        self.copyright_label = QLabel(APP_COPYRIGHT)
        self.license_label = self._link_label(
            APP_LICENSE, f"{REPOSITORY_URL}/blob/main/LICENSE"
        )
        self.github_label = self._link_label(REPOSITORY_URL, REPOSITORY_URL)
        about_form.addRow("版本", self.version_label)
        about_form.addRow("作者", self.author_label)
        about_form.addRow("版权", self.copyright_label)
        about_form.addRow("开源协议", self.license_label)
        about_form.addRow("GitHub", self.github_label)
        layout.addLayout(about_form)
        layout.addStretch()

        self.load_settings()

    @staticmethod
    def _link_label(text: str, url: str) -> QLabel:
        label = QLabel(f'<a href="{url}">{text}</a>')
        label.setOpenExternalLinks(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        return label

    def load_settings(self) -> None:
        settings = self.config.settings
        self.key_input.setText(settings.amap_api_key)
        self.security_input.setText(settings.amap_security_js_code)
        self.zoom_input.setText(str(settings.default_zoom))
        self.auto_locate.setChecked(settings.auto_locate_on_start)
        self.remember_last_point.setChecked(settings.remember_last_point)
        self.auto_scan_usb.setChecked(settings.auto_scan_usb_on_start)

    def save_settings(self) -> None:
        settings = self.config.settings
        settings.amap_api_key = self.key_input.text().strip()
        settings.amap_security_js_code = self.security_input.text().strip()
        settings.default_zoom = self._zoom_value()
        settings.auto_locate_on_start = self.auto_locate.isChecked()
        settings.remember_last_point = self.remember_last_point.isChecked()
        settings.auto_scan_usb_on_start = self.auto_scan_usb.isChecked()
        self.config.save()
        self.logMessage.emit(f"配置已保存：{self.config.path}")
        self.settingsSaved.emit()

    def _zoom_value(self) -> int:
        text = self.zoom_input.text().strip()
        if not text:
            self.zoom_input.setText("17")
            return 17
        value = max(3, min(20, int(text)))
        self.zoom_input.setText(str(value))
        return value

    def clear_key(self) -> None:
        reply = QMessageBox.question(
            self,
            "确认清空 Key",
            "确定要清空高德地图 API Key 和安全密钥吗？清空后地图需要重新配置才能正常加载。",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Ok:
            return
        self.key_input.clear()
        self.security_input.clear()
        self.save_settings()

    def _toggle_key_visible(self, checked: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.key_input.setEchoMode(mode)
        self.security_input.setEchoMode(mode)
