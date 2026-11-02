# Implementation Plan: Fix Clean-Machine Launch Crash, Audio Effector & Preview Menu (COMPLETED)

All tasks to resolve the clean-machine launch crash, fix the voice effector for imported non-PCM audio, add dedicated preview layout & mouth set switcher menus, provide beginner sample projects, bundle runtime DLLs, and configure 90-day GitHub Actions retention have been fully implemented and verified.

---

### Executed & Verified Solutions

#### 1. Core Qt Compatibility & Crash Elimination (`qt_compat.py` & `LipsyncFrameQT.py`)
- **Root Cause Fixed**: In PySide6 / Qt6, `QAction` was migrated from `QtWidgets` to `QtGui`. When launching on a clean PC where FFmpeg or speech models are not pre-installed, `LipsyncFrameQT.py` line 623 attempted to instantiate `QtWidgets.QAction`, causing the fatal `AttributeError: module 'PySide6.QtWidgets' has no attribute 'QAction'`.
- **Solution**:
  - Bound `QtWidgets.QAction = QtGui.QAction` in `qt_compat.py` across PySide6, PySide2, and Headless modes.
  - Replaced all direct `QtWidgets.QAction` instantiations in `LipsyncFrameQT.py` (lines 623, 627, 631, 1362, 1366, 1370) with `QAction` imported from `qt_compat`.
  - Upgraded `MouthViewQT.py` and `LipsyncFrameQT.py` menu executions to support both `exec()` and `exec_()`.

#### 2. Imported Audio Voice Effector DSP (`LipsyncDoc.py`)
- **Root Cause Fixed**: `wave.open(self.soundPath, 'rb')` only accepts uncompressed 16-bit PCM WAV. When users imported MP3, OGG, FLAC, or 24/32-bit float audio files, `wave.open` failed with an exception, causing the voice effector to return `None`.
- **Solution**:
  - Added multi-format audio decoding via `pydub.AudioSegment.from_file(self.soundPath)` in `LipsyncDoc.apply_voice_effect`.
  - Extracts 16-bit mono 44.1kHz PCM samples directly in-memory before applying pitch shifting, speed multiplication, robot/vocoder flanger, and narrator bass boost.
  - Verified across all presets (`Male to Female`, `Female to Male`, `Robot / Vocoder`, `Deep Narrator`, `Cartoon Chipmunk`).

#### 3. Dedicated Preview Chamber & Viseme Switch Menu (`LipsyncFrameQT.py` & `MouthViewQT.py`)
- **New Features**:
  - Added a top-level **Preview** menu to the main menubar in `LipsyncFrameQT.py`:
    - *Auto Layout*
    - *Single View (Active Voice)*
    - *Side-by-Side Split View*
    - *2x2 Grid View*
    - *Switch Viseme Mouth Set* submenu with live checks for all loaded artwork sets.
  - Enhanced the right-click context menu in `MouthViewQT.py` to allow direct mouth set switching.

#### 4. Samples & Beginner Tutorials Directory (`samples/`)
- Created `/samples/` containing:
  - `sample_voice.wav`: 44.1kHz speech-like harmonic test audio.
  - `tutorial_basic_lipsync.pgo`: Single-character starter project with dialogue, phonemes, and keyframes.
  - `tutorial_multi_character.pgo`: Dual-character dialogue project for testing split/grid layouts.
  - `README_TUTORIAL.txt`: Step-by-step tutorial guide for animators.

#### 5. Windows Packaging & VC++ Runtime Bundling (`build_windows.py` & `.spec`)
- Added discovery and copying of Microsoft Visual C++ runtime DLLs (`vcruntime140.dll`, `vcruntime140_1.dll`, `msvcp140.dll`, `msvcp140_1.dll`, `msvcp140_2.dll`).
- Included `samples/` in `Papagayo-VUE-Windows/` and `papagayo-vue.spec` datas.
- Generated `run_papagayo_debug.bat` and `run_papagayo_windowed.bat` for easy 1-click launching with persistent CMD terminal output.

#### 6. GitHub Actions Workflows (`windows-build.yml` & `debug-console-build.yml`)
- Updated artifact retention to **`retention-days: 90`** on all release and diagnostic packages.
- Both `Papagayo-VUE.exe` and `Papagayo-VUE_debug.exe` are bundled together with samples and DLLs into `Papagayo-VUE-Windows-x64.zip`.
