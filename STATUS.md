# Project Status & Clone Review Report

## Current Phase: Core Fixes, Dev Server & Verification Complete

### 1. Dev Server & Starting Point Configuration
- **Entrypoints (`app.py` & `main.py`)**: Dev server configured to serve on `0.0.0.0:3000` with an interactive Web Studio and verification suite.
- **Starting Point Bridge**: Bridges directly to `papagayo-ng.py` for both CLI (`--cli`) and desktop (`--desktop`) modes.

### 2. Resolved Underlying Bugs in Audio & .PGO File Opening
- [x] **Universal Audio Engine (`SoundPlayer.py`)**:
  - Built-in WAV fallback using Python's standard library `wave` module (zero external dependencies required).
  - Resolved `AttributeError: 'NoneType' object has no attribute 'set_sample_width'` crash when `AudioSegment` or ffmpeg was missing.
  - Added pure-Python RMS amplitude calculator fallback for environments without `audioop`.
  - Added safe clamping for `startframe` and `getsampwidth` in `GetRMSAmplitude`.
- [x] **Resilient .PGO & Audio Path Resolver (`LipsyncDoc.py`)**:
  - Added UTF-8 encoding with fallback (`errors='replace'`) preventing `UnicodeDecodeError` on Windows cp1252 systems.
  - Added automatic sibling audio file lookup: if an absolute path from another machine (e.g. `C:\Users\...\audio.wav`) is missing, it automatically checks for `audio.wav` in the same directory as the `.pgo` file, handling Windows backslashes on Linux/macOS.
  - Added safe bounds-checking to `LipSyncObject.open` for malformed or truncated lines.
- [x] **Infinite Dialog Loop Fix (`LipsyncFrameQT.py`)**:
  - Fixed infinite modal loop in `while self.doc.sound is None:` by adding standard buttons and breaking cleanly on Cancel.
  - Fixed `.trans` lookup syntax error (`path[0].rsplit` -> `os.path.splitext(path)[0]`).
- [x] **Signal Argument Type Errors (`WaveformViewRewrite.py`)**:
  - Fixed `TypeError: argument 1 has unexpected type 'float'` when emitting progress to `Signal(int)` in `recalc_waveform` and `create_waveform`.
  - Fixed `ZeroDivisionError` in `normalize(x)` when audio is silent or uniform.
  - Modernized `event.delta()` to `event.angleDelta().y()` for Qt 6 / PySide6.
- [x] **Mouth Image Format Decoding Bug (`MouthViewQT.py`)**:
  - Decoded Qt `QByteArray` supported image formats to string so `ext in supported_imagetypes` correctly matches `.png`, `.jpg`, and `.bmp`.
- [x] **Headless Fallback (`qt_compat.py`)**:
  - Added full headless Qt fallback so CLI batch exports (`papagayo-ng.py --cli`) and unit tests run anywhere without an X11/GUI display.

### 3. Immediate Next Steps (To-Do List)
1. **GitHub Actions CI/CD**: Restore `.github/workflows/build-windows.yml` if automated cloud builds are desired.
2. **Android Mod Preparation**: Implement responsive resize listener on main window to adapt smoothly to landscape tablet displays.
3. **Timeline Editor Enhancements**: Add touch tolerance and zoom controls for mobile stylus / touch screens.
