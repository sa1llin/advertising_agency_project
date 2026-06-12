from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class ApiWorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    finished = Signal()


class ApiWorker(QRunnable):
    def __init__(self, operation: Callable[[], Any]):
        super().__init__()
        self.operation = operation
        self.signals = ApiWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.operation()
        except Exception as error:
            self.signals.error.emit(str(error))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
