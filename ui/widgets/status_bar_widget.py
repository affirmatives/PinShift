from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from models.device_info import DeviceInfo


class StatusBarWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._udid = ""
        self._udid_visible = False
        self.status_label = QLabel("设备状态：未检测到设备")
        self.status_label.setObjectName("deviceStatus")
        self.status_label.setMaximumWidth(280)
        self.udid_label = QLabel("UDID：-")
        self.udid_label.setObjectName("udidValue")
        self.udid_toggle = QPushButton("显示 UDID")
        self.udid_toggle.setProperty("compact", True)
        self.udid_toggle.setToolTip("显示/隐藏 UDID")
        self.udid_toggle.setEnabled(False)
        self.udid_toggle.clicked.connect(self._toggle_udid)
        self.udid_label.hide()
        self.udid_toggle.hide()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.status_label)
        layout.addWidget(self.udid_label)
        layout.addWidget(self.udid_toggle)
        layout.addStretch()

    def set_device(self, status: str, device: DeviceInfo | None = None) -> None:
        if device:
            self._udid = device.udid
            self.status_label.setText(f"● {status} · {device.name} · iOS {device.product_version}")
            self.status_label.setToolTip(device.summary)
            self.udid_label.show()
            self.udid_toggle.show()
            self.udid_toggle.setEnabled(True)
            self.udid_toggle.setText("显示 UDID" if not self._udid_visible else "隐藏 UDID")
            self._refresh_udid_label()
        else:
            self._udid = ""
            self._udid_visible = False
            self.status_label.setText(f"● {status}")
            self.status_label.setToolTip(status)
            self.udid_label.setText("UDID：-")
            self.udid_toggle.setText("显示 UDID")
            self.udid_toggle.setEnabled(False)
            self.udid_label.hide()
            self.udid_toggle.hide()

    def _toggle_udid(self) -> None:
        self._udid_visible = not self._udid_visible
        self.udid_toggle.setText("隐藏 UDID" if self._udid_visible else "显示 UDID")
        self._refresh_udid_label()

    def _refresh_udid_label(self) -> None:
        if not self._udid:
            self.udid_label.setText("UDID：-")
            return
        value = self._udid if self._udid_visible else self._masked_udid()
        self.udid_label.setText(f"UDID：{value}")
        self.udid_label.setMinimumWidth(self.udid_label.fontMetrics().horizontalAdvance(self.udid_label.text()) + 4)
        self.udid_label.setToolTip(self._udid)

    def _masked_udid(self) -> str:
        if len(self._udid) <= 10:
            return "*" * len(self._udid)
        prefix = self._udid[:8]
        suffix = self._udid[-6:]
        return f"{prefix}{'*' * (len(self._udid) - len(prefix) - len(suffix))}{suffix}"
