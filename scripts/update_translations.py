#!/usr/bin/env python3
"""
Translation Extraction and Compilation Utility Script for Lossless Crop.
Automates running pylupdate6 to extract strings into .ts files and lrelease to compile them into .qm binary files.
"""

import subprocess
import sys
from pathlib import Path


def locate_translation_tools():
    """Locates pylupdate6.exe and pyside6-lrelease.exe in the current environment's Scripts folder."""
    python_bin_dir = Path(sys.executable).parent
    scripts_dir = (
        python_bin_dir / "Scripts"
        if (python_bin_dir / "Scripts").exists()
        else python_bin_dir
    )

    pylupdate = scripts_dir / "pylupdate6.exe"
    if not pylupdate.exists():
        pylupdate = scripts_dir / "pylupdate6"

    lrelease = scripts_dir / "pyside6-lrelease.exe"
    if not lrelease.exists():
        lrelease = scripts_dir / "pyside6-lrelease"

    return pylupdate, lrelease


def main():
    root_dir = Path(__file__).resolve().parent.parent
    translations_dir = root_dir / "translations"
    translations_dir.mkdir(exist_ok=True)

    # Define targeted .ts translation target files
    ts_targets = [
        translations_dir / "lossless_crop_en.ts",
        translations_dir / "lossless_crop_es.ts",
    ]

    # Gather python source files dynamically, ignoring environment directories
    py_files = list(root_dir.glob("**/*.py"))
    filtered_py_files = [
        str(f)
        for f in py_files
        if "venv" not in str(f) and ".git" not in str(f) and "scripts" not in str(f)
    ]

    pylupdate_exe, lrelease_exe = locate_translation_tools()
    pylupdate_cmd = str(pylupdate_exe) if pylupdate_exe.exists() else "pylupdate6"

    # 1. Run pylupdate6 for each targeted language
    print("Running translation extraction tool...")
    for ts_file in ts_targets:
        print(f"Updating {ts_file.name}...")
        try:
            cmd = [pylupdate_cmd, "--ts", str(ts_file)] + filtered_py_files
            subprocess.run(cmd, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error executing pylupdate6: {e}")
            print("Ensure PyQt6 is installed via 'pip install PyQt6'")
            sys.exit(1)

    print("Successfully updated .ts source files.")

    # 2. Run lrelease to compile .ts into binary .qm files
    print("\nCompiling .ts files into binary .qm files...")
    if not lrelease_exe or not lrelease_exe.exists():
        print(
            "[ERROR] Could not find 'pyside6-lrelease'. Please run: pip install PySide6"
        )
        sys.exit(1)

    print(f"Using native tool: {lrelease_exe.name}")
    for ts in ts_targets:
        if ts.exists():
            qm = ts.with_suffix(".qm")
            try:
                # Command syntax structure for standard lrelease tool environments
                subprocess.run([str(lrelease_exe), str(ts), "-qm", str(qm)], check=True)
                print(f"Compiled successfully: {ts.name} -> {qm.name}")
            except subprocess.CalledProcessError as e:
                print(f"Warning: Could not compile {ts.name}. Reason: {e}")


if __name__ == "__main__":
    main()
