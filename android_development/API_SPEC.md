# Papagayo-NG Android Data Specifications & API Contracts
**Author**: Victory Ukpong (2026)

---

## 1. Project Data Model (JSON / Room Schema)

The core lip-sync project structure serializes to `.pg2` (JSON format) and stores locally in Room:

```json
{
  "project_version": "2.0.0-android",
  "name": "Dialogue Scene 1",
  "fps": 24,
  "sound_duration_frames": 96,
  "sound_duration_seconds": 4.0,
  "sound_filename": "dialogue_clean.wav",
  "active_mouth_set": "4 - Preston Blair",
  "active_phoneme_set": "preston_blair",
  "dof_settings": {
    "mode": "SPRITE_3X3",
    "sprite_sheet_path": "character_angles_3x3.png",
    "keyframes": [
      { "frame": 0, "angle_id": 5, "label": "Front View" },
      { "frame": 24, "angle_id": 6, "label": "3/4 Right" },
      { "frame": 48, "angle_id": 4, "label": "3/4 Left" },
      { "frame": 72, "angle_id": 5, "label": "Front View" }
    ],
    "segment_names": {
      "1": "Top-Left",
      "2": "Up",
      "3": "Top-Right",
      "4": "3/4 Left",
      "5": "Front",
      "6": "3/4 Right",
      "7": "Down-Left",
      "8": "Down",
      "9": "Down-Right"
    }
  },
  "voices": [
    {
      "id": "v1",
      "name": "Actor 1 (Narrator)",
      "text": "Hello, welcome to Papagayo-NG.",
      "phrases": [
        {
          "text": "Hello, welcome to Papagayo-NG.",
          "start_frame": 1,
          "end_frame": 72,
          "words": [
            {
              "text": "Hello",
              "start_frame": 1,
              "end_frame": 18,
              "phonemes": [
                { "phoneme": "etc", "start_frame": 1, "end_frame": 1 },
                { "phoneme": "E", "start_frame": 6, "end_frame": 6 },
                { "phoneme": "L", "start_frame": 11, "end_frame": 11 },
                { "phoneme": "O", "start_frame": 14, "end_frame": 14 }
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "v2",
      "name": "Actor 2 (Hero)",
      "text": "Thanks! Ready for animation.",
      "phrases": [
        {
          "text": "Thanks! Ready for animation.",
          "start_frame": 40,
          "end_frame": 96,
          "words": []
        }
      ]
    }
  ]
}
```

---

## 2. 9-DOF Grid Viewport Mapping

The 3x3 layout follows the standard 9 camera perspectives:

```
┌──────────────┬──────────────┬──────────────┐
│  Index 1     │  Index 2     │  Index 3     │
│  Top-Left    │  Up          │  Top-Right   │
├──────────────┼──────────────┼──────────────┤
│  Index 4     │  Index 5     │  Index 6     │
│  3/4 Left    │  Front       │  3/4 Right   │
├──────────────┼──────────────┼──────────────┤
│  Index 7     │  Index 8     │  Index 9     │
│  Down-Left   │  Down        │  Down-Right  │
└──────────────┴──────────────┴──────────────┘
```

Coordinate calculation for 3x3 sprite slice of width $W$ and height $H$:
$$cell\_w = \lfloor W / 3 \rfloor, \quad cell\_h = \lfloor H / 3 \rfloor$$
For Index $k \in [1, 9]$:
$$row = \lfloor (k - 1) / 3 \rfloor, \quad col = (k - 1) \pmod 3$$
$$Box = (col \times cell\_w, row \times cell\_h, (col+1) \times cell\_w, (row+1) \times cell\_h)$$

---

## 3. DJV Viewer Auto-Detection Contract

To ensure image sequences are immediately playable with synced audio in DJV Viewer and professional review software:

1. **Folder Layout (Mode A - Per Character Actor)**:
   ```
   <ExportRoot>/
   └── <Actor_Name>/
       ├── <BaseName>_0001.png
       ├── <BaseName>_0002.png
       ├── ...
       ├── <BaseName>_0096.png
       └── <BaseName>.wav      <-- Companion audio with matching stem!
   ```
   When the folder `<Actor_Name>` is opened in DJV, DJV detects `<BaseName>.wav` matching `<BaseName>_####.png` and automatically attaches the audio track.

2. **Folder Layout (Mode B - Composite Interaction Grid)**:
   ```
   <ExportRoot>/
   ├── grid_<BaseName>_0001.png
   ├── grid_<BaseName>_0002.png
   ├── ...
   ├── grid_<BaseName>_0096.png
   └── grid_<BaseName>.wav     <-- Companion audio
   ```
   Each composite frame renders a side-by-side or 2x2 grid with actor names visibly labeled on the frames.

---
*© 2026 Victory Ukpong. Proprietary Android Specification.*
