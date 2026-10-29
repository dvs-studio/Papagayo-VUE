# Engineering Process, Roadmap & Verification Matrix
### Papagayo-NG Closed Android Rewrite
**Lead Engineer**: Victory Ukpong (2026)

---

## 1. Phased Development Roadmap

### Phase 1: Foundation & Audio Pipeline (Weeks 1–3)
- Initialize Android Gradle project targeting `minSdk 28`, `targetSdk 34`.
- Integrate Google Oboe via CMake/NDK for ultra-low latency audio playback.
- Implement WAV / MP3 / M4A decoder via Android `MediaExtractor` + `MediaCodec`.
- Build custom high-speed RMS waveform peak generator (100 samples/sec).
- *Milestone*: Flawless audio playback and real-time waveform scrub under 15ms latency on Android 9–14 test devices.

### Phase 2: Jetpack Compose Timeline & Multi-Voice Engine (Weeks 4–6)
- Develop `WaveformScrubber` Compose component with pinch-to-zoom (1x to 10x).
- Implement floating hover tooltip box over touch cursor showing frame number, phoneme badge, and mouth thumbnail.
- Build multi-character data layer in Room DB: multiple voice tracks, phrase/word/phoneme tree.
- Implement breakdown alignment parser with CMU Pronouncing dictionary and phonetic rule tables.
- *Milestone*: Multi-voice timeline scrubbing with live synchronous character mouth shape previews.

### Phase 3: 9-DOF Keyframe Angle Engine (Weeks 7–8)
- Implement `DofKeyframe` timeline track with diamond markers.
- Implement 3x3 sprite auto-slicer and angle folder loader with LRU bitmap cache.
- Implement radial touch menu for selecting angles 1 through 9.
- Implement angle renaming and timeline marker synchronization.
- *Milestone*: Real-time angle switching during audio playback with zero frame drops (solid 60 FPS).

### Phase 4: Voice Effector & TTS Engine (Weeks 9–10)
- Integrate Android `TextToSpeech` with auto-breakdown fallback if no context was entered.
- Build pure Kotlin DSP pitch shifting and speed scaling engine:
  - Presets: Male to Female, Female to Male, Robot, Deep Narrator, Cartoon Chipmunk, Child.
  - Global lip-sync speed scaler (0.25x to 3.0x).
- *Milestone*: Instant vocal transformations and automatic phoneme breakdown generation.

### Phase 5: Production Exporters & DJV Validation (Weeks 11–12)
- Implement Mode A (Per-Voice subfolders with companion `<base>.wav` for DJV auto-detect).
- Implement Mode B (Composite interaction grid frames with actor name labels).
- Image sequence writers: PNG, JPEG, APNG, GIF.
- Phoneme conversion kit: Preston Blair ↔ Rhubarb ↔ Fleming Dobbs ↔ CMU-39.
- *Milestone*: Exported folders open in DJV viewer with auto-bound audio and perfect frame-to-mouth synchronization.

---

## 2. Testing & Quality Assurance Protocol

1. **Audio Latency Benchmark**:
   - Device: Google Pixel / Samsung Galaxy (Android 9 through 14).
   - Metric: Touch-to-audio latency < 20ms; audio buffer underruns (xruns) = 0.

2. **Memory & Sprite Cache Stress Test**:
   - 10-minute scrub with 4 character actors and high-resolution 3x3 sprite sheets.
   - Max memory consumption < 180MB; no OutOfMemoryErrors; garbage collection pauses < 5ms.

3. **DJV Compatibility Suite**:
   - Verification that sequences exported with companion `.wav` files bind automatically upon directory drag-and-drop in DJV Viewer v2.0+.

---
*Developed by Victory Ukpong (2026).*
