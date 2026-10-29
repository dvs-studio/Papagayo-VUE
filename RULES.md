# Project Rules & Continuation Protocol

## Core Principles
1. **Zero Destructive Changes**: Do not perform massive, unverified rewrites of working core animation logic. Retain compatibility with existing Papagayo projects (`.pgo`, `.pg2`) and Moho export switch files (`.dat`).
2. **Dual Qt Compatibility**: Always route Qt imports through `qt_compat.py`. Support `PySide6` (Qt 6) as the primary modern standard for Python 3.10+ while retaining `PySide2` (Qt 5) fallback for older systems.
3. **Landscape Layout Baseline**: Preserve the desktop landscape studio layout as the baseline for timeline and waveform scrubbing precision. Do not force an unverified mobile portrait refactor that breaks audio scrubbing.
4. **Reproducible Builds**: All Windows standalone builds must be reproducible via `python build_windows.py` and automated via `.github/workflows/build-windows.yml`.
5. **No Deprecated Modules**: Never use dead modules like `imp` or `distutils.core`. Use `sys.frozen` and standard `setuptools`.
