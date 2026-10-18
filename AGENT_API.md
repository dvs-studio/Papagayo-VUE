# Agent API Reference

## Key Modules

### `qt_compat.py`
Cross-version Qt layer.
- **Exports**: `QtCore`, `QtGui`, `QtWidgets`, `QFile`, `QObject`, `Qt`, `QSize`, `QRect`, `QUrl`, `QCoreApplication`, `QSettings`, `QThreadPool`, `QPixmap`, `QIcon`, `QPainter`, `QFont`, `QPen`, `QColor`, `QDesktopServices`, `QTransform`, `QBrush`, `QApplication`, `QMainWindow`, `QWidget`, `QDialog`, `QLabel`, `QPushButton`, `QScrollArea`, `QGridLayout`, `QVBoxLayout`, `QHBoxLayout`, `QComboBox`, `QProgressDialog`, `QMessageBox`, `QFileDialog`, `QListWidget`, `QListWidgetItem`, `QGraphicsView`, `QGraphicsScene`, `uic`, `QMediaPlayer`, `QAudioOutput`.
- **Functions**:
  - `exec_app(app)`: Calls `app.exec()` (Qt6) or `app.exec_()` (Qt5).

### `build_windows.py`
Automated PyInstaller build pipeline.
- Compiles resources if `pyrcc5` or `pyside6-rcc` is available.
- Generates `file_version_info.txt` via `pyinstaller_versionfile`.
- Invokes `papagayo-ng.spec`.
- Copies assets (`rsrc`, `phonemes`, `breakdowns`, `gpl.txt`, `readme.md`) to `dist/Papagayo-NG-Windows/`.
- Compresses bundle into `dist/Papagayo-NG-Windows-x64.zip`.

### `LipsyncDoc.py`
Document object model.
- `LipsyncDoc`: Root project model containing audio path, FPS, and voice collection.
- `LipsyncVoice`: Voice track with phrases, words, and phoneme keyframes.
  - `voice.export(path)`: Moho `.dat` export.
  - `voice.export_json(path)`: JSON animation export.
  - `voice.export_alelo(path, lang, langman)`: Alelo dialogue export.
  - `voice.export_images(dir, prefix)`: Frame-by-frame mouth image sequence.

### `WaveformViewRewrite.py`
Waveform visualization & timeline editing widget (`WaveformView`).
- Renders audio waveform amplitudes, frame ruler, phrase bars, and phoneme markers.
- Handles mouse scrubbing, marker dragging, zooming, and playback sync.

### `MouthViewQT.py`
Live viseme preview widget (`MouthView`).
- Shows current mouth graphic matching the active frame's phoneme.
