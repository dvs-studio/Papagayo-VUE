# Papagayo-NG: API Kit & Developer Reference

This document provides a comprehensive technical reference for all public interfaces in **Papagayo-NG**, spanning CLI automation, Python library APIs, audio processing hooks, and the Web Studio HTTP REST service.

---

## 1. Command Line Interface (CLI)

Papagayo-NG supports fully headless CLI execution for batch lip-sync generation, project conversion, and automated animation pipelines.

### 1.1 Invocation Syntax

```bash
python3 papagayo-ng.py --cli -i <input_path> -o <output_path> [options]
```

### 1.2 CLI Flags Reference

| Flag | Long Form | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-i` | `--input` | string | *Required* | Path to the input `.pgo`, `.pg2`, or audio file (`.wav`, `.mp3`). |
| `-o` | `--output` | string | *Required* | Path to the destination export file or output directory. |
| `--cli` | | flag | `false` | Run in headless command-line mode without opening the Qt GUI window. |
| | `--output-type` | string | `moho` | Export format. Options: `moho` (`.dat`), `json`, `alelo` (`.txt`), `images` (frame sequence). |
| | `--voice` | string | `None` | Name of the voice track to export. If omitted, exports all voices or the first active voice. |
| | `--mouths` | string | `Preston Blair` | Name of mouth set folder in `rsrc/mouths/` (e.g. `Preston Blair`, `Rhubarb`, `Hunanbean CMU39`). Used when exporting images. |
| | `--fps` | integer | `24` | Animation frame rate (frames per second). |
| | `--lang` | string | `en_US` | Language dictionary code for phoneme breakdown (e.g. `en_US`, `es_ES`, `de_DE`). |
| `-v` | `--verbose` | flag | `false` | Enable verbose diagnostic logging. |

### 1.3 CLI Usage Examples

#### Export a .pgo project to Moho Switch Layer (.dat)
```bash
python3 papagayo-ng.py --cli -i project.pgo -o output_voice.dat --output-type moho
```

#### Export to Structured Animation JSON
```bash
python3 papagayo-ng.py --cli -i project.pgo -o animation_timeline.json --output-type json
```

#### Export to Rendered Frame-by-Frame Mouth PNGs
```bash
python3 papagayo-ng.py --cli -i project.pgo -o dist/frames/ --output-type images --mouths "Preston Blair" --fps 24
```

---

## 2. Python Core Library API

Developers and scripts can import Papagayo-NG's core modules directly into Python workflows.

### 2.1 `LipsyncDoc` (`LipsyncDoc.py`)

The root document class managing project state, audio synchronization, and voice tracks.

```python
from LipsyncDoc import LipsyncDoc

# Initialize empty document
doc = LipsyncDoc()

# Load a project file (.pgo or .pg2)
doc.open("path/to/project.pgo")

# Access document properties
print(f"Audio Path: {doc.soundPath}")
print(f"Framerate: {doc.fps} FPS")
print(f"Total Frames: {doc.duration_frames}")

# Access voices
for voice_name, voice in doc.voices.items():
    print(f"Voice: {voice_name}, Phrases: {len(voice.phrases)}")

# Add a new voice track
new_voice = doc.add_voice("Narrator")

# Save document back to disk
doc.save("path/to/updated_project.pgo")
```

#### Key Methods & Attributes

- `doc.open(filepath: str) -> bool`: Parses `.pgo` or `.pg2` project file. Automatically resolves audio path relative to the project directory if the original absolute path is missing.
- `doc.save(filepath: str) -> bool`: Serializes project to disk.
- `doc.load_audio(audio_path: str) -> bool`: Loads and binds audio file to the project.
- `doc.add_voice(name: str) -> LipsyncVoice`: Creates and registers a new voice track.
- `doc.delete_voice(name: str)`: Removes specified voice track.
- `doc.voices: dict[str, LipsyncVoice]`: Mapping of voice names to voice track instances.
- `doc.fps: int`: Frame rate (default: 24).
- `doc.soundPath: str`: Absolute or relative path to the bound audio file.
- `doc.sound: SoundPlayer`: SoundPlayer instance representing loaded audio.

---

### 2.2 `LipsyncVoice` (`LipsyncDoc.py`)

Represents a voice track containing spoken phrases, word intervals, and phoneme keyframes.

```python
voice = doc.voices["Narrator"]

# Set dialogue text and parse phonemes
voice.parse_text("Hello world, this is Papagayo.", language="en_US")

# Export to Moho switch format
voice.export("narrator_moho.dat")

# Export to JSON
voice.export_json("narrator.json")

# Export to Alelo format
voice.export_alelo("narrator_alelo.txt", language="en_US")

# Export frame-by-frame mouth images
voice.export_images(output_dir="renders/", prefix="mouth_", mouth_set="Preston Blair")
```

#### Key Methods & Attributes

- `voice.name: str`: Display name of the voice track.
- `voice.phrases: list[Phrase]`: Ordered list of spoken dialogue phrases.
- `voice.current_mouth: str`: Active mouth artwork set name.
- `voice.export(filepath: str)`: Exports Moho / Anime Studio `.dat` switch keyframes.
- `voice.export_json(filepath: str)`: Exports JSON structured keyframe dictionary:
  ```json
  {
    "voice": "Narrator",
    "fps": 24,
    "frames": [
      {"frame": 1, "phoneme": "etc"},
      {"frame": 5, "phoneme": "AI"},
      {"frame": 12, "phoneme": "rest"}
    ]
  }
  ```
- `voice.export_images(output_dir: str, prefix: str, mouth_set: str)`: Copies or generates mouth image sequences named `<prefix><frame_number>.png`.

---

### 2.3 `SoundPlayer` (`SoundPlayer.py`)

Handles audio playback, sample decoding, and amplitude analysis for waveform visualization.

```python
from SoundPlayer import SoundPlayer

player = SoundPlayer()

# Load audio file (.wav, .mp3, etc.)
success = player.LoadSound("speech.wav")
if success:
    # Get audio duration
    seconds = player.GetLength()
    
    # Calculate RMS amplitude for frame range (samples)
    rms = player.GetRMSAmplitude(startframe=0, endframe=1024)
    
    # Extract complete waveform envelope for UI display (e.g. 500 buckets)
    amplitudes = player.GetWaveformAmplitudes(num_buckets=500)
    
    # Playback controls
    player.Play()
    player.Stop()
```

#### Key Methods

- `player.LoadSound(path: str) -> bool`: Robust audio loader supporting standard `wave`, `pydub.AudioSegment`, or headless dummy audio when no sound drivers exist.
- `player.GetRMSAmplitude(startframe: int, endframe: int) -> float`: Returns the root-mean-square amplitude for a slice of audio samples. Includes pure-Python math fallback.
- `player.GetWaveformAmplitudes(num_buckets: int) -> list[float]`: Returns normalized (0.0 to 1.0) amplitude peaks suitable for canvas or visualizer rendering.
- `player.Play()`, `player.Stop()`, `player.Pause()`: Audio transport control.
- `player.GetPosition() -> float`: Current playback position in seconds.
- `player.SetPosition(seconds: float)`: Seek to position.

---

### 2.4 `qt_compat` (`qt_compat.py`)

Cross-version Qt bridging layer ensuring compatibility across PySide6, PySide2, and headless environments.

```python
from qt_compat import (
    QtCore, QtGui, QtWidgets,
    QWidget, QApplication, QIcon, QPixmap,
    exec_app, is_headless
)

# Safe event loop start regardless of Qt version
app = QApplication([])
# ... build UI ...
# exec_app handles app.exec() in Qt6 and app.exec_() in Qt5
exec_app(app)
```

---

## 3. Web Studio HTTP REST API (Port 3000)

The dev server (`app.py` / `main.py`) exposes an HTTP REST API for automated testing, external control, and browser-based diagnostics.

### 3.1 `GET /api/status`
Returns application health, environment diagnostics, and subsystem states.

**Response `200 OK`**:
```json
{
  "status": "online",
  "app": "Papagayo-NG Web Studio",
  "python_version": "3.12.0",
  "port": 3000,
  "qt_available": false,
  "sound_engine": "standard_wave_rms",
  "breakdown_languages": ["en_US", "es_ES", "de_DE", "fr_FR"],
  "mouth_sets": ["Preston Blair", "Rhubarb", "Gary C Martin", "Hunanbean CMU39"]
}
```

---

### 3.2 `GET /api/test-file`
Generates an in-memory 1-second 440Hz test sine WAV file and a synchronized `.pgo` project, verifies their parsing end-to-end, and returns the parsed verification metadata.

**Response `200 OK`**:
```json
{
  "test_passed": true,
  "project": {
    "fps": 24,
    "voices": 1,
    "phrases": 1,
    "words": 2,
    "phonemes": 8
  },
  "audio": {
    "channels": 1,
    "sample_rate": 44100,
    "duration_seconds": 1.0
  }
}
```

---

### 3.3 `POST /api/verify`
Upload a `.pgo`, `.pg2`, or audio file to inspect its structure without launching the desktop UI.

- **Content-Type**: `multipart/form-data`
- **Payload**: `file` (binary file)

**Response `200 OK`**:
```json
{
  "valid": true,
  "filename": "dialogue_scene1.pgo",
  "type": "pgo_project",
  "fps": 24,
  "audio_file_referenced": "dialogue_scene1.wav",
  "audio_found_on_disk": true,
  "voice_count": 2,
  "voices": [
    {
      "name": "CharacterA",
      "phrase_count": 3,
      "phoneme_count": 42
    }
  ]
}
```

---

### 3.4 `POST /api/cli`
Execute headless CLI export commands via REST API.

- **Content-Type**: `application/json`
- **Payload**:
  ```json
  {
    "input_path": "examples/scene1.pgo",
    "output_path": "exports/scene1.dat",
    "output_type": "moho",
    "fps": 24
  }
  ```

**Response `200 OK`**:
```json
{
  "success": true,
  "exit_code": 0,
  "output_file": "exports/scene1.dat",
  "bytes_written": 1420
}
```
