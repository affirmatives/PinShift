from __future__ import annotations

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from ui.main_page import MainPage
from ui.settings_page import SettingsPage
from ui.theme import apply_palette, stylesheet
from utils.paths import resource_path


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.setWindowTitle("PinShift")

        self.main_page = MainPage(config)
        self.settings_page = SettingsPage(config)
        self.settings_page.settingsSaved.connect(self._on_settings_saved)
        self.settings_page.logMessage.connect(self.main_page.add_log)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.settings_page)

        self.main_button = QPushButton("主页面")
        self.settings_button = QPushButton("配置")
        self.main_button.clicked.connect(lambda: self._switch_page(self.main_page))
        self.settings_button.clicked.connect(lambda: self._switch_page(self.settings_page))

        self.day_button = QPushButton("日间")
        self.night_button = QPushButton("夜间")
        self.day_button.clicked.connect(lambda: self._set_appearance("light"))
        self.night_button.clicked.connect(lambda: self._set_appearance("dark"))
        for button in (self.day_button, self.night_button):
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.day_button.setToolTip("切换浅色界面和日间地图")
        self.night_button.setToolTip("切换深色界面和夜间地图")

        def segments(*buttons: QPushButton) -> QWidget:
            group = QWidget()
            group.setObjectName("segmentGroup")
            row = QHBoxLayout(group)
            row.setContentsMargins(3, 3, 3, 3)
            row.setSpacing(2)
            for button in buttons:
                row.addWidget(button)
            return group

        footer = QHBoxLayout()
        footer.setSpacing(14)
        footer.addWidget(self.main_page.status_widget, 1)
        footer.addStretch()
        footer.addWidget(segments(self.day_button, self.night_button))
        footer.addWidget(segments(self.main_button, self.settings_button))

        root = QWidget()
        root.setObjectName("windowRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)
        layout.addWidget(self.stack, 1)
        layout.addLayout(footer)
        self.setCentralWidget(root)
        self._apply_style()
        self._sync_nav_buttons()

    def _on_settings_saved(self) -> None:
        self.main_page.load_map()

    def _switch_page(self, page: QWidget) -> None:
        self.stack.setCurrentWidget(page)
        self._sync_nav_buttons()

    def _sync_nav_buttons(self) -> None:
        is_main = self.stack.currentWidget() is self.main_page
        self.main_button.setProperty("active", is_main)
        self.settings_button.setProperty("active", not is_main)
        for button in (self.main_button, self.settings_button):
            button.style().unpolish(button)
            button.style().polish(button)

    def _set_appearance(self, appearance: str) -> None:
        self.config.settings.appearance = appearance
        self.config.save()
        self._apply_style()
        self.main_page.apply_map_theme()

    def _apply_style(self) -> None:
        dark = self.config.settings.appearance == "dark"
        apply_palette(dark)
        style = stylesheet(dark).replace("web/check.svg", str(resource_path("web", "check.svg")))
        self.setStyleSheet(style)
        self.day_button.setProperty("active", not dark)
        self.night_button.setProperty("active", dark)
        for button in (self.day_button, self.night_button):
            button.style().unpolish(button)
            button.style().polish(button)
