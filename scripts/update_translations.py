#!/usr/bin/env python3
"""
Translation Extraction and Compilation Utility Script for Lossless Crop.
Automates running pylupdate6 to extract strings into .ts files and lrelease to compile them into .qm binary files.
"""

import subprocess
from pathlib import Path


def main():
    root_dir = Path(__file__).resolve().parent.parent
    translations_dir = root_dir / "translations"
    translations_dir.mkdir(exist_ok=True)

    project_file = translations_dir / "lossless_crop.pro"

    # Generate a temporary .pro file for pylupdate6 if it doesn't exist
    # Listing all python source files and UI files
    py_files = list(root_dir.glob("**/*.py"))
    py_files_str = " \\\n    ".join(
        str(f.relative_to(root_dir))
        for f in py_files
        if "venv" not in str(f) and ".git" not in str(f) and "scripts" not in str(f)
    )

    pro_content = f"""
SOURCES = \\
    {py_files_str}

TRANSLATIONS = \\
    translations/lossless_crop_en.ts \\
    translations/lossless_crop_es.ts
"""
    project_file.write_text(pro_content, encoding="utf-8")
    print(f"Created project configuration: {project_file}")

    # Run pylupdate6
    print("Running pylupdate6 to update translation source (.ts) files...")
    try:
        subprocess.run(["pylupdate6", str(project_file)], check=True)
        print("Successfully updated .ts files.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Note: pylupdate6 execution failed or was not found: {e}")
        print(
            "Ensure PyQt6 development tools (pylupdate6) are installed in your environment."
        )

    # Run lrelease to compile .ts into .qm
    print("Running lrelease to compile .ts files into binary .qm files...")
    ts_files = list(translations_dir.glob("*.ts"))
    compiled_any = False
    for ts in ts_files:
        qm = ts.with_suffix(".qm")
        try:
            subprocess.run(["lrelease", str(ts), "-qm", str(qm)], check=True)
            print(f"Compiled {ts.name} -> {qm.name}")
            compiled_any = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try finding lrelease or Qt bin path if needed
            pass

    if not compiled_any:
        print(
            "lrelease command not found directly in PATH. You can compile .ts files using Qt Linguist's lrelease tool."
        )


if __name__ == "__main__":
    main()
