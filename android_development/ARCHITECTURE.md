# Android System Architecture & Technology Stack
### Papagayo-NG Native Android Studio (API 28–34)
**Architect**: Victory Ukpong (2026)

---

## 1. Architectural Philosophy

The Android rewrite adopts the modern **MVI (Model-View-Intent) / Clean Architecture** pattern utilizing Google's recommended Android architecture guide with 100% Kotlin and Jetpack Compose.

```
┌────────────────────────────────────────────────────────┐
│                     UI LAYER                           │
│  Jetpack Compose + Material 3 (Scrubbers, Grid Preview)│
└───────────────▲────────────────────────▲───────────────┘
                │ StateFlow              │ User Intents
┌───────────────┴────────────────────────┴───────────────┐
│                   VIEWMODEL LAYER                      │
│     LipsyncProjectViewModel, AudioEffectorViewModel    │
└───────────────▲────────────────────────▲───────────────┘
                │ Coroutines             │ Use Cases
┌───────────────┴────────────────────────┴───────────────┐
│                    DOMAIN LAYER                        │
│   DofSlicerUseCase, ExportDjvSequenceUseCase, TTSEngine│
└───────────────▲────────────────────────▲───────────────┘
                │ Repositories           │ Repositories
┌───────────────┴────────────────────────┴───────────────┐
│                     DATA LAYER                         │
│  Room DB (Projects) | Oboe C++ Engine | Storage API    │
└────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### A. High-Performance Audio Engine (Oboe C++ & AAudio)
- **Challenge**: Standard Android `MediaPlayer` and `AudioTrack` introduce 40–120ms of audio output latency, which causes severe timeline desynchronization during 24 FPS lip-sync editing.
- **Solution**: Use Google's **Oboe C++ library** bound via JNI. Oboe leverages **AAudio** on Android 9+ (API 28+) and automatically falls back to OpenSL ES if required.
- **Performance**: Achieves **sub-15ms round-trip latency**, allowing exact frame scrubbing and live audio looping.

### B. Waveform Visualizer & Touch Scrubber (Jetpack Compose Canvas)
- **Rendering**: Implemented as custom hardware-accelerated Compose `Canvas`.
- **RMS Peak Pre-computation**: Audio is decoded into an in-memory 16-bit PCM array upon load; RMS peaks are computed once at 100 slices/sec and cached in a compact FloatArray.
- **Hover/Touch Floating Tooltip**: A floating thumbnail tooltip box displays above the touch cursor indicating:
  - Exact Frame Number (`Frame: 14`)
  - Active Phoneme (`AI / WQ / REST`)
  - 9-DOF Angle Viewport (`Angle 5: Front`)
  - Live Mouth Thumbnail preview

### C. 9-DOF (Degrees of Freedom) Angle Slicer & Keyframe Engine
- **Representation**: Keyframes are stored as a sorted map of `Frame -> DofKeyframe(angleId: 1..9, label: String, sourceMode: FOLDER | SPRITE_3X3)`.
- **Mode 1 (Multi-Folder)**: Directly accesses 9 directories under `/assets/mouths/<Set>/angle_<1..9>/`.
- **Mode 2 (3x3 Sprite Sheet Slicing)**:
  - Input: Single 3x3 PNG/JPG sprite grid.
  - Slicing: Uses Android `Bitmap.createBitmap(source, col * w/3, row * h/3, w/3, h/3)`.
  - Cache: In-memory LRU bitmap cache (`LruCache<String, Bitmap>`) with 32MB limit.
- **Radial Angle Menu**: Long-pressing or tapping a keyframe diamond on the timeline ruler launches a circular 9-slice radial selector (Top-Left, Up, Top-Right, Left, Center, Right, Down-Left, Down, Down-Right).

### D. Multi-Character Synchronous Interaction Grid
- Multiple voices are organized as `LipSyncVoice` nodes under `LipSyncProject`.
- **Preview Screen**: A side-by-side or 2x2 grid preview renders active mouth shapes for all character actors synchronously at the playhead frame.
- **Actor Badges**: Renders overlay labels with character actor name and phoneme state.

### E. DJV Viewer Auto-Detect Image Exporter
- **Sequencing**: Generates zero-padded sequence `<BaseName>_{index:04d}.<ext>`.
- **Companion Audio Pairing**: Copies project audio to `<ExportDir>/<BaseName>.wav`. When opened in DJV Viewer or RV Player, DJV automatically detects and synchronizes the `.wav` file with the image sequence stem.
- **Formats**: PNG, JPEG, APNG, GIF (via `android.graphics.ImageDecoder` and Android GIF encoder).

---

## 3. Technology Stack Matrix

| Subsystem | Technology Choice | Target / Minimum |
|---|---|---|
| **Programming Language** | Kotlin 1.9.23 / Java 17 | 100% Kotlin Coroutines |
| **UI Framework** | Jetpack Compose + Material 3 | Android 9 (API 28) - 14 (API 34) |
| **Audio Engine** | Google Oboe C++ (v1.8.0) | Low-Latency AAudio / OpenSL ES |
| **Local Persistence** | Android Room Database (v2.6.1) | SQLite WAL Mode |
| **Image Processing** | Android Graphics + Glide/Coil | Hardware Bitmaps (Bitmap.Config.HARDWARE) |
| **Export Formats** | MediaMuxer / Custom PNG-APNG | Scoped Storage (Storage Access Framework) |
| **Build System** | Gradle 8.5 + AGP 8.3.0 | GitHub Actions CI Runner |

---
*Developed by Victory Ukpong (2026).*
