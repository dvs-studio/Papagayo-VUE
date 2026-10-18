#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Windows build and packaging script for Papagayo-NG.
Compiles standalone executable with PyInstaller and packages a portable ZIP release.
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
    print("  Papagayo-NG Windows Build Pipeline")
    print("========================================")

    # 1. Check or compile Qt resources if needed
    if not os.path.exists("papagayongrcc.py"):
        print("[1/4] Compiling Qt resources...")
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
        print("[1/4] Qt resource file papagayongrcc.py verified.")

    # 2. Generate file version information
    print("[2/4] Generating version metadata...")
    try:
        import pyinstaller_versionfile
        if os.path.exists("version_information.txt"):
            pyinstaller_versionfile.create_versionfile_from_input_file(
                output_file="file_version_info.txt",
                input_file="version_information.txt"
            )
            print("  Created file_version_info.txt successfully.")
    except ImportError:
        print("  pyinstaller_versionfile not installed, continuing with default metadata.")
    except Exception as e:
        print(f"  Versionfile generation note: {e}")

    # 3. Run PyInstaller
    print("[3/4] Running PyInstaller build...")
    run_cmd(f"{sys.executable} -m PyInstaller --noconfirm --clean papagayo-ng.spec")

    # 4. Assemble release bundle
    print("[4/4] Assembling release package...")
    dist_dir = os.path.join(root_dir, "dist")
    release_dir = os.path.join(dist_dir, "Papagayo-NG-Windows")
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir, exist_ok=True)

    # Find the built executable
    built_exe = os.path.join(dist_dir, "papagayo-ng.exe")
    if not os.path.exists(built_exe):
        built_exe = os.path.join(dist_dir, "papagayo-ng")

    if os.path.exists(built_exe):
        shutil.copy2(built_exe, release_dir)
        print(f"  Copied executable: {built_exe}")
    else:
        print(f"[WARN] Executable not found at {built_exe}")

    # Copy required runtime folders & files
    for folder in ["rsrc", "phonemes", "breakdowns"]:
        if os.path.exists(folder):
            shutil.copytree(folder, os.path.join(release_dir, folder), dirs_exist_ok=True)
            print(f"  Bundled folder: {folder}")

    for doc_file in ["readme.md", "gpl.txt", "about_markdown.html", "ipa_cmu.json", "version_information.txt"]:
        if os.path.exists(doc_file):
            shutil.copy2(doc_file, release_dir)

    # Create ZIP distribution
    zip_path = os.path.join(dist_dir, "Papagayo-NG-Windows-x64.zip")
    print(f"  Creating release zip: {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(release_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, dist_dir)
                zf.write(abs_path, rel_path)

    print("========================================")
    print("  Build completed successfully!")
    print(f"  Release Folder: {release_dir}")
    print(f"  Release Archive: {zip_path}")
    print("========================================")

if __name__ == "__main__":
    main()
