# Papagayo-NG Modernization & Crucial Files Backup Implementation Plan

Comprehensive modernization, diagnostics, and backup plan for Papagayo-NG: creating a media-free GitHub Actions backup pipeline, providing exhaustive agentic handover and API documentation, ensuring cross-platform stability, and establishing the repair roadmap.

## User Review & Critical Decisions

> [!IMPORTANT]
> **Backup & Handover Implementation**:
> 1. **Crucial Files Backup Workflow (`.github/workflows/backup.yml`)**:
>    - Implemented GitHub Actions CI workflow that triggers on `workflow_dispatch` and `push` to `main`/`master`.
>    - Employs `util/package_backup.py` to strictly filter out all media files (`*.wav`, `*.mp3`, `*.ogg`, `*.flac`, `*.png`, `*.jpg`, `*.jpeg`, `*.bmp`, `*.ico`, `*.icns`, `*.hqx`, `rsrc/mouths/`, etc.) while packaging 100% of the core animation engine, language dictionaries, phonetic breakdown rules, UI forms, and build configurations into a clean, lightweight zip archive (~2 MB vs hundreds of MBs with media).
>    - Formally verifies the presence of `AGENTIC_HANDOVER.md` and `API_KIT.md` at the root of the archive and uploads via `actions/upload-artifact@v4`.
> 2. **Agentic Handover Document (`AGENTIC_HANDOVER.md`)**:
>    - Comprehensive architecture mapping, file responsibilities, resolution history of dev server startup and file loading defects, cross-platform Qt abstractions, and protocol rules for future agents.
> 3. **API Kit Document (`API_KIT.md`)**:
>    - Complete reference for CLI automation flags (`--cli`, `-i`, `-o`, `--output-type`, `--mouths`, `--voice`, `--fps`, `--lang`), Python core data models (`LipsyncDoc`, `LipsyncVoice`, `LipSyncObject`), audio engine (`SoundPlayer`), Qt cross-version compatibility (`qt_compat`), and Web Studio HTTP REST endpoints.

---

## 1. Overview & Core Concept

- **What It Does**: Papagayo-NG is a specialized lip-sync animation tool that aligns audio dialogue with phonemes and viseme mouth shapes (Preston Blair, Rhubarb, Fleming & Dobbs, Gary C Martin, Hunanbean CMU39) and exports synchronized lip-sync data to animation software such as Moho (Anime Studio), Synfig, Blender, OpenToonz, and game engines (JSON/Alelo).
- **Current State & Progress**:
  - Dev server running on `0.0.0.0:3000` via standard library `http.server.ThreadingHTTPServer` with zero external dependencies.
  - Silent rejection and extension case sensitivity bugs in `LipsyncFrameQT.py` and `papagayo-ng.py` resolved with automatic fallback audio resolution.
  - Waveform amplitude calculation modernized with pure Python RMS calculations for environments lacking `audioop`.
  - Media-free backup toolchain (`util/package_backup.py` and `.github/workflows/backup.yml`) created and verified with 108 crucial files packaged and zero media leakage.
  - `AGENTIC_HANDOVER.md` and `API_KIT.md` generated at the project root and verified inside the archive.

---

## 2. Technical Decisions & Architecture

- **Decision 1: Deterministic Python Packager for Crucial Files**
  - *Chosen Approach*: `util/package_backup.py` accompanied by automated integrity verification.
  - *Why*: Allows both local CLI testing (`python3 util/package_backup.py`) and reproducible GitHub Actions execution (`.github/workflows/backup.yml`), ensuring media files (mouth PNGs, WAVs, icons) are systematically excluded while linguistic dictionaries (`rsrc/languages/`), breakdown rules, translation tables, and Python sources are preserved.
  - *Integrity Check*: Post-generation audit automatically fails the pipeline if any media file extension or missing handover document is detected.

- **Decision 2: Master Handover and API Kit Documents**
  - *Chosen Approach*: Standalone `AGENTIC_HANDOVER.md` and `API_KIT.md` at repository root.
  - *Why*: Provides immediate, actionable technical documentation for both AI agents resuming across truncated sessions and human developers integrating Papagayo-NG into automation scripts or build pipelines.

- **Decision 3: Zero-Dependency Dev Server & Headless Fallbacks**
  - *Chosen Approach*: Standard library HTTP server on port 3000 and headless mock Qt widgets in `qt_compat.py`.
  - *Why*: Enables instant dev server startup and headless test runners in any containerized or CI/CD environment without requiring an active X11 display or heavy third-party web frameworks.

---

## 3. Verification Roadmap & Completed Milestones

1. [x] **Dev Server Startup**: Configured `package.json` `"dev"` script and implemented zero-dependency HTTP server in `app.py`.
2. [x] **Underlying File Loading Fixes**: Updated `LipsyncFrameQT.py` and `papagayo-ng.py` with case-insensitive extension matching and fallback audio resolution for `.pgo` projects.
3. [x] **Waveform & Audio Robustness**: Implemented pure-Python RMS amplitude calculations and boundary protections in `SoundPlayer.py`.
4. [x] **Agentic Handover Documentation**: Created `AGENTIC_HANDOVER.md` detailing codebase architecture, resolved bugs, and rules for continuation.
5. [x] **API Kit Documentation**: Created `API_KIT.md` detailing CLI arguments, Python class methods, SoundPlayer hooks, and Web Studio REST endpoints.
6. [x] **Media-Free Crucial Files Backup**:
   - Created `util/package_backup.py` and `.github/workflows/backup.yml`.
   - Verified local creation: 108 crucial files packaged, 0 media files leaked, `AGENTIC_HANDOVER.md` and `API_KIT.md` verified at archive root.
7. [ ] **Proceed with Repair & Modernization Tasks**:
   - Validate standalone Windows PyInstaller build configuration in `papagayo-ng.spec` and `build_windows.py`.
   - Expand unit test coverage for headless batch export conversions (`--cli -i test.pgo -o test.dat`).
   - Add touch/stylus hit-box tolerance on waveform markers in `WaveformViewRewrite.py`.
