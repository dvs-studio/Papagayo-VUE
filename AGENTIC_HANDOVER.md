# Papagayo-NG: Comprehensive Agentic Handover Document

## 1. Executive Summary & Purpose

**Papagayo-NG** (Next Generation) is a specialized cross-platform lip-sync animation tool originally created by Lost Marble and modernized by the open-source community. It aligns spoken dialogue audio with phonemes and viseme mouth shapes (Preston Blair, Rhubarb, Fleming & Dobbs, Gary C Martin, Hunanbean CMU39). The resulting synchronized lip-sync keyframe sequences are exported directly to professional 2D and 3D animation suites, including:
- **Moho / Anime Studio** (`.dat` switch layer format)
- **Blender** (via JSON / Alembic / Python importer)
- **Synfig Studio** (`.sifz` / `.lst`)
- **OpenToonz** (`.txt` / level lip sync)
- **Game Engines & Realtime Frameworks** (structured JSON & Alelo formats)

This document serves as the master agentic handover for any AI coding agent or software engineer stepping into the repository. It details repository architecture, resolved defects, design contracts, and the active repair roadmap.

---

## 2. System Architecture & Component Mapping

```
                               ┌────────────────────────┐
                               │   Entry Points         │
                               │   - papagayo-ng.py     │
                               │   - app.py / main.py   │
                               └───────────┬────────────┘
                                           │
         ┌─────────────────────────────────┼────────────────────────────────┐
         ▼                                 ▼                                ▼
┌──────────────────┐             ┌───────────────────┐            ┌──────────────────┐
│ Web Dev Studio   │             │ Core Engine / DOM │            │ Desktop GUI      │
│ (Port 3000)      │             │                   │            │ (PySide6 / Qt)   │
│ - http.server    │             │ - LipsyncDoc.py   │            │ - LipsyncFrameQT │
│ - Pure JS Studio │◄───────────►│ - SoundPlayer.py  │◄──────────►│ - WaveformView   │
│ - Live Diag APIs │             │ - Breakdowns/Dict │            │ - MouthViewQT    │
└──────────────────┘             └─────────┬─────────┘            └──────────────────┘
                                           │
                                 ┌─────────▼─────────┐
                                 │ Qt Abstraction    │
                                 │ - qt_compat.py    │
                                 │ (PySide6 / Headless)
                                 └───────────────────┘
```

### 2.1 File & Module Responsibilities

| File / Directory | Role & Responsibilities |
| :--- | :--- |
| `papagayo-ng.py` | Primary CLI (`--cli`) and desktop GUI launcher. Parses arguments, handles batch exports, and creates `LipsyncFrame`. |
| `LipsyncDoc.py` | Root document model (`LipsyncDoc`, `LipSyncObject`, `LipsyncVoice`, `Phoneme`). Handles reading and writing `.pgo` and `.pg2` projects, phrase breakdown, and export drivers (Moho `.dat`, JSON, Alelo, PNG frame sequence). |
| `SoundPlayer.py` | Audio playback, waveform analysis, and amplitude extraction engine. Contains standard library `wave` fallback and pure-Python RMS calculations. |
| `SoundPlayerNew.py` / `SoundPlayerQT.py` / `SoundPlayerOSX.py` | Platform-specific sound drivers for desktop audio output. |
| `LipsyncFrameQT.py` | Main desktop application window and menu/action dispatcher. Coordinates timeline scrubbing, voice tree, and playback controls. |
| `WaveformViewRewrite.py` | Custom Qt widget rendering interactive audio waveforms, frame rulers, word bars, and draggable phoneme markers. |
| `MouthViewQT.py` | Viseme preview widget displaying corresponding mouth artwork (`rsrc/mouths/`) synchronized with the current timeline frame. |
| `qt_compat.py` | Unified Qt compatibility layer. Bridges `PySide6` (primary), `PySide2` (legacy), and provides headless mock fallbacks for headless/CI systems without an X11 server. |
| `phoneme_conversion_helper.py` | Phoneme set converter (CMU to Preston Blair, Rhubarb, etc.). |
| `breakdowns/` | Language and phonetic rules mapping text words to phonemes. |
| `phonemes/` | Phoneme definitions and viseme mapping tables. |
| `rsrc/languages/` | Text dictionaries (e.g. CMU Pronouncing Dictionary) used for automatic phoneme conversion. |
| `app.py` / `main.py` | Zero-dependency HTTP development server serving the interactive Web Studio on `0.0.0.0:3000`. |
| `build_windows.py` & `papagayo-ng.spec` | Automated PyInstaller packaging toolchain for standalone Windows executables. |
| `.github/workflows/` | Continuous integration and backup workflows. |

---

## 3. History of Fixes & Key Architectural Decisions

### 3.1 Dev Server Startup Resolution
- **Issue**: Dev server failed to launch initially.
- **Root Cause**: The runtime platform expects a `package.json` with a `"dev"` script running on port 3000. Additionally, earlier iterations of `app.py` attempted to import `flask`, which was not installed in the container environment.
- **Resolution**:
  1. Configured `/package.json` with `"dev": "python3 main.py"`, `"start": "python3 main.py"`, and `"build"`.
  2. Implemented `app.py` using Python's standard library `http.server.ThreadingHTTPServer` on `0.0.0.0:3000` with zero external dependencies.
  3. Built an interactive, full-fidelity Web Studio featuring live waveform inspection, mouth viseme preview, diagnostic APIs, and CLI test runners.

### 3.2 Resilient .PGO & Audio Path Loading
- **Issue**: Opening `.pgo` files silently failed or raised unhandled exceptions when project audio was moved, or when file extensions used upper-case letters.
- **Root Cause**:
  1. `LipsyncFrameQT.open_file_no_gui` checked `if doc.sound is None:` and immediately returned `None`, discarding all voices and phonemes if the recorded audio path did not exist on the current machine.
  2. Extension checks were case-sensitive (`.pgo` vs `.PGO`).
  3. Absolute paths embedded from different OS environments (e.g. `C:\Users\animator\audio.wav` opened on Linux) failed string resolution.
- **Resolution**:
  1. Updated `LipsyncDoc.py` to check for audio files with the same filename in the same directory as the `.pgo` project file.
  2. Preserved the voice, word, and phoneme document structure even if audio is missing, alerting the user gracefully rather than discarding work.
  3. Normalized all file extension checks to lower case.

### 3.3 Audio Engine Fallbacks
- **Issue**: Environments without `pydub`, `ffmpeg`, `pyaudio`, or `audioop` (removed in Python 3.13) crashed during waveform calculation or audio loading.
- **Root Cause**: Hard reliance on external audio libraries and missing standard library fallbacks.
- **Resolution**:
  1. Added standard library `wave` module fallback in `SoundPlayer.py`.
  2. Implemented a pure-Python RMS amplitude calculator in `SoundPlayer.py` for environments lacking compiled C extensions.
  3. Added boundary clamps preventing slice out-of-range errors when audio sample rates or frame counts are irregular.

### 3.4 Qt 6 / PySide6 Modernization
- **Issue**: Modern desktop environments using PySide6 encountered deprecated Qt5 methods.
- **Resolution**:
  1. Routed all Qt imports through `qt_compat.py`.
  2. Replaced `QWheelEvent.delta()` with `QWheelEvent.angleDelta().y()`.
  3. Wrapped progress bar signals with strict integer casts to avoid `TypeError: argument 1 has unexpected type 'float'`.

---

## 4. Crucial Guidelines & Preservation Protocol

When extending or repairing this codebase, subsequent agents **must** adhere to these rules:

1. **Zero Destructive Changes to Animation Math**: Never alter the timeline timing, frame interpolation, or Moho `.dat` export formatting. Animators rely on frame-accurate synchronization with external animation software.
2. **Dual Qt & Headless Discipline**:
   - Never import directly from `PySide6` or `PyQt5` in functional modules. Always import from `qt_compat`.
   - Maintain the headless fallback in `qt_compat.py` so unit tests and CLI batch exports (`papagayo-ng.py --cli`) run cleanly without an X11 display.
3. **Landscape Timeline Baseline**:
   - The desktop GUI timeline and waveform editor are designed for landscape orientation (horizontal scrubbing precision). Preserve this layout hierarchy.
4. **Dev Server Independence**:
   - Never introduce required pip packages (like Flask, Django, FastAPI) to `app.py` or `main.py`. The web preview on port 3000 must run exclusively on standard library modules.
5. **Pre-Commit Syntax & Build Verification**:
   - After any edits to Python files, run `python3 -m py_compile <file>` or `compile_applet` to verify clean compilation.

---

## 5. Active Roadmap & Pending Tasks

1. **Windows Packaging Validation**:
   - Ensure `build_windows.py` and `papagayo-ng.spec` properly collect all phonetic dictionaries (`rsrc/languages/`) and breakdown files into the PyInstaller one-dir output.
2. **Touch & Stylus Tolerance**:
   - Add configurable hit-box tolerance on waveform markers in `WaveformViewRewrite.py` for animators using stylus/tablet devices (Wacom, Surface, iPad via Sidecar).
3. **Automated Headless Test Suite**:
   - Add automated test scripts running CLI exports (`--cli -i test/example.pgo -o /tmp/test.dat --output-type moho`) and asserting valid output.
4. **Phoneme Alignment Refinement**:
   - Maintain compatibility with Rhubarb Lip Sync binary integration for automated phoneme recognition where available.
