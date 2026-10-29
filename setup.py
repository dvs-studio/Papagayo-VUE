# -*- coding: utf-8 -*-
# Papagayo-NG, a lip-sync tool for use with several different animation suites
# Original Copyright (C) 2005 Mike Clifton
# Modifications (C) 2020-2026 Morevna Project / Papagayo-NG Contributors
# Licensed under GNU General Public License v2 or later (see gpl.txt)

from setuptools import setup, find_packages
import os
import sys

def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "version_information.txt")
    if os.path.exists(version_file):
        with open(version_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("version:"):
                    return line.split(":")[1].strip()
    return "1.4.2"

setup(
    name="Papagayo-NG",
    version=get_version(),
    description="Lip-sync animation tool for 2D and 3D animators (Moho, Synfig, Blender)",
    long_description=open("readme.md", encoding="utf-8").read() if os.path.exists("readme.md") else "",
    long_description_content_type="text/markdown",
    author="Morevna Project / Mike Clifton",
    license="GPL-2.0-or-later",
    url="https://github.com/morevnaproject/papagayo-ng",
    packages=find_packages(),
    py_modules=[
        "qt_compat",
        "papagayongrcc",
        "utilities",
        "LipsyncDoc",
        "LipsyncFrameQT",
        "WaveformViewRewrite",
        "MouthViewQT",
        "SettingsQT",
        "AboutBoxQT",
        "PronunciationDialogQT",
        "SoundPlayer",
        "SoundPlayerNew",
        "SoundPlayerOSX",
        "SoundPlayerQT",
        "Rhubarb",
        "auto_recognition",
        "phoneme_conversion_helper"
    ],
    install_requires=[
        "PySide6>=6.5.0",
        "sounddevice>=0.4.6",
        "cffi>=1.15.0",
        "numpy>=1.22.0",
        "pydub>=0.25.1",
        "anytree>=2.8.0",
        "audioread>=3.0.0",
        "appdirs>=1.4.4",
        "pyyaml>=6.0",
    ],
    extras_require={
        "legacy": [
            "PySide2>=5.15.2",
        ],
        "build": [
            "pyinstaller>=6.0.0",
            "pyinstaller-versionfile>=2.1.1",
        ]
    },
    entry_points={
        "gui_scripts": [
            "papagayo-ng = papagayo_ng:main",
        ]
    },
    python_requires=">=3.8",
)
