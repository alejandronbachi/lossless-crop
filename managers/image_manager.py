import os
import platform
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

    def execute_crop(self, source_path, output_path, rect, use_lossless):
        pass

    def rotate_image(self, pil_image, angle):
        return pil_image.rotate(angle, expand=True)
