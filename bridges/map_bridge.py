from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot


class MapBridge(QObject):
    pointSelected = Signal(float, float)
    logMessage = Signal(str)
    currentLocationReceived = Signal(float, float)
    currentLocationRequested = Signal()

    @Slot(float, float)
    def selectPoint(self, longitude: float, latitude: float) -> None:
        self.pointSelected.emit(longitude, latitude)

    @Slot(str)
    def log(self, message: str) -> None:
        self.logMessage.emit(message)

    @Slot(float, float)
    def currentLocation(self, longitude: float, latitude: float) -> None:
        self.currentLocationReceived.emit(longitude, latitude)

    @Slot()
    def requestCurrentLocation(self) -> None:
        self.currentLocationRequested.emit()
