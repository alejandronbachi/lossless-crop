import logging
import os
import platform
import subprocess
from pathlib import Path

from PIL import Image

from config import app_constants, ui_constants

logger = logging.getLogger(__name__)


class ImageProcessor:
    def __init__(self):

        current_os = platform.system()
        if current_os == "Windows":
            binary_file = app_constants.BINARY_WINDOWS
        elif current_os == "Darwin":
            binary_file = app_constants.BINARY_MAC
        else:
            binary_file = app_constants.BINARY_LINUX
        self._binary_path = app_constants.APP_ROOT_DIR / "binaries" / binary_file
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
        if path.suffix.lower() not in app_constants.JPEG_EXTENSIONS:
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
        logger.info("\n[ENGINE ACTIVATION] ---> %s", engine_name)
        logger.info(" 📂 Source File   : %s", src)
        logger.info(" 💾 Target Output : %s", dest)
        logger.info(" 📐 File Dimensions: %sx%s", w, h)
        logger.info(" 🧮 Crop Geometry : X=%s, Y=%s, W=%s, H=%s", c_x, c_y, c_w, c_h)

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
            logger.info(
                "[SUCCESS] Lossless binary block transformation completed with 0% quality loss."
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(
                "❌ [EMERGENCY FALLBACK] jpegtran failed, shifting to Pillow re-compression: %s",
                e,
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
            logger.info(
                "[SUCCESS] Image pixel re-compression slice saved successfully."
            )
            return True
        except Exception as e:
            logger.error(
                "❌ [CROP FAILURE] Pillow re-compression pipeline failed: %s", e
            )
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
        """Centralized routing hub that,converts coordinates, logs actions,
        and delegates to the correct low-level execution method and
        safely wraps and cuts coordinates to fit the image boundaries before executing the crop tools.
        """
        src_w, src_h = image_dimensions

        #  BOUNDARY CLAMPING AND AUTO-RESIZING
        # 1. Grab raw coordinates from your unified source_rect
        raw_left = source_rect.x()
        raw_top = source_rect.y()
        raw_width = source_rect.width()
        raw_height = source_rect.height()

        # 2. Compute true bottom-right bounds before altering anything
        raw_right = raw_left + raw_width
        raw_bottom = raw_top + raw_height

        # 3. INTERSECT WITH PHYSICAL CANVAS BOUNDARIES (Prevents padding extensions)
        crop_left = max(0, min(src_w, raw_left))
        crop_top = max(0, min(src_h, raw_top))
        crop_right = max(0, min(src_w, raw_right))
        crop_bottom = max(0, min(src_h, raw_bottom))

        # 4. RECALCULATE DYNAMIC WIDTH AND HEIGHT FROM CLAMPED REGIONS
        # (This scales down the selection box to prevent left/top drifting extensions)
        crop_width = crop_right - crop_left
        crop_height = crop_bottom - crop_top

        # 5. SANITY REJECTION PASS (If selection box was dragged entirely outside the screen)
        if crop_width <= 0 or crop_height <= 0:
            return False

        # Build telemetry log block
        crop_dimensions_tuple = (crop_width, crop_height, crop_left, crop_top)

        # Handle logging and engine delegation
        if lossless:
            self.log_engine_activation(
                ui_constants.ENGINE_ACTIVATION_LOSSLESS,
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
                ui_constants.ENGINE_ACTIVATION_PIXEL_PERFECT,
                source_path,
                output_path,
                (src_w, src_h),
                crop_dimensions_tuple,
            )
            # Format arguments for Pillow: (left, top, right, bottom)
            crop_args = (crop_left, crop_top, crop_right, crop_bottom)
            return self.execute_lossy_pillow_crop(source_path, output_path, crop_args)
