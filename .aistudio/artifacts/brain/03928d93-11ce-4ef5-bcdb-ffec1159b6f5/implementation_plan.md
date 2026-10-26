# Active Mouth Set Sync, Advanced Image Sequence / Animation Export, & Phoneme Viseme Conversion Kit

Deliver a complete fix for active image set synchronization in the Mouth View, implement an industry-standard DJV-compatible image sequence and animated media export system (`<savename>_0001.<ext>`, PNG, JPG, Animated GIF, APNG), and restore the menu-bar Phoneme Viseme Conversion Kit supporting bidirectional conversion between standard Papagayo (Preston Blair) and Rhubarb/etc.

## User Review & Critical Decisions

> [!IMPORTANT]
> The following specifications reflect confirmed user answers and requirements:
> - **Filename & Indexing**: Uses underscore separation with 4-digit 1-based indexing (`<savename>_0001.<ext>`), fully recognized and sequence-scrubbable in professional viewers like DJV.
> - **Frame Coverage**: Full timeline export rendering every frame (`0` to `total_frames - 1` or `1` to `total_frames`) across the audio duration according to project FPS.
> - **Active Set Authority**: Export strictly obeys the active mouth set selected in the UI dropdown (`mouth_choice`), retrieving images from its registered directory rather than stale global config paths.
> - **Live Mouth Set Sync**: Switching the active mouth set in the dropdown or via the image set button immediately redraws the Mouth View preview without requiring audio playback.
> - **Missing Phoneme Fallback**: Configurable fallback via UI checkbox—either substitute with the `'rest'` shape (default checked) or hold the previous valid phoneme shape.
> - **Media Formats**: Export dialog offers format selection between Image Sequences (PNG, JPG) and Animated Media (Animated GIF, APNG).
> - **Phoneme Viseme Conversion Kit**: Menu-bar conversion action under the *Conversion* menu with bidirectional transformation between standard Papagayo (Preston Blair) visemes and Rhubarb format (and vice versa, as well as CMU_39 and Fleming Dobbs), refreshing the waveform timeline buttons and mouth canvas instantly.

---

## 1. Overview & Core Concept

This milestone addresses three integrated capabilities in Papagayo-NG:

1. **Instant Visual Mouth Set Switching**: Eliminates the caching/redraw lag where switching the active mouth set did not refresh the mouth canvas until playback began.
2. **Standardized Image Sequence & Animation Export Portal**: Replaces the legacy viseme-named leaf export with a frame-accurate, indexed sequence export adhering to industry naming conventions (`savename_0001.png`), plus unified animated GIF and APNG export for animatics and review.
3. **Phoneme Viseme Conversion Kit**: Connects and enhances the Conversion menu bar tool (`action_convert_phonemes`) to convert existing project phoneme keyframes seamlessly between Papagayo Preston Blair and Rhubarb letters (`A-H, X/rest`), allowing users to switch target animation software pipelines without re-transcribing audio.

---

## 2. User Experience & Visual Design

### Key User Flows

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Active Mouth Set Selection & Immediate Preview                      │
│    User changes dropdown "mouth_choice" (e.g., Anime)                  │
│    └─► MouthView immediately repaints canvas to active set at cur frame│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. Menu Bar: Phoneme Viseme Conversion Kit                             │
│    Menu: Conversion ► Convert Phonemes                                 │
│    ├── Prompts Source Set -> Target Set (or syncs with phoneme_set box)│
│    ├── Bidirectional conversion:                                       │
│    │     Preston Blair (AI, E, etc, FV, L, MBP, O, rest, U, WQ)        │
│    │     ◄────────────────────────────────────────────────────►        │
│    │     Rhubarb (A, B, C, D, E, F, G, H, X/rest)                      │
│    └── Instantly updates waveform movable buttons & mouth preview      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. Advanced Export Portal                                              │
│    Dropdown: "Images (Sequence / Animated)" ► Click "Export"           │
│    ├── File Format: [ PNG Sequence (*.png) ]                           │
│    │               [ JPG Sequence (*.jpg) ]                            │
│    │               [ Animated GIF (*.gif) ]                            │
│    │               [ Animated PNG (*.apng) ]                           │
│    ├── Pattern: <savename>_0001.<ext> (DJV-compatible 4-digit index)   │
│    └── [x] Fallback to 'rest' when phoneme is missing                  │
│        (uncheck to hold previous phoneme shape)                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Visual Identity & UI Components
- **Immediate Preview Sync**: When selecting any mouth set from `mouth_choice`, `MouthView.draw_me(force=True)` repaints immediately without awaiting playback events.
- **Phoneme Conversion Feedback**:
  - Menu action `action_convert_phonemes` wired in `LipsyncFrameQT.__init__` with status bar progress and completion notifications (`"Converted 142 phonemes from preston_blair to rhubarb"`).
  - Also exposes an "Open Phoneme Conversion Helper..." action to launch `PhonemeHelper` for visual mapping adjustments.
- **Enhanced Export Modal / Options**:
  - Format selector combo box integrated cleanly with Qt styling.
  - Checkbox for *Fallback to 'rest' mouth shape on missing phoneme* (persisted in user settings).
  - Clear file pattern preview indicator showing an example output filename: `dialogue_0001.png`.

---

## 3. Key Product Decisions & Trade-Offs

### Decision 1: Bidirectional Phoneme Conversion Engine
- **Chosen Approach**: Build a robust, bidirectional conversion map directly supporting:
  - `preston_blair` -> `rhubarb`:
    - `AI -> D`, `E -> C`, `etc -> B`, `FV -> G`, `L -> H`, `MBP -> A`, `O -> E`, `U -> F`, `WQ -> F`, `rest -> rest` (or `X`).
  - `rhubarb` -> `preston_blair`:
    - `A -> MBP`, `B -> etc`, `C -> E`, `D -> AI`, `E -> O`, `F -> WQ`, `G -> FV`, `H -> L`, `X -> rest`, `rest -> rest`.
  - Fallback transit through `CMU_39` if an arbitrary or custom set pair is requested.
- **Why**: Allows animators to take a voice broken down in standard Papagayo and re-target it to Rhubarb 2D rigs (OpenToonz, Moho, Spine, Blender) and vice versa with one click.
- **Alternatives Considered**: Restricting to one-way CMU dictionary breakdown, which would force the user to re-run speech recognition from scratch and lose manual adjustments.

### Decision 2: Directory Registration for All Mouth Sets
- **Chosen Approach**: Enhance `MouthView` to maintain a registry mapping set names directly to their filesystem folder paths (`self.mouth_directories[name] = folder_path`).
- **Why**: Allows both built-in sets (in `rsrc/mouths/<set>`) and custom imported sets (via `choose_imageset_button`) to be addressed seamlessly by name during export.
- **Alternatives Considered**: Relying on `self.config.value("MouthDir")`, which caused stale directory lock-in where custom sets overwrote standard sets globally.

### Decision 3: Frame-by-Frame Resolution vs. Phoneme Leaf Copying
- **Chosen Approach**: For every timeline frame `f` from `0` to `soundDuration - 1`, query `voice.get_phoneme_at_frame(f)`, resolve the corresponding bitmap/file, and output `<prefix>_{frame:04d}.<ext>`.
- **Why**: Industry-standard animation sequences (and players like DJV Viewer) require unbroken sequential frames representing the complete timeline.
- **Alternatives Considered**: Copying only phoneme start frames (original behavior), which caused missing intermediate frames and unplayable sequences in video scrubbers.

### Decision 4: Multi-Format Animated Media Output
- **Chosen Approach**:
  - Image Sequences (PNG, JPG): Written via `QPixmap` / `QImageWriter` or direct stream copy.
  - Animated GIF / APNG: Generated by compositing sequence frames at the exact project FPS. If Pillow is installed, uses Pillow's native multi-frame animated GIF/PNG save routines; if not, falls back to pure-Python GIF / APNG frame chunk assembly.

---

## 4. Technical Architecture & Implementation Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Application UI                                 │
│  ┌───────────────────────┐             ┌──────────────────────────────────┐ │
│  │ mouth_choice Dropdown │             │ Export Dialog & Format Options   │ │
│  └───────────┬───────────┘             └────────────────┬─────────────────┘ │
│              │                                          │                   │
│              │             ┌──────────────────────────┐ │                   │
│              │             │ Menu: Conversion Action  │ │                   │
│              │             └─────────────┬────────────┘ │                   │
└──────────────┼───────────────────────────┼──────────────┼───────────────────┘
               │ on_mouth_choice           │ on_convert   │ on_voice_export
               ▼                           ▼              ▼
┌──────────────────────────────────┐ ┌───────────────────┐ ┌─────────────────┐
│           MouthView              │ │  Phoneme Converter│ │ export_images   │
│ ├── mouth_directories map        │ │ ├── Preston Blair │ │ ├── Frame loop  │
│ ├── Force-refresh draw_me()      │ │ ├── Rhubarb <-> PB│ │ ├── DJV index   │
│ └── Immediate preview sync       │ │ ├── CMU transit   │ │ └── PNG/JPG/GIF │
└──────────────────────────────────┘ └───────────────────┘ └─────────────────┘
```

### Affected Files & Modifications
1. **`MouthViewQT.py`**:
   - Store `self.mouth_directories[set_name] = directory_path` during `add_mouth` and `load_mouths`.
   - Update `draw_me()` to detect `current_mouth` changes and always force scene repainting even if `self.current_phoneme` hasn't changed.
   - Add helper `get_mouth_directory(set_name)` returning the exact disk path.
2. **`LipsyncDoc.py`**:
   - Refactor `export_images(self, path, currentmouth, format_choice, fallback_to_rest)`:
     - Locate mouth directory from active mouth set.
     - Iterate through timeline frames `0` to `self.soundDuration - 1`.
     - Resolve image file for each frame using active set + fallback rule (rest shape vs previous phoneme hold).
     - Save as `<path>_{index:04d}.<ext>` for sequences, or compile frames into single animated file for GIF/APNG.
   - Upgrade `convert_to_phonemeset(self, target_set=None)`:
     - Support explicit bidirectional conversion between Preston Blair and Rhubarb (and other sets).
     - Update all phoneme text tokens in document hierarchy.
     - Refresh waveform buttons and update document dirty state.
3. **`LipsyncFrameQT.py`**:
   - Connect `action_convert_phonemes` directly in `__init__` to `on_convert_phonemes()`.
   - Provide a clean conversion prompt or target selection dropdown if triggered from the menu bar.
   - Connect `mouth_choice.currentIndexChanged` to immediately update `mouth_view.current_mouth` and redraw canvas.
   - In `on_voice_image_choose`: after scanning the custom directory, immediately select it in `mouth_choice` and force redraw.
   - Expand `on_voice_export` with format filter choices (PNG Sequence, JPG Sequence, Animated GIF, Animated PNG) and save settings.
4. **`requirements-desktop.txt`**:
   - Ensure `Pillow>=9.0.0` is present for native animated GIF/APNG rendering.
