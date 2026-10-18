# Papagayo-NG (Modernized)

![Papagayo-NG](rsrc/papagayo-ng.png)

**Papagayo-NG** is an open-source lip-sync animation tool designed for 2D and 3D animators. It allows you to synchronize recorded dialogue with phonemes and viseme mouth shapes (Preston Blair, Fleming & Dobbs, Rhubarb, Hunanbean CMU39) and export sync data to animation software such as **Moho (Anime Studio)**, **Synfig**, **Blender**, **OpenToonz**, or game engines via JSON and Alelo.

---

## What's New in this Modernization Update

- **Modern Qt Support (PySide6 / Qt 6)**: Fully modernized to run on **Python 3.10, 3.11, 3.12+** via `PySide6`, while maintaining backward-compatibility with legacy `PySide2` (Python 3.7–3.9).
- **Automated Windows Standalone Packaging**: Replaced outdated `py2exe` with a clean `PyInstaller` pipeline (`build_windows.py` and `papagayo-ng.spec`) producing self-contained `.exe` and `.zip` archives.
- **GitHub Actions CI/CD Matrix**: Automated workflow (`.github/workflows/build-windows.yml`) that compiles Windows binaries on push, manual dispatch, or release tags and attaches artifacts.
- **Preserved Studio Landscape Layout**: Maintains the stable, tested timeline layout to ensure scrubbing and mouth previews remain rock solid.
- **Android Mod Roadmap & Strategy**: Structured architectural guidelines for mobile/tablet deployment with landscape baseline and planned orientation toggling.

---

## System Requirements

### Modern Setup (Recommended: Python 3.10+)
Install dependencies using the updated `requirements.txt`:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Key packages installed:
* `PySide6 >= 6.5.0`
* `sounddevice >= 0.4.6`
* `cffi >= 1.15.0`
* `numpy >= 1.22.0`
* `pydub >= 0.25.1`
* `anytree >= 2.8.0`
* `audioread >= 3.0.0`
* `appdirs >= 1.4.4`
* `pyyaml >= 6.0`
* `pyinstaller >= 6.0.0`
* `pyinstaller-versionfile >= 2.1.1`

### Legacy Setup (Python 3.7 - 3.9)
If running on legacy environments requiring `PySide2`:
```bash
pip install -r requirements-legacy.txt
```

---

## Running Locally

To launch Papagayo-NG from source:
```bash
python papagayo-ng.py
```

### Command Line Interface (CLI) Usage
Papagayo-NG also supports headless CLI execution for batch processing:
```bash
python papagayo-ng.py --cli -i path/to/audio.wav -o path/to/output.dat --output-type MOHO
```
Options:
* `-i FILE`: Input audio file (`.wav`, `.mp3`, `.ogg`, `.m4a`) or project file (`.pgo`, `.pg2`).
* `-o FILE`: Target output file or folder.
* `--output-type`: Exporter format (`MOHO`, `JSON`, `ALELO`, `IMAGES`, `PGO`, `PG2`).
* `--use-rhubarb`: Run Rhubarb automatic lip-sync recognition on input.
* `--use-allosaurus`: Run Allosaurus phonetic recognizer on input.
* `--fps INT`: Set target frame rate (default 24).

---

## How to Build into a Windows Application (.exe / .zip)

You can build a standalone Windows distribution that runs on any modern 64-bit Windows machine without needing Python installed.

### Option A: Automated One-Click Build Script (Recommended)
1. Open PowerShell or Command Prompt in the repository root.
2. Ensure dependencies are installed:
   ```cmd
   pip install -r requirements.txt
   ```
3. Run the packaging pipeline:
   ```cmd
   python build_windows.py
   ```
4. When finished, your outputs are located in `dist/`:
   * **`dist/Papagayo-NG-Windows/`**: Portable folder containing `papagayo-ng.exe`, assets, dictionaries, and mouth shapes.
   * **`dist/Papagayo-NG-Windows-x64.zip`**: Ready-to-distribute compressed archive.

### Option B: Direct PyInstaller Invocation
If you prefer running PyInstaller directly:
```cmd
pyinstaller --noconfirm --clean papagayo-ng.spec
```
The resulting executable will be placed in `dist/papagayo-ng.exe`. Ensure you keep the `rsrc/`, `breakdowns/`, and `phonemes/` folders alongside the executable.

### Option C: NSIS Installer Setup
To generate a Windows setup wizard installer (`Papagayo-NG-Installer.exe`):
1. Install [NSIS (Nullsoft Scriptable Install System)](https://nsis.sourceforge.io/).
2. Run the build script to populate `dist/Papagayo-NG-Windows/`.
3. Compile the script using `makensis`:
   ```cmd
   makensis papagayo-ng.nsi
   ```

---

## Automated GitHub Actions CI / CD Workflow

This repository includes a continuous integration workflow located at `.github/workflows/build-windows.yml`:

* **Automatic Artifact Creation**: On every push to `master`/`main` or pull request, GitHub Actions launches a `windows-latest` virtual runner, installs Python 3.11, builds the standalone application, and publishes `Papagayo-NG-Windows-x64.zip` as a downloadable workflow artifact.
* **Release Publishing on Git Tag**: When you tag a release (e.g. `git tag v1.4.2 && git push --tags`), the workflow automatically creates a GitHub Release and attaches the packaged zip file.
* **Manual Dispatch**: You can manually trigger a build at any time from the GitHub repository:
  1. Go to the **Actions** tab on GitHub.
  2. Select **Build Windows Application**.
  3. Click **Run workflow**.
  4. Download the compiled zip artifact once the run finishes.

---

## Android Mod: Architecture, Landscape Baseline & Orientation Roadmap

For mobile animators and tablet users running Android, Papagayo-NG is designed with an **incremental adaptation model**:

### 1. Landscape Layout as the Primary Baseline
To avoid breaking the waveform visualization, timeline scrubbing, and mouth shape preview during the initial modernization:
* The original **landscape studio layout** is preserved as the default display.
* **Recommended Resolution**: 1280x720 or higher in landscape orientation.
* The multi-track timeline requires horizontal screen width for accurate frame positioning (dragging phonemes and words across dialogue bars).

### 2. Android Deployment Pathways
There are three recommended methods to run or package Papagayo-NG on Android:

* **Method 1: BeeWare Briefcase / Chaquopy APK Packaging**
  * Android packaging wraps the Python runtime and PySide/Qt bindings via Chaquopy or BeeWare.
  * In the Android manifest (`AndroidManifest.xml`), specify landscape orientation:
    ```xml
    <activity
        android:name=".MainActivity"
        android:screenOrientation="landscape"
        android:configChanges="orientation|screenSize">
    ```
* **Method 2: Pydroid 3 (Direct On-Device Execution)**
  1. Install **Pydroid 3** and the **Pydroid repository plugin** from Google Play.
  2. Open Pydroid Terminal and install dependencies:
     ```bash
     pip install sounddevice numpy pydub anytree pyyaml
     ```
  3. Clone or copy the Papagayo-NG project folder to your device storage.
  4. Run `python papagayo-ng.py` in landscape mode.
* **Method 3: Termux + X11 Desktop**
  Run full desktop Linux binaries via Termux with `termux-x11` for a complete tablet studio setup.

### 3. Future Orientation Toggle Roadmap (Assistive Mobile Mod)
Planned additions for subsequent mobile revisions:
* [ ] **Orientation Switcher**: Top toolbar toggle allowing switching between **Studio Landscape Mode** (full timeline + waveform) and **Dialogue Breakdown Mode** (vertical phrase list + pronunciation inspector).
* [ ] **Touch Scrubbing Enhancements**: Expanded touch hitboxes (minimum 44x44px) for timeline markers and pinch-to-zoom on the waveform.
* [ ] **Floating Viseme Preview**: Resizable, collapsible mouth shape preview overlay for compact tablet screens.

---

## Project Structure

```
├── .github/workflows/
│   └── build-windows.yml          # GitHub Actions Windows CI build & release workflow
├── breakdowns/                    # Language breakdown phonetic dictionaries
│   ├── dutch_breakdown.py
│   ├── french_breakdown.py
│   ├── german_breakdown.py
│   ├── korean_breakdown.py
│   ├── spanish_breakdown.py
│   └── ...
├── phonemes/                      # Phoneme sets in JSON format
│   ├── CMU_39.json
│   ├── fleming_dobbs.json
│   ├── preston_blair.json
│   └── rhubarb.json
├── rsrc/                          # UI assets, icons, mouth shape illustrations
│   ├── mouths/                    # Viseme image sets (Preston Blair, Rhubarb, etc.)
│   ├── languages/                 # Language configuration ini files & word lists
│   ├── papagayo-ng.ui             # Qt Designer main UI template
│   └── icons/                     # SVG / PNG action icons
├── qt_compat.py                   # Cross-Qt compatibility shim (PySide6 & PySide2)
├── papagayo-ng.py                 # Application entry point & CLI handler
├── LipsyncDoc.py                  # Project document model, voice tracks, and exporters
├── LipsyncFrameQT.py              # Main application window and controller
├── WaveformViewRewrite.py         # Waveform audio visualizer and timeline ruler
├── MouthViewQT.py                 # Live viseme preview canvas
├── SoundPlayer.py                 # Audio playback engine (sounddevice + pydub)
├── SoundPlayerNew.py              # Windows Media Foundation audio backend
├── SoundPlayerQT.py               # Qt Multimedia audio backend
├── Rhubarb.py                     # Rhubarb auto lip-sync bridge
├── auto_recognition.py            # Allosaurus neural phoneme recognition bridge
├── papagayongrcc.py               # Compiled Qt binary resource bundle
├── build_windows.py               # Automated Windows packaging script
├── papagayo-ng.spec               # PyInstaller specification file
├── setup.py                       # Modern setuptools packaging script
├── requirements.txt               # Modern dependencies (Python 3.10+)
├── requirements-legacy.txt        # Legacy dependencies (Python 3.7 - 3.9)
└── readme.md                      # Documentation
```

---

## Animation Software Exporters

Papagayo-NG exports synced mouth data to popular 2D/3D animation software:

* **Moho (Anime Studio)**: Exports `.dat` switch files that bind directly to Moho Switch Layers.
* **JSON**: Exports complete timeline frames, words, and phoneme labels for web players, Godot, Unity, or Unreal Engine.
* **Alelo**: Exports dialogue transcript and timestamped phoneme text files.
* **Image Sequences**: Exports numbered `.png` frames of mouth shapes matching the frame rate.

---

## Authors & Credits

* **Original Papagayo**: &copy; 2005 Mike Clifton ([Lost Marble](http://www.lostmarble.com))
* **Modifications**: &copy; 2010 Benjamin Lau
* **Papagayo-NG & Modernization**:
  * Konstantin Dmitriev ([Morevna Project](https://morevnaproject.org/))
  * Stefan Murawski
  * Azia Giles Abuara
  * Owen Gallagher
  * Victory Ukpong - Contributors & Community (2026)

## License

This software is released under the **GNU General Public License v2.0 or later** (GPL-2.0-or-later). See [gpl.txt](gpl.txt) for details.
