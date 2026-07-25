import os
import platform
import subprocess
from pathlib import Path

from PIL import Image

from config.app_constants import APP_ROOT_DIR


class ImageProcessor:
    def __init__(self):

        current_os = platform.system()
        if current_os == "Windows":
            binary_file = "jpegtran.exe"
        elif current_os == "Darwin":
            binary_file = "jpegtran_mac"
        else:
            binary_file = "jpegtran_linux"
        self._binary_path = APP_ROOT_DIR / "binaries" / binary_file
        self._lossless_available = os.path.exists(self.binary_path)

    @property
    def binary_path(self) -> Path:
        """Exposes the absolute target path to the system binary executable."""
        return self._binary_path

    @property
    def is_lossless_available(self) -> bool:
        """Dynamically verifies if the required lossless binary executable exists on disk."""
        return self._binary_path.exists()

    def load_image(self, path):
        return Image.open(path)

    @staticmethod
    def is_true_jpeg(file_path_input) -> bool:
        """
        Validates if a file is an authentic JPEG by verifying its suffix
        and testing its underlying magic number binary signatures.
        """
        # 1. Convert input cleanly to a Path object (handles strings or Path instances)
        path = Path(file_path_input)

        # 2. Extract extension string using modern case-insensitive suffix calls
        if path.suffix.lower() not in (".jpg", ".jpeg"):
            return False

        try:
            # 3. Open, read exactly 3 bytes, and close file implicitly in one go
            with path.open("rb") as f:
                return f.read(3) == b"\xff\xd8\xff"
        except Exception:
            return False

    @staticmethod
    def log_engine_activation(
        engine_name: str, src: Path, dest: str, size: tuple, crop_box: tuple
    ):
        """Prints a clean, structured typographic layout map of active operations."""
        w, h = size
        c_w, c_h, c_x, c_y = crop_box
        print(f"\n[ENGINE ACTIVATION] ---> {engine_name}")
        print(f" 📂 Source File   : {src}")
        print(f" 💾 Target Output : {dest}")
        print(f" 📐 File Dimensions: {w}x{h}")
        print(f" 🧮 Crop Geometry : X={c_x}, Y={c_y}, W={c_w}, H={c_h}")

    def execute_lossless_jpegtran_crop(
        self, src: Path, dest: str, crop_box: tuple
    ) -> bool:
        """🚀 ENGINE A: Executes raw binary block manipulations inside VRAM via jpegtran."""
        c_w, c_h, c_x, c_y = crop_box
        crop_argument = f"{c_w}x{c_h}+{c_x}+{c_y}"

        command = [
            self.binary_path,
            "-crop",
            crop_argument,
            "-outfile",
            dest,
            str(src),
        ]
        try:
            subprocess.run(
                command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            print(
                "[SUCCESS] Lossless binary block transformation completed with 0% quality loss."
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(
                f"❌ [EMERGENCY FALLBACK] jpegtran failed, shifting to Pillow re-compression: {e}"
            )
            return self.execute_lossy_pillow_crop(
                src, dest, (c_x, c_y, c_x + c_w, c_y + c_h)
            )

    @staticmethod
    def execute_lossy_pillow_crop(src: Path, dest: str, bounding_box: tuple) -> bool:
        """🎨 ENGINE B: Standard fallback or pixel-perfect CPU image re-compression."""
        left, top, right, bottom = bounding_box
        try:
            # We open an isolated reader instance to dodge file locks and data degradation
            with Image.open(src) as img:
                cropped_image = img.crop((left, top, right, bottom))
                cropped_image.save(dest)
            print("[SUCCESS] Image pixel re-compression slice saved successfully.")
            return True
        except Exception as e:
            print(f"❌ [CROP FAILURE] Pillow re-compression pipeline failed: {e}")
            return False

    @staticmethod
    def rotate_session_view(session) -> int:
        """
        Rotates the active visual viewport texture without degrading the original source data.
        Returns the updated cumulative rotation angle integer.
        """
        if not session or not session.has_active_image:
            return 0

        # 1. Update the session's cumulative rotation angle property tracker
        session.current_rotation_angle = (session.current_rotation_angle - 90) % 360

        # 2. Compute a hardware-accelerated texture transform
        from PyQt6.QtGui import QTransform

        transform = QTransform().rotate(-90)

        # 3. Apply the rotation directly to the GPU VRAM cache layer
        session.master_pixmap = session.master_pixmap.transformed(transform)

        # 4. Flip the session dimensions so resolution readouts track correctly
        session.width, session.height = session.height, session.width

        return session.current_rotation_angle

        # IMAGE PROCESSOR ROUTER METHOD

    def process_and_route_crop(
        self, lossless: bool, source_path, output_path, source_rect, image_dimensions
    ) -> bool:
        """Centralized routing hub that converts coordinates, logs actions,
        and delegates to the correct low-level execution method.
        """
        src_w, src_h = image_dimensions

        # 1. Safely break down unified coordinates
        crop_left = max(0, source_rect.x())
        crop_top = max(0, source_rect.y())
        crop_width = source_rect.width()
        crop_height = source_rect.height()

        crop_right = min(src_w, crop_left + crop_width)
        crop_bottom = min(src_h, crop_top + crop_height)

        crop_dimensions_tuple = (crop_width, crop_height, crop_left, crop_top)

        # 2. Handle logging and engine delegation
        if lossless:
            self.log_engine_activation(
                "LOSSLESS MODE (jpegtran)",
                source_path,
                output_path,
                (src_w, src_h),
                crop_dimensions_tuple,
            )
            # Format arguments for jpegtran: (width, height, left, top)
            crop_args = crop_dimensions_tuple
            return self.execute_lossless_jpegtran_crop(
                source_path, output_path, crop_args
            )
        else:
            self.log_engine_activation(
                "PIXEL-PERFECT MODE (Pillow)",
                source_path,
                output_path,
                (src_w, src_h),
                crop_dimensions_tuple,
            )
            # Format arguments for Pillow: (left, top, right, bottom)
            crop_args = (crop_left, crop_top, crop_right, crop_bottom)
            return self.execute_lossy_pillow_crop(source_path, output_path, crop_args)
