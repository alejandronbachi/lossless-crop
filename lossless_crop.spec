# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Base imports shared across Windows, macOS, and Linux
base_hidden_imports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PIL',
    'PIL.Image',
    'PIL.ImageQt',
    'requests',
]

# 1. Dynamically target ONLY the assets that exist on the active OS runner
if sys.platform == "win32":
    current_icon = "assets/icons/icon.ico"            # Native Windows container metadata
    active_binaries = [("binaries/jpegtran.exe", "binaries")]
    # Force PyInstaller to bundle the shortcut plumbing on Windows runners
    active_hidden_imports = base_hidden_imports + ['winshell', 'win32com', 'win32com.client']
elif sys.platform == "darwin":
    current_icon = "assets/icons/icon.icns"           # Native Apple Retina matrix container
    active_binaries = [("binaries/jpegtran_mac", "binaries")]
    active_hidden_imports = base_hidden_imports
else:
    current_icon = "assets/icons/icon.png"            # Standard Linux high-res PNG fallback
    active_binaries = [("binaries/jpegtran_linux", "binaries")]
    active_hidden_imports = base_hidden_imports

a = Analysis(
    ['lossless_crop.py'],
    pathex=[],
    binaries=active_binaries, # Only bundles the file that physically exists on this active machine
    datas=[
        ('assets', 'assets'), # Maps your consolidated assets tree
        ('config', 'config'), # Keeps your custom config bundle intact
        ('version.txt', '.'),  # Adds version for the app to grab and show
        ('translations', 'translations'), # Package .qm files
        ('docs/user_manual_*.md', 'docs'),  # Include all markdown docs
    ],
    hiddenimports=active_hidden_imports, # Uses the platform-safe dynamic list
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

# =========================================================================
# SYSTEM SPECIFIC TARGET GENERATION BLOCK
# =========================================================================
if sys.platform == "win32":
    # ---------------------------------------------------------------------
    #  ATTACHMENT / MODIFICATION TRIGGER 
    # TARGET WINDOWS A: THE SINGLE PORTABLE EXE (For Manual GitHub Releases)
    # ---------------------------------------------------------------------
    exe_standalone = EXE(
        pyz,
        a.scripts,
        a.binaries,       
        a.zipfiles,       
        a.datas,          
        [],
        name='LosslessCrop', # Generates "dist/LosslessCrop.exe"
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,     
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=[current_icon],
    )

    # ---------------------------------------------------------------------
    # TARGET WINDOWS B: THE UNCOMPRESSED DIRECTORY (To Fuel Windows Store MSIX)
    # ---------------------------------------------------------------------
    exe_for_folder = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True, 
        name='LosslessCropStoreLauncher', # Internal execution wrapper name
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,     
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=[current_icon],
    )

    coll = COLLECT(
        exe_for_folder,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='LosslessCropAppFolder', # Generates "dist/LosslessCropAppFolder/" directory
    )

else:
    # TARGET LINUX & MACOS: Preserves your existing high-performance single-binary structures
    exe_standalone = EXE(
        pyz,
        a.scripts,
        a.binaries,       
        a.zipfiles,       
        a.datas,          
        [],
        name='LosslessCrop',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,     
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=[current_icon],
    )
