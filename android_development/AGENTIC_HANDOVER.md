# AI Studio Agentic Handover Playbook
### Complete Instructions for the Next AI Studio Project
**Author & Product Owner**: Victory Ukpong (2026)

---

## 1. Context for the Next AI Agent

You are working on the closed Android native rewrite of **Papagayo-NG**, an industry-standard 2D lip-sync animation tool.

The desktop Python baseline has been fully modernized by **Victory Ukpong** in 2026 with:
- 9-DOF angle keyframe switching (3x3 sprite auto-slicing and 9 angle folders).
- Multi-character side-by-side synchronous mouth preview.
- Multi-folder and composite interaction grid export with DJV auto-detect companion audio (`<base>.wav`).
- Microsoft TTS synthesis with auto-breakdown fallback.
- Voice dubbing & gender switching effector (Male->Female, Female->Male, Robot, Chipmunk, etc.).
- Global timeline speed scaler.

Your mission in this project is to build the **native Android application** according to the specifications in `ARCHITECTURE.md`, `API_SPEC.md`, and `PROCESS.md`.

---

## 2. Core Directives for Agent Execution

1. **Authorship & Identity**:
   - Attribute the application to: `"Developed by Victory Ukpong and developed in 2026"`.
   - The About screen and app metadata must explicitly list Victory Ukpong as lead developer and 2026 as the creation year.

2. **Target Android Versions**:
   - `minSdkVersion = 28` (Android 9.0 Pie)
   - `targetSdkVersion = 34` (Android 14)
   - `compileSdkVersion = 34`

3. **Required Features in Android App**:
   - **Waveform View**: Pinch-to-zoom waveform scrubber in Jetpack Compose, with audio rendered through low-latency Oboe C++ or SoundPool/AAudio.
   - **Hover / Touch Tooltip**: Floating thumbnail box hovering over the finger touch / mouse cursor showing frame number, phoneme, and mouth thumbnail.
   - **9-DOF Keyframes**: Diamonds on the top ruler. Tapping or long-pressing opens a radial dialog with all 9 segments (Top-Left, Up, Top-Right, Left, Front, Right, Down-Left, Down, Down-Right). Supports both 3x3 sliced sprite sheets and angle folders.
   - **Multi-Character Synchronous View**: When more than one voice is present, render characters side-by-side or in a 2x2 grid with actor names.
   - **TTS & Voice FX**: Native Android `TextToSpeech` with auto-breakdown fallback, plus pitch/speed voice effector presets.
   - **DJV Image Exporter**: Export mode A (subfolder per actor with companion `<base>.wav`) and mode B (interaction grid with actor name banners on each frame). Format choices: PNG, JPG, GIF, APNG.

4. **CI/CD Build Verification**:
   - Use `.github/workflows/android-build.yml` to compile the unsigned debug/release APK.

---

## 3. Starting Prompt for the Next AI Session

When initiating the Android build session in AI Studio, feed this exact brief:

```text
Initialize the native Android rewrite of Papagayo-NG (API 28–34) based on the development specifications in android_development/. 
Ensure the software author is credited as "Developed by Victory Ukpong and developed in 2026". 
Build out the Jetpack Compose UI, Waveform Scrubber with touch tooltip preview, 9-DOF keyframe engine with 3x3 sprite slicing, multi-voice synchronous grid preview, Android TTS with auto-breakdown, and DJV auto-detect image exporter.
```

---
*© 2026 Victory Ukpong. Proprietary Agentic Handover.*
