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
        self._lossless_available = self.binary_path.exists()

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
                return f.read(2) == b"\xff\xd8"
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
        self, src: Path, dest: str, crop_box: tuple, rotation_angle: int = 0
    ) -> bool:
        """ENGINE A: Executes raw binary block manipulations inside VRAM via jpegtran."""
        c_w, c_h, c_x, c_y = crop_box
        crop_argument = f"{c_w}x{c_h}+{c_x}+{c_y}"

        command = [
            self.binary_path,
            "-copy",
            "all",
            "-crop",
            crop_argument,
        ]

        # Convert your internal CCW rotation angle to a CW angle for jpegtran
        cw_angle = (-rotation_angle) % 360
        if cw_angle in (90, 180, 270):
            command.extend(["-rot", str(cw_angle)])

        command.extend(
            [
                "-outfile",
                dest,
                str(src),
            ]
        )

        # Create a startup info object to hide the console window
        startupinfo = None
        if os.name == "nt":  # Only applies to Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE  # 0

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
            )
            if result.stdout:
                logger.debug("jpegtran stdout: %s", result.stdout.strip())
            logger.info(
                "[SUCCESS] Lossless binary block transformation completed with 0%% quality loss."
            )
            return True
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.strip() if e.stderr else str(e)
            logger.error(
                "❌ [ERROR] jpegtran failed (exit code %s): %s",
                e.returncode,
                error_output,
            )
            return False
        except FileNotFoundError as e:
            logger.error("❌ [ERROR] Binary not found for jpegtran: %s", e)
            return False

    # IMAGE PROCESSOR ROUTER METHOD

    def process_and_route_crop(
        self,
        lossless: bool,
        source_path,
        output_path,
        source_rect,
        image_dimensions,
        rotation_angle: int = 0,
        is_true_jpeg: bool = False,
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
                source_path, output_path, crop_args, rotation_angle=rotation_angle
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
            return self.execute_lossy_pillow_crop(
                source_path,
                output_path,
                crop_args,
                rotation_angle=rotation_angle,
                is_true_jpeg=is_true_jpeg,
            )

    def execute_lossy_pillow_crop(
        self,
        src: Path,
        dest: str,
        bounding_box: tuple,
        rotation_angle: int = 0,
        is_true_jpeg: bool = False,
    ) -> bool:
        """ENGINE B: Standard fallback or pixel-perfect CPU image re-compression."""
        left, top, right, bottom = bounding_box
        try:
            with Image.open(src) as img:
                img_format = img.format  # Cache format before transformations

                # 1. Isolate metadata building using self
                save_kwargs = self._extract_pillow_metadata(img, rotation_angle)

                # 2. Apply chronological transformations
                if rotation_angle % 360 != 0:
                    img = img.rotate(rotation_angle % 360, expand=True)

                cropped_image = img.crop((left, top, right, bottom))

                # 3. Use clean instance methods for format routing
                is_webp = img_format == "WEBP" or Path(src).suffix.lower() == ".webp"

                if is_true_jpeg:
                    return self._save_pillow_jpeg(img, cropped_image, dest, save_kwargs)
                if is_webp:
                    return self._save_pillow_webp(cropped_image, dest, save_kwargs)

                return self._save_pillow_generic_fallback(
                    cropped_image, dest, img_format, save_kwargs
                )

        except Exception as err:
            logger.error("Pillow crop execution failed: %s", err)
            return False

    # --- Extracted Private Instance Helpers ---

    def _extract_pillow_metadata(self, img: Image.Image, rotation_angle: int) -> dict:
        """Extracts and safely processes incoming image EXIF and ICC profile layers."""
        save_kwargs = {}

        icc_profile = img.info.get("icc_profile")
        if icc_profile:
            save_kwargs["icc_profile"] = icc_profile

        try:
            exif_obj = img.getexif()
            if exif_obj:
                # Reset Orientation tag (0x0112) to Normal (1) if physical rotation was applied
                if rotation_angle % 360 != 0:
                    exif_obj[0x0112] = 1
                save_kwargs["exif"] = exif_obj.tobytes()
        except Exception as ex_err:
            logger.warning("Could not process EXIF tags: %s", ex_err)
            exif_data = img.info.get("exif")
            if exif_data:
                save_kwargs["exif"] = exif_data

        return save_kwargs

    def _save_pillow_jpeg(
        self,
        original_img: Image.Image,
        cropped_img: Image.Image,
        dest: str,
        save_kwargs: dict,
    ) -> bool:
        """Handles quantization 'keep' verification or falls back to basic high-quality JPEG compression."""
        has_qtables = (
            hasattr(original_img, "quantization") and original_img.quantization
        )
        if has_qtables:
            try:
                cropped_img.save(
                    dest,
                    format="JPEG",
                    quality="keep",
                    subsampling="keep",
                    qtables=original_img.quantization,
                    **save_kwargs,
                )
                logger.info("[SUCCESS] JPEG saved successfully with quality='keep'.")
                return True
            except Exception as keep_err:
                logger.debug("JPEG quality='keep' failed: %s. Falling back.", keep_err)

        # Standard JPEG Fallback
        cropped_img.save(dest, format="JPEG", quality=95, subsampling=0, **save_kwargs)
        logger.info("[SUCCESS] JPEG saved via premium fallback profile.")
        return True

    def _save_pillow_webp(
        self, cropped_img: Image.Image, dest: str, save_kwargs: dict
    ) -> bool:
        """Applies explicit performance parameters required by WebP schemas."""
        cropped_img.save(dest, format="WEBP", quality=95, method=6, **save_kwargs)
        logger.info("[SUCCESS] WebP saved successfully.")
        return True

    def _save_pillow_generic_fallback(
        self,
        cropped_img: Image.Image,
        dest: str,
        img_format: str | None,
        save_kwargs: dict,
    ) -> bool:
        """Saves any remaining non-specialized formats like PNG, BMP, or TIFF."""
        cropped_img.save(dest, format=img_format, **save_kwargs)
        logger.info("[SUCCESS] Image saved successfully using format fallback.")
        return True
