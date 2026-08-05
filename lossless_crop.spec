# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# 1. Dynamically target ONLY the assets that exist on the active OS runner
if sys.platform == "win32":
    current_icon = "assets/icons/icon.ico"            # Native Windows container metadata
    active_binaries = [("binaries/jpegtran.exe", "binaries")]
elif sys.platform == "darwin":
    current_icon = "assets/icons/icon.icns"           # Native Apple Retina matrix container
    active_binaries = [("binaries/jpegtran_mac", "binaries")]
else:
    current_icon = "assets/icons/icon.png"            # Standard Linux high-res PNG fallback
    active_binaries = [("binaries/jpegtran_linux", "binaries")]

a = Analysis(
    ['lossless_crop.py'],
    pathex=[],
    binaries=active_binaries, # Only bundles the file that physically exists on this active machine
    datas=[
        ('assets', 'assets'), # Maps your consolidated assets tree
        ('config', 'config'), # Keeps your custom config bundle intact
        ('version.txt', '.'),  # Adds version for the app to grab and show
        ('docs/user_manual.md', 'docs'),  # Adds user manual
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PIL',
        'PIL.Image',
        'PIL.ImageQt',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,       # <-- Added this line to pack binaries inside
    a.zipfiles,       # <-- Added this line to pack python modules inside
    a.datas,          # <-- Added this line to pack your assets folder inside
    [],
    name='LosslessCrop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,     # Hides the black terminal box
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[current_icon],
)


