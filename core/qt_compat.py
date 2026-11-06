"""
Compatibility layer supporting both PySide6 and PyQt6 seamlessly.
Prioritizes PySide6 if installed; falls back to PyQt6.
"""

import sys

QT_API = None

try:
    import PySide6.QtCore as QtCore
    import PySide6.QtGui as QtGui
    import PySide6.QtWidgets as QtWidgets
    
    Signal = QtCore.Signal
    Slot = QtCore.Slot
    Property = QtCore.Property
    QT_API = "PySide6"
except ImportError:
    try:
        import PyQt6.QtCore as QtCore
        import PyQt6.QtGui as QtGui
        import PyQt6.QtWidgets as QtWidgets
        
        Signal = QtCore.pyqtSignal
        Slot = QtCore.pyqtSlot
        Property = QtCore.pyqtProperty
        QT_API = "PyQt6"
    except ImportError as e:
        raise ImportError(
            "Neither PySide6 nor PyQt6 is installed. Please install one of them: "
            "pip install PySide6 (or PyQt6)"
        ) from e

Qt = QtCore.Qt
QObject = QtCore.QObject
QTimer = QtCore.QTimer
QThreadPool = QtCore.QThreadPool
QRunnable = QtCore.QRunnable
QSize = QtCore.QSize
QPoint = QtCore.QPoint
QRect = QtCore.QRect

__all__ = [
    "QtCore",
    "QtGui",
    "QtWidgets",
    "Signal",
    "Slot",
    "Property",
    "Qt",
    "QObject",
    "QTimer",
    "QThreadPool",
    "QRunnable",
    "QSize",
    "QPoint",
    "QRect",
    "QT_API",
]
