# Project Status & Clone Review Report

## Current Phase: Modernization & Packaging Complete

### 1. Clones & Imported Repositories Review
- **Root Directory (`/`)**: Main active Papagayo-NG codebase modernized to PySide6/Qt6 with full compatibility layer.
- **Upstream Mirror (`/papagayo-ng-upstream/`)**: Pristine copy of the original upstream Morevna repository retained for historical diffing and asset reference.
- **Resource Folders (`/rsrc/`, `/assets/`, `/phonemes/`, `/breakdowns/`)**:
  - `phonemes/`: Preston Blair, Fleming & Dobbs, Rhubarb, CMU 39 phoneme dictionaries.
  - `rsrc/mouths/`: 10 viseme illustration sets across multiple artistic styles.
  - `rsrc/languages/`: Dictionaries and ini configurations for English, Spanish, German, French, Korean, Italian, Dutch, and more.
  - `breakdowns/`: Language phonetic decomposition algorithms.

### 2. Codebase Health Check & Completed Modernization Milestones
- [x] **Qt Framework Modernization**: Created `qt_compat.py` supporting PySide6 (Qt 6) with PySide2 (Qt 5) fallback.
- [x] **Module Deprecation Fixes**: Removed deprecated `imp` in `utilities.py`; replaced with standard `sys.frozen` check for Python 3.12+ compatibility.
- [x] **Event Loop Harmonization**: Added `exec_app` wrapper for `app.exec()` vs `app.exec_()` differences.
- [x] **Modern Requirements**: Created `requirements.txt` for Python 3.10+ (PySide6) and `requirements-legacy.txt` for Python 3.7–3.9.
- [x] **Modern Build Pipeline**: Replaced obsolete `py2exe` setup with modern `setuptools` (`setup.py`) and an automated PyInstaller builder (`build_windows.py` and `papagayo-ng.spec`).
- [x] **GitHub Actions CI/CD**: Created `.github/workflows/build-windows.yml` to automatically build Windows standalone `.exe`, zip the distribution, and upload release artifacts.
- [x] **Comprehensive Documentation**: Updated `readme.md` with Windows standalone compilation steps, GitHub Actions CI instructions, and Android deployment / orientation roadmap.

### 3. Immediate Next Steps (To-Do List)
1. **GitHub Actions Validation**: Run initial workflow dispatch on Windows runner to verify PyInstaller artifact creation.
2. **Android Mod Preparation**: Implement responsive resize listener on main window to adapt smoothly to landscape tablet displays.
3. **Timeline Editor Enhancements**: Add touch tolerance and zoom controls for mobile stylus / touch screens.
