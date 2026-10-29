# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import shutil

block_cipher = None
standalone_exe = True
with_rhubarb = False

# Generate version information file on Windows if pyinstaller_versionfile is present
if sys.platform == "win32":
    try:
        import pyinstaller_versionfile
        if os.path.exists("./version_information.txt"):
            pyinstaller_versionfile.create_versionfile_from_input_file(
                output_file="./file_version_info.txt",
                input_file="./version_information.txt"
            )
    except Exception as e:
        print(f"Warning: could not generate version file: {e}")

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
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtUiTools',
    'PySide2',
    'PySide2.QtCore',
    'PySide2.QtGui',
    'PySide2.QtWidgets',
    'PySide2.QtUiTools',
    'numpy.random.common',
    'numpy.random.bounded_integers',
    'numpy.random.entropy',
    'audioread',
    'pydub',
    'yaml',
    'appdirs',
    'anytree',
    'sounddevice',
    'cffi',
]

a = Analysis(
    ['papagayo-ng.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

spec_file = "./file_version_info.txt" if (sys.platform == "win32" and os.path.exists("./file_version_info.txt")) else None
splash_file = './rsrc/splash.png' if os.path.exists('./rsrc/splash.png') else None

if splash_file and sys.platform == "win32":
    try:
        splash = Splash(splash_file, binaries=a.binaries, datas=a.datas)
    except Exception:
        splash = None
else:
    splash = None

exe_args = {
    'name': 'papagayo-ng',
    'debug': False,
    'bootloader_ignore_signals': False,
    'strip': False,
    'upx': False,
    'console': False,
    'icon': './papagayo-ng.ico' if os.path.exists('./papagayo-ng.ico') else None,
}

if spec_file:
    exe_args['version'] = spec_file

if standalone_exe:
    # Single-file standalone executable
    splash_items = [splash, splash.binaries] if splash else []
    exe = EXE(
        pyz,
        a.scripts,
        *splash_items,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        **exe_args
    )
else:
    # Multi-file directory distribution
    splash_items = [splash] if splash else []
    exe = EXE(
        pyz,
        a.scripts,
        *splash_items,
        a.zipfiles,
        exclude_binaries=True,
        **exe_args
    )
    coll = COLLECT(
        exe,
        splash.binaries if splash else [],
        a.binaries,
        a.datas,
        name='papagayo-ng',
        strip=False,
        upx=False
    )