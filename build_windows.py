#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Windows build and packaging script for Papagayo-VUE.
Redeveloped by Victory Ukpong (2026).
Compiles dual standalone executables (Papagayo-VUE.exe + Papagayo-VUE_debug.exe)
and packages a portable ZIP release.
"""

import os
import sys
import shutil
import subprocess
import zipfile

def run_cmd(cmd, check=True):
    print(f"[RUN] {cmd}")
    res = subprocess.run(cmd, shell=True)
    if check and res.returncode != 0:
        print(f"[ERROR] Command failed with exit code {res.returncode}: {cmd}")
        sys.exit(res.returncode)
    return res.returncode

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)

    print("========================================")
    print("  Papagayo-VUE Windows Build Pipeline")
    print("  Redeveloped by Victory Ukpong (2026)")
    print("========================================")

    # 1. Check or compile Qt resources if needed
    if not os.path.exists("papagayongrcc.py"):
        print("[1/5] Compiling Qt resources...")
        rcc_cmd = None
        for candidate in ["pyside6-rcc", "pyrcc5", "pyside2-rcc"]:
            if shutil.which(candidate):
                rcc_cmd = candidate
                break
        if rcc_cmd:
            run_cmd(f"{rcc_cmd} qt-icons.qrc -o papagayongrcc.py")
        else:
            print("[WARN] No RCC compiler found in PATH, skipping resource recompilation.")
    else:
        print("[1/5] Qt resource file papagayongrcc.py verified.")

    # 2. Generate file version information if needed
    print("[2/5] Checking version metadata...")
    if not os.path.exists("file_version_info.txt") or os.path.getsize("file_version_info.txt") < 50:
        try:
            import pyinstaller_versionfile
            if os.path.exists("version_information.txt"):
                pyinstaller_versionfile.create_versionfile_from_input_file(
                    output_file="file_version_info.txt",
                    input_file="version_information.txt"
                )
                print("  Generated file_version_info.txt from version_information.txt.")
        except Exception as e:
            print(f"  Versionfile generation note: {e}")
    else:
        print("  file_version_info.txt verified and present.")

    # 3. Choose PyInstaller spec
    spec_target = "papagayo-vue.spec" if os.path.exists("papagayo-vue.spec") else "papagayo-ng.spec"
    print(f"[3/5] Running PyInstaller build using {spec_target}...")
    py_exec = sys.executable or "python"
    run_cmd(f'"{py_exec}" -m PyInstaller --noconfirm --clean "{spec_target}"')

    # 4. Assemble release bundle
    print("[4/5] Assembling dual-executable release package...")
    dist_dir = os.path.join(root_dir, "dist")
    release_dir = os.path.join(dist_dir, "Papagayo-VUE-Windows")
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir, exist_ok=True)

    # Look for both Papagayo-VUE and Papagayo-VUE_debug
    exe_candidates = [
        ("Papagayo-VUE.exe", "Papagayo-VUE"),
        ("Papagayo-VUE_debug.exe", "Papagayo-VUE_debug"),
        ("papagayo-ng.exe", "papagayo-ng")
    ]
    copied_exes = []
    for exe_name, fallback_name in exe_candidates:
        candidate_paths = [
            os.path.join(dist_dir, exe_name),
            os.path.join(dist_dir, fallback_name),
            os.path.join(dist_dir, exe_name.replace(".exe", ""), exe_name),
            os.path.join(dist_dir, fallback_name, f"{fallback_name}.exe")
        ]
        for candidate_path in candidate_paths:
            if os.path.exists(candidate_path) and os.path.isfile(candidate_path):
                dest = os.path.join(release_dir, exe_name)
                shutil.copy2(candidate_path, dest)
                copied_exes.append(exe_name)
                print(f"  [OK] Bundled binary: {exe_name} (from {candidate_path})")
                break

    if not copied_exes:
        print("[ERROR] No compiled executable binaries found in dist/!")
        sys.exit(1)

    # Copy required runtime folders & files
    for folder in ["rsrc", "phonemes", "breakdowns"]:
        if os.path.exists(folder):
            shutil.copytree(folder, os.path.join(release_dir, folder), dirs_exist_ok=True)
            print(f"  Bundled folder: {folder}")

    for doc_file in ["readme.md", "gpl.txt", "about_markdown.html", "ipa_cmu.json", "version_information.txt", "diagnose_crash.py"]:
        if os.path.exists(doc_file):
            shutil.copy2(doc_file, release_dir)

    # 5. Create ZIP distribution
    print("[5/5] Creating release zip...")
    zip_path = os.path.join(dist_dir, "Papagayo-VUE-Windows-x64.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(release_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, dist_dir)
                zf.write(abs_path, rel_path)

    # Write build summary
    summary_path = os.path.join(dist_dir, "build_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("Papagayo-VUE Build Summary\n")
        f.write("Redeveloped by Victory Ukpong (2026)\n")
        f.write("========================================\n")
        f.write(f"Release Dir: {release_dir}\n")
        f.write(f"Executables: {', '.join(copied_exes)}\n")
        f.write(f"Archive: {zip_path}\n")

    print("========================================")
    print("  Build completed successfully!")
    print(f"  Release Folder: {release_dir}")
    print(f"  Bundled Executables: {', '.join(copied_exes)}")
    print(f"  Release Archive: {zip_path}")
    print("========================================")

if __name__ == "__main__":
    main()
