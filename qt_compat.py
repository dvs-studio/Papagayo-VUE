# -*- coding: utf-8 -*-
"""
Qt compatibility layer supporting PySide6 (Qt 6) with fallback to PySide2 (Qt 5).
Ensures Papagayo-NG runs seamlessly on modern Python 3.10+ environments as well
as legacy Python 3.7-3.9 installations.
"""

import sys

QT_LIB = None

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import (
        QFile, QObject, Qt, QSize, QRect, QUrl, QCoreApplication, QSettings,
        QThreadPool, QTranslator
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
    from PySide2 import QtCore, QtGui, QtWidgets
    from PySide2.QtCore import (
        QFile, QObject, Qt, QSize, QRect, QUrl, QCoreApplication, QSettings,
        QThreadPool, QTranslator
    )
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


def exec_app(app_instance):
    """Safely execute the QApplication event loop in both Qt5 and Qt6."""
    if hasattr(app_instance, "exec"):
        return app_instance.exec()
    return app_instance.exec_()
