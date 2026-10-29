# Revised Implementation Plan: Papagayo-VUE Renaming, Victory Ukpong Attribution, Themes & Dual-Executable Windows Build

## 1. Executive Summary & Goals
This revised plan incorporates:
1. **Renaming Python Entrypoint**:
   - Rename `papagayo-ng.py` $\rightarrow$ `papagayo-vue.py` as the primary CLI and desktop application launcher.
   - Maintain a lightweight backward-compatible shim in `papagayo-ng.py` forwarding to `papagayo-vue.py` so existing scripts and shortcuts remain functional.
2. **Contributor & Redevelopment Attribution for Victory Ukpong**:
   - Update `about_markdown.html`, `AboutBoxQT.py`, `version_information.txt`, `metadata.json`, and `app.py` to prominently list **Victory Ukpong** as lead redeveloper and contributor with active redevelopment in 2026.
3. **Theme Engine (Dark Grey Default, Presets & Customizer)**:
   - Enforce **Dark Grey** (#121214 / #18181b / #27272a charcoal) as the primary default theme (ensuring no light office theme is forced as default).
   - Provide instant selectable presets for **Light** (clean studio paper) and **Slate** (modern indigo-slate).
   - Enable full **Custom Color Scheme** with live pickers (accent, page background, card surface, text color, and quick color swatches) with persistent storage.
4. **Dual Windows Executable Architecture (`Papagayo-VUE.exe` + `Papagayo-VUE_debug.exe`) & GitHub Action**:
   - Update PyInstaller specifications and `build_windows.py` to compile **both**:
     - `Papagayo-VUE.exe` (clean windowed release without CMD popup).
     - `Papagayo-VUE_debug.exe` (console enabled directly in CMD terminal with verbose stderr/stdout logs to immediately diagnose crash reasons).
   - Create `.github/workflows/windows-build.yml` GitHub Action workflow to automate building and bundling both executables into `Papagayo-VUE-Windows-x64.zip`.
5. **Beginner-Friendly Crash Diagnostic Suite (`diagnose_crash.py`)**:
   - Provide an automated test script and web button that verifies Python version, Qt backend, audio drivers, file paths, and syntax, generating a cleanly formatted report ready to be copy-pasted directly into chat for instant troubleshooting.

---

## 2. Technical Architecture & File Changes

### A. Python File Renaming & Entrypoints
- **Primary Launcher**: `papagayo-vue.py` (migrated from `papagayo-ng.py`).
  - Launches desktop Qt GUI when display is available or passes arguments to CLI batch lipsync processor.
- **Compatibility Wrapper**: `papagayo-ng.py` (imports and executes `papagayo-vue.main()`).
- **Web & Build Entrypoints**:
  - `main.py`: imports `app` and references `papagayo-vue.py`.
  - `package.json`: scripts updated to `"dev": "python3 main.py"`, `"start": "python3 main.py"`, `"build": "python3 -c 'import app, main; print(\"Build check OK\")'"`.
  - `app.py`: CLI execution endpoint updated to invoke `papagayo-vue.py`.

### B. Contributor Credits & About Dialogs
- **`about_markdown.html`**:
  - Title: **Papagayo-VUE Lip-Sync Animation Studio**
  - Prominent attribution: **"Redeveloped by Victory Ukpong in 2026"**
  - Contributors list: Includes **Victory Ukpong (Lead Redeveloper & 9-DOF Architect, 2026)** alongside original author Mike Clifton (2005) and Morevna Project contributors.
- **`version_information.txt`**:
  - `CompanyName`: Victory Ukpong
  - `FileDescription`: Papagayo-VUE Lip-Sync Animation Studio
  - `LegalCopyright`: Copyright (C) 2026 Victory Ukpong & Contributors
  - `ProductName`: Papagayo-VUE
- **`app.py` & `metadata.json`**:
  - Header branding: `Papagayo-VUE • Developed by Victory Ukpong and developed in 2026`.

### C. Theme Engine
- **Web Studio (`app.py`)**:
  - Default theme: `data-theme="dark-grey"` (charcoal studio background).
  - Presets: `dark-grey` (Default), `light`, `slate`, `custom`.
  - Custom Color Swatches & Inputs: Accent color, background tone, card surface, and text color.
  - Waveform canvas and viseme hover tooltips dynamically adapt their background, center line, and wave envelopes to the selected theme.
- **Desktop Application (`SettingsQT.py`, `rsrc/themes/`)**:
  - QSS files: `rsrc/themes/dark_grey.qss`, `rsrc/themes/light.qss`, `rsrc/themes/slate.qss`.
  - Settings dialog connects to theme QSS stylesheets.

### D. Dual Windows Executables (`Papagayo-VUE.exe` & `Papagayo-VUE_debug.exe`)
- `papagayo-vue.spec`:
  - Target 1: `Papagayo-VUE.exe` with `console=False` (release).
  - Target 2: `Papagayo-VUE_debug.exe` with `console=True` (CMD terminal debug output).
- `build_windows.py`:
  - Executes PyInstaller to build both binaries.
  - Packages both executables, `rsrc/`, `phonemes/`, `breakdowns/`, and documentation into `dist/Papagayo-VUE-Windows/` and creates `dist/Papagayo-VUE-Windows-x64.zip`.
- `.github/workflows/windows-build.yml`:
  - Runs on `windows-latest`.
  - Installs dependencies and runs `python build_windows.py`.
  - Uploads the portable zip containing both binaries as a GitHub Release/workflow artifact.

### E. Crash Diagnostic Suite (`diagnose_crash.py`)
- Independent Python script executable via `python3 diagnose_crash.py` or through the Web Studio UI button.
- Comprehensive checks:
  1. Python version, architecture (64-bit), OS platform.
  2. Qt backend detection (`PySide6`, `PyQt5`, `PySide2`, or headless fallback).
  3. Audio engine verification (`wave`, `pydub`, `sounddevice`, `scipy`).
  4. File paths and asset tree validation (`rsrc/mouths`, `rsrc/languages`, `rsrc/themes`, `.ui` files).
  5. Document parser & phoneme conversion kit sanity check.
  6. 9-DOF keyframe engine test.
- Outputs a copy-pasteable summary block and writes to `crash_diagnostic.txt`.

---

## 3. Step-by-Step Implementation Steps

### Step 1: Rename `papagayo-ng.py` to `papagayo-vue.py` & Update References
- Create `papagayo-vue.py` with updated branding and entrypoints.
- Create compatibility shim in `papagayo-ng.py` forwarding execution to `papagayo-vue.py`.
- Update `main.py`, `app.py`, and `build_windows.py`.

### Step 2: Update Contributor Credits & About Files
- Update `about_markdown.html` with Victory Ukpong as lead redeveloper (2026) and contributor.
- Update `version_information.txt` and `file_version_info.txt`.
- Update `metadata.json` and `app.py` header branding to `Papagayo-VUE`.

### Step 3: Finalize Theme Settings (Dark Grey Default, Presets, Customizer)
- Ensure default theme is set to `dark-grey` across `app.py` and desktop QSS settings.
- Verify live custom color picker updates CSS variables and waveform canvas.

### Step 4: Configure Dual Windows Executable Build & GitHub Action
- Create `papagayo-vue.spec` with both `Papagayo-VUE.exe` and `Papagayo-VUE_debug.exe`.
- Update `build_windows.py` to bundle both executables into `dist/Papagayo-VUE-Windows/`.
- Create `.github/workflows/windows-build.yml` GitHub Actions workflow.

### Step 5: Implement `diagnose_crash.py`
- Create `diagnose_crash.py` with standalone execution and clear sectioned logs.
- Add "Run Crash Diagnostics" and "Copy Diagnostic Log" buttons to the Web Studio interface.

---

## 4. Verification & Testing Plan
1. **File Renaming & Launch Verification**:
   - Verify `python3 papagayo-vue.py --help` runs and outputs help text.
   - Verify `python3 papagayo-ng.py --help` compatibility shim forwards seamlessly.
2. **Web Studio & Theming Verification**:
   - Verify server starts and responds on port 3000.
   - Verify Dark Grey is the default theme, with Light, Slate, and Custom color pickers functional.
3. **Diagnostics Tool Verification**:
   - Run `python3 diagnose_crash.py` and verify all checks pass and generate `crash_diagnostic.txt`.
4. **Build & Spec Verification**:
   - Verify `papagayo-vue.spec` and `build_windows.py` syntax and module validation.
