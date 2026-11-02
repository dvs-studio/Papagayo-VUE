========================================================================
 PAPAGAYO-VUE (2026) - QUICK START & TUTORIAL SAMPLES
 Redeveloped by Victory Ukpong (2026)
========================================================================

Welcome to Papagayo-VUE! This tutorial package is designed to help you
get up and running immediately with lip-sync animation.

INCLUDED TUTORIAL FILES:
1. sample_voice.wav
   A clean 16-bit 44.1kHz audio sample ready to use for lip-sync testing.

2. tutorial_basic_lipsync.pgo
   A single-character project demonstrating word breakdowns, phoneme
   placement, and 9-DOF keyframing ("Welcome to Studio").

3. tutorial_multi_character.pgo
   A dual-character project (Character A and Character B) showing how to
   use the Side-by-Side Split and 2x2 Grid Preview Layouts.

========================================================================
HOW TO USE:
========================================================================
Step 1: Launch Papagayo-VUE
  - Standard GUI: Double-click Papagayo-VUE.exe
  - With Diagnostic Console: Double-click run_papagayo_debug.bat or
    Papagayo-VUE_debug.exe to view live command-line logs and tracebacks.

Step 2: Open a Tutorial Project
  - In the top menu, click File -> Open Project (Ctrl+O).
  - Navigate to this 'samples' folder and select 'tutorial_basic_lipsync.pgo'.
  - You will see the waveform, dialogue text, and phonemes mapped out.

Step 3: Play & Scrub Audio
  - Press the Spacebar or click the Play button to listen.
  - Drag the timeline scrubber with your mouse to inspect mouth visemes
    frame-by-frame.

Step 4: Switch Preview Layout & Mouth Sets
  - Click the new 'Preview' menu in the top menubar.
  - Try 'Single View', 'Side-by-Side Split View', or '2x2 Grid View'.
  - Under 'Preview' -> 'Switch Viseme Mouth Set', choose between:
      * 4 - Preston Blair (classic cartoon)
      * 9 - Hunanbean (39 CMU photorealistic / anime)
      * 3 - Gary C Martin
      * 8 - Rhubarb (standard 9-phoneme set)
  - You can also right-click anywhere in the mouth preview window to switch!

Step 5: Experiment with the Voice Effector
  - Click the 'Voice Effector' button in the toolbar.
  - Choose presets like 'Male to Female', 'Robot / Vocoder', 'Deep Narrator',
    or adjust pitch semitones and speed multiplier.
  - Click OK to apply. Works with both imported audio and TTS files!

Step 6: Export Your Animation
  - In the Export dropdown (bottom-right), choose your target format:
      * Moho / Anime Studio (.dat)
      * JSON Keyframes (for Blender, Unity, or Unreal)
      * Rendered PNG Image Sequence (for DJV viewer or video compositing)
  - Click 'Export' and save to your project folder.

Have fun animating with Papagayo-VUE!
Redeveloped by Victory Ukpong (2026).
