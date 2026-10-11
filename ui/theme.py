from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def apply_palette(dark: bool) -> None:
    palette = QPalette()
    colors = {
        QPalette.ColorRole.Window: '#202124' if dark else '#f2f3f5',
        QPalette.ColorRole.WindowText: '#f5f5f7' if dark else '#202124',
        QPalette.ColorRole.Base: '#28292d' if dark else '#ffffff',
        QPalette.ColorRole.AlternateBase: '#333438' if dark else '#f5f5f7',
        QPalette.ColorRole.Text: '#f5f5f7' if dark else '#202124',
        QPalette.ColorRole.Button: '#38393d' if dark else '#ffffff',
        QPalette.ColorRole.ButtonText: '#f5f5f7' if dark else '#202124',
        QPalette.ColorRole.Highlight: '#0a84ff' if dark else '#007aff',
        QPalette.ColorRole.HighlightedText: '#ffffff',
        QPalette.ColorRole.PlaceholderText: '#96979e' if dark else '#85858b',
    }
    for role, color in colors.items():
        palette.setColor(role, QColor(color))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText, QPalette.ColorRole.WindowText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor('#707178' if dark else '#aaaab0'))
    QApplication.instance().setPalette(palette)


def stylesheet(dark: bool) -> str:
    c = dict(
        bg='#202124' if dark else '#f2f3f5',
        surface='#2b2c30' if dark else '#ffffff',
        inset='#232428' if dark else '#f5f5f7',
        text='#f5f5f7' if dark else '#202124',
        muted='#a2a3aa' if dark else '#77777e',
        border='#424348' if dark else '#e2e3e7',
        button='#3b3c41' if dark else '#ffffff',
        hover='#47484e' if dark else '#f0f1f4',
        pressed='#303136' if dark else '#e6e7ec',
        blue='#0a84ff' if dark else '#007aff',
        bluehover='#3098ff' if dark else '#1685ff',
        segment='#38393e' if dark else '#e6e7eb',
        active='#56575d' if dark else '#ffffff',
        disabled='#707178' if dark else '#aaaab0',
    )
    return """
        QWidget { font-family: "Helvetica Neue"; font-size: 13px; color: %(text)s; }
        QMainWindow, #windowRoot { background: %(bg)s; }
        QLabel { background: transparent; border: none; }
        #sidebar { background: %(surface)s; border: 1px solid %(border)s; border-radius: 18px; }
        #sectionTitle { color: %(muted)s; font-size: 12px; font-weight: 600; }
        #pageTitle { font-size: 25px; font-weight: 600; padding-bottom: 18px; }
        QPushButton { min-height: 26px; padding: 5px 14px; border: 1px solid %(border)s;
            border-radius: 10px; background: %(button)s; font-weight: 500; }
        QPushButton:hover { background: %(hover)s; }
        QPushButton:pressed { background: %(pressed)s; }
        QPushButton:focus { border-color: %(blue)s; }
        QPushButton:disabled { color: %(disabled)s; background: %(inset)s; }
        QPushButton[compact="true"] { min-height: 22px; padding: 3px 10px; font-size: 11px; border-radius: 8px; }
        #primaryButton { background: %(blue)s; color: white; border-color: %(blue)s; font-weight: 600; }
        #primaryButton:hover { background: %(bluehover)s; }
        #primaryButton:pressed { background: #0063cd; }
        #segmentGroup { background: %(segment)s; border-radius: 10px; }
        #segmentGroup QPushButton { background: transparent; border: none; border-radius: 8px;
            min-height: 22px; padding: 3px 11px; font-size: 12px; color: %(muted)s; }
        #segmentGroup QPushButton:hover { color: %(text)s; }
        #segmentGroup QPushButton[active="true"] { background: %(active)s; color: %(text)s; }
        QLineEdit, QSpinBox { min-height: 28px; padding: 4px 11px; border: 1px solid %(border)s;
            border-radius: 9px; background: %(inset)s; selection-background-color: %(blue)s; }
        QLineEdit:focus, QSpinBox:focus { border: 1px solid %(blue)s; }
        QCheckBox { spacing: 8px; min-height: 28px; background: transparent; }
        QCheckBox::indicator { width: 16px; height: 16px; border-radius: 5px;
            border: 1px solid %(border)s; background: %(inset)s; }
        QCheckBox::indicator:checked { background: %(blue)s; border-color: %(blue)s; image: url("web/check.svg"); }
        QTextEdit { background: %(inset)s; border: 1px solid %(border)s; border-radius: 11px;
            padding: 10px; color: %(muted)s; font-family: "Menlo"; font-size: 11px;
            selection-background-color: %(blue)s; }
        #coordBox { background: %(inset)s; border: 1px solid %(border)s; border-radius: 12px; }
        #coordBox QLabel { font-family: "Menlo"; font-size: 13px; font-weight: 500; }
        #deviceStatus { color: %(muted)s; font-size: 11px; }
        #udidValue { color: %(muted)s; font-family: "Menlo"; font-size: 10px; }
        QSplitter::handle { background: transparent; }
        QScrollBar:vertical { width: 8px; margin: 3px; background: transparent; }
        QScrollBar::handle:vertical { background: %(border)s; border-radius: 3px; min-height: 24px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
        QToolTip, QMenu { background: %(surface)s; color: %(text)s; border: 1px solid %(border)s; }
    """ % c
