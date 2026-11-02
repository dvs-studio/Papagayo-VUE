# Papagayo-VUE Studio Stabilization, Dubbing & Audio Workflow Plan

This update permanently resolves the cross-thread `QTimer` termination crash on clean Windows installations, introduces native Voice Recording and Microsoft TTS project initialization, enables Continuous Generation lip-sync appending, adds a non-destructive Audio Range Selection & Dubbing Modifier tool, updates the Rhubarb automated downloader to v1.14.0 (`Rhubarb-Lip-Sync-1.14.0-Windows.zip`), and upgrades the Preview Chamber with auto-sizing, edge antialiasing, and customizable background color controls.

### User Review & Critical Decisions

> [!IMPORTANT]
> The following architectural and user preferences were established from your feedback and are incorporated into the build plan:
> - **Rhubarb Lip-Sync v1.14.0**: Pinned direct download URL updated to `https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Windows.zip` (with matching macOS and Linux v1.14.0 archives) along with GitHub API `User-Agent: Papagayo-VUE/2026` headers to prevent 403 Forbidden errors.
> - **Dev Server & Web Studio Health**: Verified dev server boots unbuffered on port 3000 with socket reuse (`SO_REUSEADDR`) and standard HTTP 200 response.
> - **New Audio & Continuous Generation Access**: Dedicated buttons ("New Audio" and "Append Lip-Sync") placed directly in the top Studio Toolbar and under the `File` menu.
> - **Dubbing / Range Modifier UX**: Click-and-drag range selection on the timeline waveform, activated via a dedicated "Range Select / Dubbing Mode" toggle button so normal timeline scrubbing remains unaffected. Includes auto-saving dub audio to a temporary file before commit.
> - **Timeline & Keyframing**: Visual diamond keyframe markers on the waveform ruler with an "Enable Keyframe" toggle checkbox.
> - **Preview Chamber & Export**: White canvas background by default (user-customizable via palette), with auto-scaling to prevent cropping and an export toggle for transparent PNG sequence vs. solid background.

---

### 1. Overview & Core Concept

- **What It Does**:
  1. Eliminates the runtime fatal error `QObject::killTimer: Timers cannot be stopped from another thread` by moving all playback timing, thread callbacks, and audio stop invocations onto the Qt GUI event thread using decoupled Qt Signals (`QtCore.Signal`).
  2. Enables creators to start a lip-sync project immediately from their microphone ("Voice Recording") or from Microsoft Speech API / TTS, with automatic pitch-safe WAV encoding.
  3. Supports Continuous Generation: append subsequent dialogue sentences, character phrases, or audio chunks to an existing timeline without overwriting previous keyframes or alignment.
  4. Introduces an Audio Dubbing / Voice Modifier range tool: creators highlight a region on the waveform to re-voice, pitch-shift, or replace dialogue with automatic temp-file management.
  5. Provides "New Audio..." and "Export Audio..." in the `File` menu.
  6. Fixes multi-character preview cropping and edge jaggies through responsive aspect-ratio fitting (`KeepAspectRatio`) and bilinear antialiased pixmap filtering.
  7. Downloads Rhubarb Lip-Sync v1.14.0 seamlessly without HTTP 403 or broken link errors.

- **Target Persona**: Animators, game developers, dialogue editors, and voice actors creating synchronized 2D/3D mouth movements without manual frame-by-frame rigging.

- **Key Value**: Rock-solid stability on any clean Windows machine without python pre-installed, combined with a seamless voice recording and incremental dubbing workflow.

---

### 2. User Experience & Visual Design

#### Key User Flows

1. **New Audio Flow (Voice Recording / TTS)**:
   - Click `File -> New Audio...` or the toolbar button `[+ New Audio]`.
   - A modal dialog provides two tabs:
     - **Microphone Recording**: Click `Record`, speak into mic with real-time level meter, click `Stop`, preview playback, enter transcript text, and click `Create Lip-Sync`.
     - **Microsoft TTS**: Choose system voice (SAPI5 / Windows Speech), enter script text, preview, and generate project.
   - The project initializes instantly with the generated 16-bit PCM WAV audio and initial phrase breakdowns.

2. **Continuous Generation (Append Lip-Sync)**:
   - Click `File -> Append Lip-Sync...` or toolbar button `[+ Append Dialogue]`.
   - Record additional speech, enter TTS text, or pick an additional audio file.
   - The new audio is seamlessly appended to the end of the project's sound buffer, and the new phrases and phonemes are placed sequentially without disturbing existing frames.

3. **Audio Range Dubbing & Voice Modifier Flow**:
   - Click the toolbar toggle button `[Dub / Range Select Mode]` (highlights in amber).
   - Click and drag over the waveform to select an in/out region (rendered as a glowing translucent blue selection box with frame timestamps).
   - Click `[Apply Dub / Voice Shift]`: Choose a voice preset (Robot, Gender Shift, Chipmunk, Custom Pitch) or record replacement dialogue for that segment.
   - Audio is generated and previewed in temporary cache; on confirmation, it splices into the project audio with instant waveform re-rendering.
   - Click `File -> Export Audio...` to save the final compiled dialogue as `.wav` or `.mp3`.

4. **Multi-Character Preview & Background Customization**:
   - The preview chamber displays with a clean white canvas background.
   - Right-click or use `Preview -> Background Color...` to select any custom color (white, black, greenscreen chroma green, or gray).
   - In Multi-Character split or grid views, character portraits and mouths auto-scale within their viewport cells with smooth antialiasing (`SmoothPixmapTransform`), eliminating pixel cracking and edge clipping.
   - When exporting image sequences (`File -> Export -> Image Sequence...`), a checkbox `[x] Transparent Background (Alpha Channel)` toggles between transparent PNGs and the selected background color.

---

### 3. Key Product Decisions & Trade-Offs

- **Cross-Thread Timer Architecture**:
  - *Chosen Approach*: Replace raw `_thread.start_new_thread` playback loops and direct `QCoreApplication.processEvents()` calls in `SoundPlayerQT.py` / `SoundPlayer.py` with standard Qt `QThread` / `QTimer` instances bound to the main thread, communicating exclusively via Qt Signals (`playback_tick`, `playback_stopped`).
  - *Why*: In PySide6/Qt, interacting with `QObject` timers from OS worker threads triggers `QObject::killTimer: Timers cannot be stopped from another thread` and causes fatal segfaults upon application exit or audio stop. Qt signals guarantee thread-affinity safety.

- **Audio Dubbing Temp Storage Strategy**:
  - *Chosen Approach*: Store non-destructive dub iterations in the system temporary directory (`util.get_temp_dir()` / `tempfile`) as standard 16-bit 44.1kHz WAV slices.
  - *Why*: Prevents corruption of the source audio during experimentation while providing an instant undo/revert path.

- **Rhubarb v1.14.0 Download Architecture**:
  - *Chosen Approach*:
    - Windows primary: `https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Windows.zip`
    - macOS primary: `https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-macOS.zip`
    - Linux primary: `https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Linux.zip`
    - Fallback: GitHub Releases API query with standard `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Papagayo-VUE/2026`.
  - *Why*: Guarantees reliable automated downloads even when GitHub's unauthenticated API is rate-limited.

---

### 4. Technical Architecture & Data Strategy

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Papagayo-VUE Main GUI                         │
│  ┌───────────────────────┐  ┌────────────────────────────────────────┐ │
│  │   Studio Toolbar      │  │        Menu Bar (File, Edit, Preview)  │ │
│  │ [+ New Audio]         │  │  - File > New Audio (Mic / TTS)        │ │
│  │ [+ Append Lip-Sync]   │  │  - File > Export Audio (WAV/MP3)       │ │
│  │ [Dub / Range Select]  │  │  - Preview > Background Color...       │ │
│  │ [Enable Keyframe] [x] │  │  - Preview > View Modes (1x1, 1x2, 2x2)│ │
│  └───────────┬───────────┘  └───────────────────┬────────────────────┘ │
│              │                                  │                      │
│              ▼                                  ▼                      │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │               WaveformView (Ruler & Audio Timeline)               │ │
│  │  - Scrubber playhead & frame counter                              │ │
│  │  - Range selection overlay (In/Out markers)                       │ │
│  │  - Visual 9-DOF keyframe diamonds on timeline ruler               │ │
│  └──────────────────────────────────┬────────────────────────────────┘ │
│                                     │                                  │
│              ┌──────────────────────┴──────────────────────┐           │
│              ▼                                             ▼           │
│  ┌───────────────────────────────┐     ┌─────────────────────────────┐ │
│  │   MouthView Preview Chamber   │     │   SoundPlayer & Effector    │ │
│  │  - Auto-scaled viewport       │     │  - Safe Qt Signals thread   │ │
│  │  - Bilinear smooth filtering  │     │  - Temp audio buffer cache  │ │
│  │  - White / custom background  │     │  - In/Out segment splicing  │ │
│  │  - Multi-character grid 2x2   │     │  - SAPI5 / Web TTS synth    │ │
│  │                               │     │  - Rhubarb v1.14.0 engine   │ │
│  └───────────────────────────────┘     └─────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

#### Verification & Quality Checks
1. Dev server verified responding HTTP 200 OK on `0.0.0.0:3000`.
2. Rhubarb v1.14.0 download verified accessible via HTTP HEAD/GET request.
3. Execute `python3 diagnose_crash.py` to ensure all Qt classes, threading wrappers, and audio bridges pass unit verification.
4. Verify audio playback starts, scrubs, and terminates without `killTimer` or `~QObject` console warnings.
5. Test recording from microphone and generating Microsoft TTS into a fresh document.
6. Verify continuous appending adds frames without altering existing mouth positions.
7. Verify timeline range dubbing correctly replaces audio and updates waveform rendering.
8. Verify multi-character grid preview displays all characters without clipping.
