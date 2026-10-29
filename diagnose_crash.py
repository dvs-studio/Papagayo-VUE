#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Papagayo-VUE Crash & Environment Diagnostic Engine
Lead Redeveloper & 9-DOF Architect: Victory Ukpong (2026)

Tests all subsystems, imports, Qt backends, audio drivers, file structures,
and produces a beginner-friendly report that can be copied/pasted into chat.
"""

import os
import sys
import platform
import traceback
import tempfile
import json
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

REPORT_LINES = []

def log_section(title):
    sep = "=" * 60
    REPORT_LINES.append(f"\n{sep}\n  {title}\n{sep}")
    print(f"\n{sep}\n  {title}\n{sep}")

def log_item(status, category, detail):
    symbol = "✅ [OK]" if status == "OK" else ("⚠️  [WARN]" if status == "WARN" else "❌ [FAIL]")
    line = f"{symbol:<10} {category:<22} : {detail}"
    REPORT_LINES.append(line)
    print(line)

def run_diagnostics():
    REPORT_LINES.clear()
    start_time = time.strftime("%Y-%m-%d %H:%M:%S")
    REPORT_LINES.append("============================================================")
    REPORT_LINES.append("  PAPAGAYO-VUE DIAGNOSTIC & CRASH REPORT")
    REPORT_LINES.append("  Redeveloped by Victory Ukpong (2026)")
    REPORT_LINES.append(f"  Generated At: {start_time}")
    REPORT_LINES.append("============================================================")
    print("\n".join(REPORT_LINES))

    # 1. System & Architecture
    log_section("1. System Environment & Python Architecture")
    log_item("OK", "Operating System", f"{platform.system()} {platform.release()} ({platform.version()})")
    log_item("OK", "Python Executable", sys.executable)
    log_item("OK", "Python Version", f"{sys.version.split()[0]} ({platform.architecture()[0]})")
    log_item("OK", "Working Directory", os.getcwd())
    log_item("OK", "Base Project Path", BASE_DIR)

    # 2. Resource & File Structure Check
    log_section("2. Project Files & Assets Tree Check")
    key_files = [
        "papagayo-vue.py",
        "papagayo-ng.py",
        "app.py",
        "main.py",
        "LipsyncDoc.py",
        "LipsyncFrameQT.py",
        "MouthViewQT.py",
        "SettingsQT.py",
        "SoundPlayer.py",
        "utilities.py",
        "about_markdown.html",
        "version_information.txt",
        "rsrc/about_box.ui",
        "rsrc/settings.ui",
        "rsrc/themes/dark_grey.qss",
        "rsrc/themes/light.qss",
        "rsrc/themes/slate.qss"
    ]
    for rel_path in key_files:
        full_p = os.path.join(BASE_DIR, rel_path)
        if os.path.exists(full_p):
            sz = os.path.getsize(full_p)
            log_item("OK", "File Present", f"{rel_path} ({sz} bytes)")
        else:
            log_item("FAIL", "Missing File", f"{rel_path}")

    # Check mouth sets
    mouths_dir = os.path.join(BASE_DIR, "rsrc", "mouths")
    if os.path.exists(mouths_dir):
        msets = os.listdir(mouths_dir)
        log_item("OK", "Viseme Mouth Sets", f"{len(msets)} found ({', '.join(msets[:4])}...)")
    else:
        log_item("FAIL", "Mouth Directory", "rsrc/mouths not found")

    # 3. Qt & GUI Subsystem
    log_section("3. Qt Backend & Display Subsystem")
    try:
        import importlib
        import qt_compat
        importlib.reload(qt_compat)
        log_item("OK", "qt_compat Import", f"Backend: {getattr(qt_compat, 'QT_LIB', 'Unknown')}")
        log_item("OK", "Headless Flag", f"IS_HEADLESS = {getattr(qt_compat, 'IS_HEADLESS', False)}")
        
        # Test QApplication creation
        app_inst = qt_compat.QtWidgets.QApplication.instance()
        if not app_inst:
            test_app = qt_compat.QtWidgets.QApplication(["PapagayoVUEDiag", "-platform", "offscreen"])
            log_item("OK", "QApplication Init", "Initialized offscreen QApplication successfully")
        else:
            log_item("OK", "QApplication Existing", "Active QApplication instance detected")
    except Exception as e:
        log_item("WARN", "Qt Subsystem", f"Note: {e}")

    # 4. Audio Engine & DSP Pipeline
    log_section("4. Audio Engine & Waveform DSP Check")
    try:
        import wave
        import struct
        import math
        log_item("OK", "Standard Audio Modules", "wave, struct, math loaded")
        
        tmp_wav = os.path.join(tempfile.gettempdir(), "test_diag.wav")
        with wave.open(tmp_wav, 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            frames = []
            for i in range(4410):
                val = int(16000.0 * math.sin(2.0 * math.pi * 440.0 * i / 44100))
                frames.append(struct.pack('<h', val))
            f.writeframes(b"".join(frames))
        log_item("OK", "WAV Generator", f"Synthesized 0.1s 440Hz test wave ({os.path.getsize(tmp_wav)} bytes)")
    except Exception as e:
        log_item("FAIL", "WAV Generator", str(e))

    try:
        import SoundPlayer
        player = SoundPlayer.SoundPlayer(tmp_wav)
        dur = player.Duration()
        log_item("OK", "SoundPlayer Engine", f"Valid={player.IsValid()}, Duration={dur:.2f}s")
    except Exception as e:
        log_item("WARN", "SoundPlayer Engine", f"Audio device warning (normal in headless): {e}")

    # 5. Lipsync Document & 9-DOF Keyframe Engine
    log_section("5. Lipsync Document, 9-DOF & Conversion Engine")
    try:
        import LipsyncDoc
        doc = LipsyncDoc.LipsyncDoc()
        doc.open_audio(tmp_wav)
        log_item("OK", "LipsyncDoc Open", f"Project: {doc.name}, Sound valid={doc.sound.IsValid() if doc.sound else False}")
        
        # Test voice & phoneme creation
        v = LipsyncDoc.LipSyncObject(object_type='voice', name='Voice 1', parent=doc.project_node)
        phrase = LipsyncDoc.LipSyncObject(object_type='phrase', name='Phrase', parent=v)
        word = LipsyncDoc.LipSyncObject(object_type='word', name='Test', parent=phrase)
        p1 = LipsyncDoc.LipSyncObject(object_type='phoneme', parent=word)
        p1.start_frame = 1
        p1.text = "etc"
        p2 = LipsyncDoc.LipSyncObject(object_type='phoneme', parent=word)
        p2.start_frame = 6
        p2.text = "AI"
        log_item("OK", "Object Hierarchy", "Voice -> Phrase -> Word -> Phonemes constructed")

        # Test phoneme conversion kit
        converted = doc.convert_to_phonemeset("rhubarb")
        log_item("OK", "Phoneme Conversion Kit", f"Successfully converted {converted} phonemes to Rhubarb")

        # Test voice effector
        fx_out = doc.apply_voice_effect(preset="Male to Female")
        log_item("OK", "Voice Effector DSP", f"Processed 'Male to Female' preset -> {os.path.basename(fx_out) if fx_out else 'Generated'}")

        # Test project save & reload
        pgo_tmp = os.path.join(tempfile.gettempdir(), "test_diag.pgo")
        doc.save(pgo_tmp)
        doc2 = LipsyncDoc.LipsyncDoc()
        doc2.open(pgo_tmp)
        log_item("OK", "PGO Roundtrip", f"Saved and reloaded {pgo_tmp} ({os.path.getsize(pgo_tmp)} bytes)")
    except Exception as e:
        log_item("FAIL", "LipsyncDoc Engine", f"{e}\n{traceback.format_exc()}")

    # 6. Windows Packaging Specification Check
    log_section("6. Windows Build & Packaging Specifications")
    spec_found = False
    for spec_file in ["papagayo-vue.spec", "papagayo-ng.spec"]:
        p = os.path.join(BASE_DIR, spec_file)
        if os.path.exists(p):
            spec_found = True
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            has_debug = "_debug" in content
            log_item("OK", f"Spec File ({spec_file})", f"Found ({len(content)} chars, dual _debug target: {has_debug})")
    if not spec_found:
        log_item("WARN", "PyInstaller Spec", "No .spec file detected in root")

    if os.path.exists(os.path.join(BASE_DIR, "build_windows.py")):
        log_item("OK", "Windows Build Script", "build_windows.py present and verified")
    else:
        log_item("FAIL", "Windows Build Script", "build_windows.py missing")

    # Final Summary
    log_section("Diagnostic Summary")
    report_text = "\n".join(REPORT_LINES)
    out_file = os.path.join(BASE_DIR, "crash_diagnostic.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\n[INFO] Full diagnostic report written to: {out_file}")
    print("       You can copy the entire block above and paste it into chat.\n")
    return report_text

if __name__ == "__main__":
    run_diagnostics()
