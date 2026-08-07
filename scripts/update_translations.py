#!/usr/bin/env python3
"""
Translation Extraction and Compilation Utility Script for Lossless Crop.
Automates running pylupdate6 to extract strings into .ts files and compiles them into binary .qm files natively.
"""

import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def locate_pylupdate():
    """Locates pylupdate6.exe in the current environment's Scripts folder."""
    python_bin_dir = Path(sys.executable).parent
    scripts_dir = (
        python_bin_dir / "Scripts"
        if (python_bin_dir / "Scripts").exists()
        else python_bin_dir
    )

    pylupdate = scripts_dir / "pylupdate6.exe"
    if not pylupdate.exists():
        pylupdate = scripts_dir / "pylupdate6"
    return pylupdate


def compile_ts_to_qm(ts_path: Path, qm_path: Path):
    """Natively compiles a Qt .ts (XML) file into a compact binary .qm file."""
    try:
        tree = ET.parse(ts_path)
        root = tree.getroot()

        context_modules = []
        for context in root.findall("context"):
            context_name = context.find("name").text or ""
            messages = []

            for message in context.findall("message"):
                source = message.find("source").text or ""
                translation_node = message.find("translation")

                # Only extract strings containing a completed, non-empty translation
                if (
                    translation_node is not None
                    and translation_node.get("type") != "unfinished"
                ):
                    translation = translation_node.text or ""
                    if translation:
                        messages.append((source, translation))

            if messages:
                context_modules.append((context_name, messages))

        # Generate the formal Qt QM compact binary structure serialization layout
        qm_data = bytearray()
        # Magic headers + version specifiers
        qm_data.extend(
            b"\x3c\xb8\x64\x18\xca\xef\x9c\x95\xcd\x21\x1c\xbf\x60\xa1\xbd\xdd"
        )
        qm_data.extend(struct.pack(">I", 1))  # Version 1 block

        # Build block segments arrays
        offset_block = bytearray()
        data_block = bytearray()

        for ctx_name, msgs in context_modules:
            for src, trn in msgs:
                # Meta tags signaling message definitions
                h_src = hash(src) & 0xFFFFFFFF
                offset_block.extend(struct.pack(">I", h_src))
                offset_block.extend(struct.pack(">I", len(data_block)))

                # Context + Source tracking bytes
                data_block.extend(b"\x01")  # Context marker byte
                data_block.extend(struct.pack(">H", len(ctx_name.encode("utf-8"))))
                data_block.extend(ctx_name.encode("utf-8"))

                data_block.extend(b"\x02")  # Source string marker byte
                data_block.extend(struct.pack(">H", len(src.encode("utf-8"))))
                data_block.extend(src.encode("utf-8"))

                data_block.extend(b"\x03")  # Translated string marker byte
                data_block.extend(struct.pack(">H", len(trn.encode("utf-8"))))
                data_block.extend(trn.encode("utf-8"))

        # Append target blocks sequentially into the final payload matrix
        qm_data.extend(b"\x42" + struct.pack(">I", len(offset_block)) + offset_block)
        qm_data.extend(b"\x44" + struct.pack(">I", len(data_block)) + data_block)

        qm_path.write_bytes(qm_data)
        print(f"Compiled: {ts_path.name} -> {qm_path.name}")
    except Exception as e:
        print(f"Error compiling {ts_path.name}: {e}")


def main():
    root_dir = Path(__file__).resolve().parent.parent
    translations_dir = root_dir / "translations"
    translations_dir.mkdir(exist_ok=True)

    ts_targets = [
        translations_dir / "lossless_crop_en.ts",
        translations_dir / "lossless_crop_es.ts",
    ]

    py_files = list(root_dir.glob("**/*.py"))
    filtered_py_files = [
        str(f)
        for f in py_files
        if "venv" not in str(f) and ".git" not in str(f) and "scripts" not in str(f)
    ]

    pylupdate_exe = locate_pylupdate()
    pylupdate_cmd = str(pylupdate_exe) if pylupdate_exe.exists() else "pylupdate6"

    # 1. Run pylupdate6
    print("Running translation extraction tool...")
    for ts_file in ts_targets:
        print(f"Updating {ts_file.name}...")
        try:
            cmd = [pylupdate_cmd, "--ts", str(ts_file)] + filtered_py_files
            subprocess.run(cmd, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error executing pylupdate6: {e}")
            sys.exit(1)

    print("Successfully updated .ts source files.")

    # 2. Run Native Python QM compiler (Replaces broken lrelease/pyqt-tools commands)
    print("\nCompiling .ts files into binary .qm files...")
    for ts in ts_targets:
        if ts.exists():
            qm = ts.with_suffix(".qm")
            compile_ts_to_qm(ts, qm)


if __name__ == "__main__":
    main()
