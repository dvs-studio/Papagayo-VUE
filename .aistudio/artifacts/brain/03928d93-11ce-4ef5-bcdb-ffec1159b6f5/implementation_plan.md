# Papagayo-NG Modernization & Cross-Platform Packaging Plan

Comprehensive modernization strategy for Papagayo-NG: upgrading from deprecated PySide2 to PySide6/Qt6, modernizing the Windows PyInstaller build toolchain, introducing automated GitHub Actions CI for Windows artifact releases, preserving the rock-solid landscape studio layout, updating documentation with step-by-step Windows and Android instructions, and structuring the Android landscape/portrait mod on the future roadmap.

## User Review & Critical Decisions

> [!IMPORTANT]
> The following decisions have been confirmed with the user in Phase 1:
> - **Modernization Path**: Modernize the existing Python codebase with PySide6/Qt6 compatibility, PyInstaller, and clean dependency management rather than rewriting from scratch, maintaining stability first.
> - **Screen Layout & Orientation**: Maintain the original landscape studio layout as the baseline. Avoid disruptive UI rewrites in this first major modernization to ensure existing workflows, waveform scrubbing, and mouth previews do not break.
> - **Packaging & CI Pipeline**: Prioritize modern PyInstaller standalone Windows packaging (`.exe` and `.zip`), automate with a GitHub Actions CI matrix workflow for Windows releases with artifact uploads, and document build instructions in `readme.md`.
> - **Android Mod Strategy**: Maintain the landscape orientation baseline in the documentation and roadmap; prepare the compatibility shim so Android packaging (via Chaquopy/BeeWare or web container) can be introduced incrementally after the core desktop modernization is stable.

---

## 1. Overview & Core Concept

- **What It Does**: Papagayo-NG is a specialized lip-sync animation tool that aligns audio dialogue with phonemes and viseme mouth shapes (Preston Blair, Fleming & Dobbs, Rhubarb, Hunanbean CMU39) and exports synchronized lip-sync data to animation software such as Moho (Anime Studio), Synfig, Blender, OpenToonz, and game engines (JSON/Alelo).
- **Current State & Codebase Review**:
  - The repository contains the complete original Python codebase alongside an upstream mirror (`papagayo-ng-upstream/`).
  - Core logic relies on `PySide2` (Qt 5), which is deprecated and cannot compile or install wheels on modern Python 3.10–3.12+ environments.
  - The packaging system (`setup.py`) uses ancient `distutils` and `py2exe`, which fail on modern Python.
  - The timeline editor and waveform visualizer (`WaveformViewRewrite.py`, `LipsyncFrameQT.py`, `MouthViewQT.py`) are fully functional desktop Qt widgets that need PySide6/Qt6 API harmonization (e.g., `QAction`, enum namespaces like `QtCore.Qt.AlignmentFlag`, `QAudioOutput`, and Qt UI loaders).
- **Target Audience / Persona**: 2D and 3D animators, game developers, motion designers, and hobbyists looking for a modern, reliable lip-sync tool on Windows (and eventually mobile/Android).
- **Key Value**: Restoring out-of-the-box buildability on modern systems, eliminating deprecated dependencies, providing reproducible 1-click Windows builds via GitHub Actions, and delivering updated documentation.

---

## 2. User Experience & Visual Design

- **Core User Flow**:
  1. **Project Setup**: User opens Papagayo-NG, creates or loads a project (`.pgo` / `.pg2`), and imports an audio track (`.wav`, `.mp3`, `.ogg`, `.m4a`).
  2. **Transcription & Breakdown**: User types spoken dialogue or runs automated phoneme recognition (via Rhubarb or Allosaurus integration). Spoken words are decomposed into language phonemes via phonetic dictionary lookup.
  3. **Timeline & Waveform Editing**: User navigates the waveform in the classic landscape layout, adjusts word and phoneme marker boundaries along the timeline, and scrubs audio with real-time playback.
  4. **Viseme Preview**: In the mouth view panel, selected mouth sets (Preston Blair, Rhubarb, Hunanbean) display the exact viseme for the active frame.
  5. **Export**: Export animation switch layers to Moho (`.dat`), JSON, Alelo, or frame sequences.

- **Layout & Visual Identity**:
  - **Aesthetic**: Utilitarian, focused desktop studio layout with dark/neutral contrast.
  - **Landscape Studio Orientation**: Top menu/toolbar -> Left-to-right split with Voices list and Mouth preview on the upper tier, Dialogue text box in center, and multi-track Timeline/Waveform spanning the full bottom viewport.
  - **Mobile/Android Adaptation Strategy**: Retain the landscape layout as the primary mode to guarantee timeline scrubbing precision. The Android adaptation section in documentation will specify minimum recommended resolution (1280x720 landscape) with touch-friendly scrubbing tolerances.

---

## 3. Key Product Decisions & Trade-Offs

- **Decision 1: PySide6 (Qt 6) Compatibility Shim (`qtpy` or dual PySide2/PySide6 import fallback)**
  - *Chosen Approach*: Implement a clean Qt compatibility layer (`qt_compat.py` or standardized imports) that seamlessly supports `PySide6` (modern Python 3.10+) while maintaining fallback compatibility with `PySide2`.
  - *Why*: Allows the codebase to run natively on modern operating systems without breaking older setups or requiring a complete codebase rewrite.
  - *Alternatives Considered*: Complete rewrite into a web app (rejected by user in favor of incremental modernization to avoid breaking existing features).

- **Decision 2: Modern PyInstaller Build Pipeline & `setup.py` Replacement**
  - *Chosen Approach*: Replace legacy `py2exe` in `setup.py` with an updated, robust `papagayo-ng.spec` PyInstaller configuration that bundles all assets (`rsrc/`, `breakdowns/`, `phonemes/`, dictionaries, icons) into a standalone Windows `.exe` and `.zip`.
  - *Why*: PyInstaller is the industry standard for cross-platform Python packaging, handles hidden imports and Qt dynamic libraries cleanly, and runs reliably in CI.

- **Decision 3: GitHub Actions CI for Windows Release Artifacts**
  - *Chosen Approach*: Create `.github/workflows/build-windows.yml` that checks out code, sets up Python 3.11, installs modern dependencies, compiles resources, runs PyInstaller to build a portable standalone release, zips the bundle, and attaches it as a GitHub Actions workflow artifact (and draft release on tag).
  - *Why*: Eliminates "works on my machine" issues and gives users and contributors instant, reproducible binary downloads.

- **Decision 4: Detailed Documentation Update in `readme.md`**
  - *Chosen Approach*: Completely revamp `readme.md` with modern requirements (Python 3.10+, PySide6), local development instructions, Windows packaging guide (PyInstaller + NSIS), GitHub Actions CI usage, and an Android mod roadmap detailing landscape orientation setup and packaging strategies.

---

## 4. Technical Architecture & Data Strategy (Technical Reference)

### System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Papagayo-NG Studio                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   ┌───────────────────┐    ┌───────────────────┐   ┌────────────────┐  │
│   │   Voices & Words  │    │   Mouth Preview   │   │ Phoneme Set    │  │
│   │   Hierarchy Tree  │    │   (MouthViewQT)   │   │ (Preston Blair,│  │
│   │   (LipsyncDoc)    │    │   Viseme Images   │   │  Rhubarb, etc) │  │
│   └─────────┬─────────┘    └─────────▲─────────┘   └────────┬───────┘  │
│             │                        │                      │          │
│             ▼                        │                      ▼          │
│   ┌──────────────────────────────────┴──────────────────────────────┐  │
│   │                  Dialogue & Breakdown Engine                    │  │
│   │        Language Dictionaries (CMU, Dutch, German, etc.)         │  │
│   │        Auto-recognition: Allosaurus & Rhubarb CLI               │  │
│   └──────────────────────────────────┬──────────────────────────────┘  │
│                                      │                                 │
│   ┌──────────────────────────────────▼──────────────────────────────┐  │
│   │                 Waveform & Multi-Track Timeline                 │  │
│   │        Audio playback (SoundPlayer, SoundPlayerQT/New)          │  │
│   │        Waveform rendering, Frame markers, Scrubbing             │  │
│   └──────────────────────────────────┬──────────────────────────────┘  │
│                                      │                                 │
│   ┌──────────────────────────────────▼──────────────────────────────┐  │
│   │                         Exporters                               │  │
│   │        Moho (.dat) │ JSON │ Alelo (.txt) │ Image Sequence       │  │
│   └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### Packaging & Release Pipeline

```
GitHub Push / Release Tag
          │
          ▼
GitHub Actions CI (windows-latest)
          │
          ├──> Python 3.11 Environment Setup
          ├──> pip install -r requirements.txt (PySide6, numpy, pydub, etc.)
          ├──> Resource Compilation (pyside6-rcc -> papagayongrcc.py)
          ├──> PyInstaller Build (papagayo-ng.spec)
          │         └──> Bundles executable + rsrc/ + phonemes/ + breakdowns/
          ├──> Package ZIP Archive: Papagayo-NG-Windows-x64.zip
          └──> Upload Artifact to GitHub Action Run / Create Release
```

### Phased Execution Roadmap

1. **Phase 1: Qt Compatibility & Modern Dependency Setup**
   - Provide a dual-compatible Qt wrapper (`qt_compat.py`) supporting `PySide6` with `PySide2` fallback.
   - Update `requirements.txt` to include `PySide6`, `pyinstaller`, and modern dependency pins.
   - Ensure imports across `papagayo-ng.py`, `LipsyncFrameQT.py`, `WaveformViewRewrite.py`, `MouthViewQT.py`, `SettingsQT.py`, and `AboutBoxQT.py` cleanly use the compatibility layer.

2. **Phase 2: Windows Build Configuration**
   - Modernize `papagayo-ng.spec` to include all required data directories (`rsrc`, `phonemes`, `breakdowns`), hidden imports, and icon resources.
   - Update `setup.py` to use modern setuptools / PyInstaller invocation instead of dead `py2exe`.

3. **Phase 3: GitHub Actions CI Matrix Workflow**
   - Create `.github/workflows/build-windows.yml` configured to build on `windows-latest` with artifact publishing.
   - Include test triggers on both `workflow_dispatch` and `push`/`release`.

4. **Phase 4: Comprehensive README & Android Documentation**
   - Update `readme.md` with:
     - Modern quickstart (Python 3.10+, virtual environment, PySide6).
     - Step-by-step Windows executable compilation instructions.
     - GitHub Actions CI workflow usage.
     - Android Mod section: Maintaining landscape layout baseline, touch navigation recommendations, and future APK packaging paths (BeeWare Briefcase / Chaquopy / Pydroid).
