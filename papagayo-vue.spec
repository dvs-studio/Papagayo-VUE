# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification for Papagayo-VUE.
Redeveloped by Victory Ukpong (2026).
Dual-Target Build:
  1. Papagayo-VUE.exe: Standard windowed GUI application (no console popup)
  2. Papagayo-VUE_debug.exe: Console-enabled executable with interactive CMD logging & tracebacks
"""
import os
import sys

block_cipher = None

datas = [
    ('rsrc', 'rsrc'),
    ('phonemes', 'phonemes'),
    ('breakdowns', 'breakdowns'),
    ('ipa_cmu.json', '.'),
    ('version_information.txt', '.'),
    ('about_markdown.html', '.'),
    ('gpl.txt', '.'),
]

hidden_imports = [
    'qt_compat',
    'papagayongrcc',
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtUiTools',
    'numpy',
    'audioread',
    'pydub',
    'pydub.playback',
    'pydub.utils',
    'yaml',
    'appdirs',
    'anytree',
    'sounddevice',
    'cffi',
    'wave',
    'struct',
    'logging',
    'configparser',
]

spec_version_file = "./file_version_info.txt" if os.path.exists("./file_version_info.txt") else None
icon_file = './papagayo-ng.ico' if os.path.exists('./papagayo-ng.ico') else None

# ==============================================================================
# TARGET 1: Windowed Release Executable (Papagayo-VUE.exe)
# ==============================================================================
a_release = Analysis(
    ['papagayo-vue.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz_release = PYZ(a_release.pure, a_release.zipped_data, cipher=block_cipher)

exe_release = EXE(
    pyz_release,
    a_release.scripts,
    a_release.binaries,
    a_release.zipfiles,
    a_release.datas,
    [],
    name='Papagayo-VUE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon_file,
    version=spec_version_file
)

# ==============================================================================
# TARGET 2: Debug Console Executable (Papagayo-VUE_debug.exe)
# ==============================================================================
a_debug = Analysis(
    ['papagayo-vue.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz_debug = PYZ(a_debug.pure, a_debug.zipped_data, cipher=block_cipher)

exe_debug = EXE(
    pyz_debug,
    a_debug.scripts,
    a_debug.binaries,
    a_debug.zipfiles,
    a_debug.datas,
    [],
    name='Papagayo-VUE_debug',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=icon_file,
    version=spec_version_file
)
