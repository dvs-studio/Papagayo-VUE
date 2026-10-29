# Papagayo-NG Android Development Kit (API 28–34)
### Closed Rewrite Baseline & Engineering Handover
**Lead Developer & Architect**: Victory Ukpong (2026)  
**Target Platform**: Android 9 (Pie, API 28) through Android 14 (Upside Down Cake, API 34)  
**Distribution**: Proprietary Closed-Source Rewrite  

---

## 1. Executive Summary

This development package contains the full engineering specifications, architecture blueprints, data interchange schemas, agentic handover workflows, and automated CI/CD pipeline for the upcoming native Android rewrite of **Papagayo-NG**.

Designed by Victory Ukpong, this rewrite transitions Papagayo-NG from a desktop Python/PySide application into an ultra-responsive, touch-optimized mobile studio for 2D character animators, story artists, and voice actors.

---

## 2. Core Capabilities to Port

1. **Audio Decoding & Real-Time Waveform Scrubbing**:
   - High-precision waveform display with sub-frame pinch-to-zoom and multi-touch scrubbing.
   - Low-latency audio playback utilizing Android C++ Oboe / AAudio.
   - Touch scrubber with floating tooltip showing current frame, phoneme viseme, and 9-DOF angle thumbnail.

2. **9-DOF (Degrees of Freedom) Keyframe Engine**:
   - Timeline keyframe track for head rotation and camera angle switching.
   - Mode 1: Multi-folder angle switching (9 angle asset folders).
   - Mode 2: 3x3 Sprite Sheet slicing (Auto-slicing a single 3x3 sprite image into 9 viewports: Top-Left, Up, Top-Right, Left, Center/Front, Right, Down-Left, Down, Down-Right).
   - Long-press / context radial selector on waveform ruler to pick angle (1–9), name angles, and edit keyframes.

3. **Multi-Character Synchronous Interaction**:
   - Multi-voice project support with synchronous split-screen / interaction grid mouth shape preview.
   - Per-Voice actor tracks with individual dialogue transcripts and phoneme timings.

4. **Speech Synthesis & Voice Effector (DSP)**:
   - Android Text-To-Speech (`android.speech.tts.TextToSpeech`) integration with auto-phonetic breakdown fallback when no text is provided.
   - Voice transformation effector: Pitch shift (semitones) and speed multiplier presets (Male to Female, Female to Male, Robot, Deep Narrator, Cartoon Chipmunk, Child).
   - Global lip-sync speed scaler (0.25x to 3.0x).

5. **Production Image Sequence & DJV Exporter**:
   - Option A: Isolated subfolder per character actor (`<ExportDir>/<ActorName>/<base>_{index:04d}.<ext>`), paired with companion `<base>.wav` for automatic DJV Viewer timeline binding.
   - Option B: Composite interaction grid frames with actor name labels burnt into each frame.
   - Support for PNG sequence, JPEG sequence, Animated GIF, and APNG formats.
   - Phoneme viseme converter (Preston Blair ↔ Rhubarb ↔ Fleming Dobbs ↔ CMU-39).

---

## 3. Directory Layout

```
android_development/
├── README.md                  # This master introduction and overview
├── ARCHITECTURE.md            # Modern Android architecture (Jetpack Compose, Oboe, Room)
├── API_SPEC.md                # Data schemas, serialization, and DJV auto-detect protocol
├── PROCESS.md                 # Phased engineering roadmap and QA testing matrices
├── AGENTIC_HANDOVER.md        # Comprehensive AI Studio agent handover instructions
└── .github/
    └── workflows/
        └── android-build.yml  # GitHub Actions workflow for compiling unsigned APK
```

---

## 4. Building the Development APK

The included GitHub Actions workflow (`.github/workflows/android-build.yml`) compiles an unsigned APK supporting Android 9 (API 28) through Android 14 (API 34) using:
- **Gradle 8.5**
- **Android Gradle Plugin (AGP) 8.3**
- **JDK 17 (Temurin)**
- **NDK 26.1.10909125** (for high-performance audio engine)

To trigger a build:
1. Push this folder to a GitHub repository.
2. The GitHub Action will automatically configure the Android SDK, build the debug/release unsigned APK, and upload the APK as a downloadable GitHub Actions artifact.

---
*© 2026 Victory Ukpong. All Rights Reserved. Proprietary & Confidential Closed Rewrite.*
