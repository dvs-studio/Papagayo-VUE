# -*- coding: utf-8 -*-
"""
Qt compatibility layer supporting PySide6 (Qt 6) with fallback to PySide2 (Qt 5)
and a robust headless fallback for CLI, container, and test environments.
"""

import sys
import os
import configparser

QT_LIB = None
IS_HEADLESS = False

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import (
        QFile, QObject, Qt, QSize, QRect, QUrl, QCoreApplication, QSettings,
        QThreadPool, QTranslator, Signal
    )
    from PySide6.QtGui import (
        QPixmap, QIcon, QPainter, QFont, QPen, QColor, QDesktopServices,
        QTransform, QBrush
    )
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QDialog, QLabel, QPushButton,
        QScrollArea, QGridLayout, QVBoxLayout, QHBoxLayout, QComboBox,
        QProgressDialog, QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
        QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
        QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsTextItem, QGraphicsPixmapItem
    )
    from PySide6.QtUiTools import QUiLoader as uic

    try:
        from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    except ImportError:
        QMediaPlayer = None
        QAudioOutput = None

    QT_LIB = "PySide6"
    IS_PYSIDE6 = True
    IS_PYSIDE2 = False

except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
        from PySide2.QtCore import (
            QFile, QObject, Qt, QSize, QRect, QUrl, QCoreApplication, QSettings,
            QThreadPool, QTranslator
        )
        try:
            from PySide2.QtCore import Signal
        except ImportError:
            from PySide2.QtCore import Signal as Signal
        from PySide2.QtGui import (
            QPixmap, QIcon, QPainter, QFont, QPen, QColor, QDesktopServices,
            QTransform, QBrush
        )
        from PySide2.QtWidgets import (
            QApplication, QMainWindow, QWidget, QDialog, QLabel, QPushButton,
            QScrollArea, QGridLayout, QVBoxLayout, QHBoxLayout, QComboBox,
            QProgressDialog, QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
            QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
            QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsTextItem, QGraphicsPixmapItem
        )
        from PySide2.QtUiTools import QUiLoader as uic

        try:
            from PySide2.QtMultimedia import (
                QMediaPlayer, QAudioFormat, QAudioBuffer, QAudioDecoder, QAudioOutput
            )
        except ImportError:
            QMediaPlayer = None
            QAudioOutput = None

        QT_LIB = "PySide2"
        IS_PYSIDE6 = False
        IS_PYSIDE2 = True

    except ImportError:
        # Headless fallback when neither PySide6 nor PySide2 is installed
        QT_LIB = "Headless"
        IS_PYSIDE6 = False
        IS_PYSIDE2 = False
        IS_HEADLESS = True

        class _Signal:
            def __init__(self, *args, **kwargs):
                self._callbacks = []
            def connect(self, fn):
                self._callbacks.append(fn)
            def emit(self, *args, **kwargs):
                for fn in self._callbacks:
                    try:
                        fn(*args, **kwargs)
                    except Exception:
                        pass

        def Signal(*args, **kwargs):
            return _Signal(*args, **kwargs)

        class QObject:
            def __init__(self, *args, **kwargs):
                pass

        class _Qt:
            AlignLeft = 1
            AlignCenter = 2
            AlignRight = 3
            SolidPattern = 1
            ScrollBarAlwaysOff = 0
            ScrollBarAlwaysOn = 1

        Qt = _Qt()

        class QSize:
            def __init__(self, w=0, h=0):
                self._w = w; self._h = h
            def width(self): return self._w
            def height(self): return self._h

        class QRect:
            def __init__(self, x=0, y=0, w=0, h=0):
                self._x = x; self._y = y; self._w = w; self._h = h
            def x(self): return self._x
            def y(self): return self._y
            def width(self): return self._w
            def height(self): return self._h

        class QUrl:
            def __init__(self, url=""):
                self.url = url
            @staticmethod
            def fromLocalFile(path):
                return QUrl(path)

        class QSettings:
            IniFormat = 1
            def __init__(self, path="", fmt=1):
                self.path = path
                self._data = {}
                self._load()

            def _load(self):
                if self.path and os.path.exists(self.path):
                    cp = configparser.ConfigParser()
                    try:
                        cp.read(self.path)
                        for section in cp.sections():
                            for k, v in cp.items(section):
                                self._data[f"{section}/{k}"] = v
                                self._data[k] = v
                    except Exception:
                        pass

            def setFallbacksEnabled(self, b):
                pass

            def value(self, key, default=None):
                clean_key = key.lstrip("/")
                val = self._data.get(clean_key, self._data.get(key, default))
                if val is not None and default is not None:
                    if isinstance(default, bool):
                        return str(val).lower() in ("true", "1", "yes")
                    if isinstance(default, int):
                        try: return int(val)
                        except ValueError: return default
                    if isinstance(default, float):
                        try: return float(val)
                        except ValueError: return default
                return val if val is not None else default

            def setValue(self, key, val):
                clean_key = key.lstrip("/")
                self._data[clean_key] = val
                self._data[key] = val

        class QCoreApplication:
            @staticmethod
            def processEvents():
                pass
            @staticmethod
            def instance():
                return None
            def exec_(self):
                return 0
            def exec(self):
                return 0

        class QColor:
            def __init__(self, r=0, g=0, b=0, a=255):
                self.r = r; self.g = g; self.b = b; self.a = a

        class QFont:
            def __init__(self, name="Swiss", size=6):
                self.name = name; self.size = size

        class QIcon:
            def __init__(self, path=""):
                self.path = path

        class QPixmap:
            def __init__(self, path=""):
                self.path = path

        class QPen:
            def __init__(self, color=None):
                self.color = color

        class QBrush:
            def __init__(self, color=None, style=1):
                self.color = color; self.style = style

        class QPainter:
            pass

        class QTransform:
            def translate(self, *args): return self
            def scale(self, *args): return self
            def m22(self): return 1.0

        class QDesktopServices:
            @staticmethod
            def openUrl(url): return True

        class QThreadPool:
            @staticmethod
            def globalInstance(): return QThreadPool()
            def start(self, runnable):
                try: runnable.run()
                except Exception: pass
            def waitForDone(self): pass

        class QTranslator:
            def load(self, *args): return True

        class QFile:
            ReadOnly = 1
            def __init__(self, path=""): self.path = path
            def open(self, *args): return True
            def close(self): pass

        class _DummyWidget:
            def __init__(self, *args, **kwargs):
                self._visible = True
            def show(self): self._visible = True
            def hide(self): self._visible = False
            def setVisible(self, v): self._visible = v
            def setEnabled(self, e): pass
            def setMaximum(self, m): pass
            def setMinimum(self, m): pass
            def setValue(self, v): pass
            def reset(self): pass
            def clear(self): pass
            def addItems(self, items): pass
            def setText(self, t): pass
            def toPlainText(self): return ""
            def currentText(self): return ""
            def setWindowIcon(self, icon): pass
            def setWindowTitle(self, title): pass
            def tabBar(self): return self
            def count(self): return 0
            def removeTab(self, i): pass
            def addTab(self, t): pass
            def setTabText(self, i, t): pass

        class QApplication(QCoreApplication):
            @staticmethod
            def topLevelWidgets(): return []

        class QMainWindow(_DummyWidget): pass
        class QWidget(_DummyWidget): pass
        class QDialog(_DummyWidget): pass
        class QLabel(_DummyWidget): pass
        class QPushButton(_DummyWidget): pass
        class QScrollArea(_DummyWidget): pass
        class QGridLayout(_DummyWidget): pass
        class QVBoxLayout(_DummyWidget): pass
        class QHBoxLayout(_DummyWidget): pass
        class QComboBox(_DummyWidget): pass
        class QProgressDialog(_DummyWidget): pass
        class QMessageBox(_DummyWidget):
            Yes = 1; No = 2; Cancel = 3; Ok = 4; Warning = 1; Information = 2
            def exec_(self): return QMessageBox.Ok
            def exec(self): return QMessageBox.Ok
            def setStandardButtons(self, b): pass
            def setIcon(self, i): pass
        class QFileDialog:
            @staticmethod
            def getOpenFileName(*args, **kwargs): return ("", "")
            @staticmethod
            def getSaveFileName(*args, **kwargs): return ("", "")
        class QListWidget(_DummyWidget): pass
        class QListWidgetItem: pass
        class QGraphicsView(_DummyWidget):
            def scene(self): return QGraphicsScene()
            def setScene(self, s): pass
            def setVerticalScrollBarPolicy(self, p): pass
            def setHorizontalScrollBarPolicy(self, p): pass
        class QGraphicsScene:
            def clear(self): pass
            def update(self): pass
            def addRect(self, *args): return _DummyWidget()
            def addPolygon(self, *args): return _DummyWidget()
            def addText(self, *args): return _DummyWidget()
            def items(self): return []
            def sceneRect(self): return QRect(0, 0, 800, 600)
            def setSceneRect(self, r): pass
        class QGraphicsItem: pass
        class QGraphicsRectItem: pass
        class QGraphicsLineItem: pass
        class QGraphicsPolygonItem: pass
        class QGraphicsTextItem: pass
        class QGraphicsPixmapItem: pass

        class _Loader:
            def load(self, file_obj): return QMainWindow()

        uic = _Loader
        QMediaPlayer = None
        QAudioOutput = None

        def Slot(*args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

        class _QtCore:
            QFile = QFile
            QObject = QObject
            Qt = Qt
            QSize = QSize
            QRect = QRect
            QUrl = QUrl
            QCoreApplication = QCoreApplication
            QSettings = QSettings
            QThreadPool = QThreadPool
            QTranslator = QTranslator
            Signal = Signal
            Slot = staticmethod(Slot)
            QRunnable = object
            qRegisterResourceData = staticmethod(lambda *args: True)
            qUnregisterResourceData = staticmethod(lambda *args: True)

        QtCore = _QtCore()

        class _QtGui:
            QPixmap = QPixmap
            QIcon = QIcon
            QPainter = QPainter
            QFont = QFont
            QPen = QPen
            QColor = QColor
            QDesktopServices = QDesktopServices
            QTransform = QTransform
            QBrush = QBrush
            class QImageReader:
                @staticmethod
                def supportedImageFormats(): return [b"png", b"jpg", b"bmp"]

        QtGui = _QtGui()

        class _QtWidgets:
            QApplication = QApplication
            QMainWindow = QMainWindow
            QWidget = QWidget
            QDialog = QDialog
            QLabel = QLabel
            QPushButton = QPushButton
            QScrollArea = QScrollArea
            QGridLayout = QGridLayout
            QVBoxLayout = QVBoxLayout
            QHBoxLayout = QHBoxLayout
            QComboBox = QComboBox
            QProgressDialog = QProgressDialog
            QMessageBox = QMessageBox
            QFileDialog = QFileDialog
            QListWidget = QListWidget
            QListWidgetItem = QListWidgetItem
            QGraphicsView = QGraphicsView
            QGraphicsScene = QGraphicsScene
            QGraphicsItem = QGraphicsItem
            QGraphicsRectItem = QGraphicsRectItem
            QGraphicsLineItem = QGraphicsLineItem
            QGraphicsPolygonItem = QGraphicsPolygonItem
            QGraphicsTextItem = QGraphicsTextItem
            QGraphicsPixmapItem = QGraphicsPixmapItem

        QtWidgets = _QtWidgets()


def exec_app(app_instance):
    """Safely execute the QApplication event loop in both Qt5, Qt6, and headless mode."""
    if hasattr(app_instance, "exec"):
        return app_instance.exec()
    if hasattr(app_instance, "exec_"):
        return app_instance.exec_()
    return 0
