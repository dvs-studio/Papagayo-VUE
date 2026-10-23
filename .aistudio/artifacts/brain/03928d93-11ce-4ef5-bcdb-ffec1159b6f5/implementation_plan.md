# Audio Scrubbing, Playhead Restoration, and Runtime Fixes

Repair audio timeline scrubbing, restore the persistent scrubber needle and handle, resolve the regex syntax warning in `WaveformViewRewrite.py`, and eliminate audio playback buffer truncation so complete audio files play smoothly.

> [!IMPORTANT]
> **User Review & Confirmed Decisions**:
> - **Syntax Warning Resolved**: Raw string prefix `r'...'` applied to regex pattern `(border-width: \dpx) \d+px` to eliminate Python 3.12+ syntax warnings.
> - **Persistent Scrubber Needle & Handle**: Restoring a visible, persistent playhead scrubber (vertical marker line + top handle) that remains at the selected frame upon mouse release, synchronizing both the Mouth View shape preview and the frame status counter.
> - **Complete Audio Playback & Preloaded Buffer**: Converting loaded audio to uniform 16-bit PCM in memory with mono downmixing to ensure sounddevice plays the entire track without premature cutoff or channel interleaving issues.
> - **Smooth Scrub Audio Slices**: Scrubbing drag events will play discrete, micro-sliced audio frames (1 frame duration) without locking the UI thread or blocking subsequent mouse moves.

---

## 1. Overview & Core Concept

### What It Does
This update restores standard timeline scrubbing and playback behavior in Papagayo-NG. Users will be able to see the playhead scrubber at all times on the waveform timeline, click or drag anywhere along the timeline to scrub audio and inspect corresponding phoneme mouth shapes in real time, and hear complete, uninterrupted audio playback.

### Target Audience & Persona
Animators, voice actors, and lipsync artists running Papagayo-NG on modern Python environments (Windows/macOS/Linux) who need accurate, responsive audio scrubbing and persistent playhead indicators to align phonemes to speech.

### Key Value
- **Zero Playhead Disappearance**: The playhead needle stays visible at the current frame when stopping or releasing the mouse instead of vanishing.
- **Accurate Audio Playback**: Long and short audio files play to completion without truncating after the first few frames.
- **Responsive Scrubbing**: Instant audio feedback at each frame with mouth preview sync and zero UI stutter.

---

## 2. User Experience & Visual Design

### Key User Flows
1. **Audio & Project Loading**:
   - Loading an audio file (`.wav`, `.mp3`, `.ogg`) or `.pgo` project initializes the timeline with the full duration.
   - The scrubber needle is drawn at frame 0 (or saved start frame) with a clearly visible top drag handle.
2. **Timeline Clicking & Dragging (Scrubbing)**:
   - Clicking anywhere along the waveform or ruler immediately moves the scrubber to that frame.
   - Dragging the scrubber smoothly glides across frames, emits short frame audio slices, and updates the Mouth View shape preview instantly.
   - Releasing the mouse keeps the scrubber positioned on that exact frame and leaves the mouth preview on that frame for inspection.
3. **Playback & Stop**:
   - Pressing Play or Spacebar advances the scrubber needle in lockstep with audio playback across the entire sound file.
   - Pressing Stop halts playback and leaves the scrubber needle positioned at the stopped frame (or resets to beginning if requested).

### Visual Layout & Timeline Needle Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│ Papagayo-NG Studio Window                                              │
├────────────────────────────────────────────────────────────────────────┤
│ [Mouth Preview View]       │ [Voice & Breakdown Hierarchy]             │
│   ┌──────────────────┐     │   Voice 1                                 │
│   │   [ Phoneme O ]  │     │   ├── "Hello" (Frames 1-12)               │
│   └──────────────────┘     │   └── "World" (Frames 14-30)              │
├────────────────────────────────────────────────────────────────────────┤
│ Waveform Timeline & Scrubber View                                      │
│                                                                        │
│ Frames:  0       10      20      30      40      50      60      70    │
│ Ruler:   ├───┼───┼───────┼───────┼───────┼───────┼───────┼───────┤     │
│                     ▼  [Scrubber Top Handle]                           │
│                     │                                                  │
│ Wave:    ~/\~~/\~   │  ~/\~/\~~/\~       ~~/\~/\~                      │
│                     │                                                  │
│ Phrases: [  Phrase 1  │  Phrase 2  ]                                   │
│ Words:   [ Hello  │   World    ]                                       │
│ Phonemes:[E][L][O]│  [W][ER][L][D]                                     │
│                     │                                                  │
│                     ▲  [Persistent Playhead Needle Line]               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Key Product Decisions & Trade-Offs

- **Decision 1: In-Memory Mono PCM Normalization for Playback**:
  - *Chosen Approach*: Convert audio data upon load into a standardized in-memory 16-bit PCM array (mono downmixed).
  - *Why*: Eliminates stereo interleaving bugs where `sounddevice` plays only half the buffer or plays at 2x speed. It also prevents file seeking race conditions between the playback thread and the waveform rendering worker.
  - *Alternatives Considered*: Streaming directly from disk via `wave.open()` was prone to thread collisions during concurrent waveform recalculation.

- **Decision 2: Persistent QGraphicsLineItem / QGraphicsRectItem Scrubber**:
  - *Chosen Approach*: Maintain a dedicated scrubber item with a top indicator handle that is permanently attached to the scene, updating its X position during scrub, playback, and manual clicks without toggling visibility off on mouse release.
  - *Why*: Animators rely on the stationary scrubber needle to judge spacing between adjacent phonemes and mouth shapes.
  - *Alternatives Considered*: Creating and destroying the marker on every click produced Qt object recreation overhead and runtime errors during rapid mouse moves.

- **Decision 3: Non-Blocking Audio Scrub Slices**:
  - *Chosen Approach*: Play a short, fixed 1-frame audio slice (e.g. 40-50ms) using a quick, non-blocking audio task, throttling repeated mouse move triggers to avoid queue saturation.
  - *Why*: Ensures dragging feels lightweight and fluid while still producing the characteristic lipsync scrub audio.

---

## 4. Technical Architecture & Component Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Mouse Interaction                   │
│               (Click / Drag on Waveform Scene)              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 WaveformView (PySide / Qt)                  │
│  - Maps scene coordinates to timeline frame index           │
│  - Positions persistent scrubber needle & top handle        │
│  - Updates MouthView.set_frame(frame)                       │
│  - Requests audio slice: sound.play_segment(time, duration) │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│      SoundPlayer Module      │ │      Mouth View Canvas     │
│  - In-memory PCM buffer      │ │  - Immediate visual        │
│  - Non-blocking audio slice  │ │    phoneme preview update  │
│  - Full duration playback    │ └────────────────────────────┘
└──────────────────────────────┘
```

### State & Handler Modifications
1. **Regex Warning**:
   - `WaveformViewRewrite.py`: Replace non-raw string regex with raw string `r'(border-width: \dpx) \d+px'`.
2. **Scrubber Display & Interaction**:
   - `WaveformViewRewrite.py`:
     - In `__init__`, initialize permanent playhead needle with top scrubber marker.
     - In `mousePressEvent`, immediately update playhead position to clicked frame, update mouth shape, and trigger audio scrub snippet.
     - In `mouseMoveEvent`, update position dynamically while mouse is held down.
     - In `mouseReleaseEvent`, preserve playhead visibility and keep current frame selected (removing the call that hid the marker and reset frame to 0).
3. **Sound Playback Buffer & Duration**:
   - `SoundPlayer.py`:
     - Standardize audio stream channels and sample rate to avoid stereo mono truncation.
     - Ensure `_play` loops through the full track duration using non-blocking audio writes without thread contention.
4. **Verification**:
   - Verify syntax cleanliness, linting, and compile execution via `compile_applet`.
