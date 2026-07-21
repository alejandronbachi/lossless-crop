import os
import platform
import subprocess

from PIL import Image


class ImageProcessor:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if os.name == "nt":
            BINARY_FILE = "jpegtran.exe"
        elif platform.system() == "Darwin":
            BINARY_FILE = "jpegtran_mac"
        else:
            BINARY_FILE = "jpegtran_linux"
        self.binary_path = os.path.join(current_dir, "binaries", BINARY_FILE)
        self.lossless_available = os.path.exists(self.binary_path)

    def load_image(self, path):
        return Image.open(path)

    def is_lossless_supported(self, file_path):
        if not self.lossless_available:
            return False
        _, ext = os.path.splitext(file_path.lower())
        if ext not in (".jpg", ".jpeg"):
            return False
        try:
            with open(file_path, "rb") as f:
                return f.read(3) == b"\xff\xd8\xff"
        except Exception:
            return False

    def execute_crop(self, source_path, output_path, rect, use_lossless):
        # rect = (left, top, right, bottom)
        crop_left, crop_top, crop_right, crop_bottom = rect
        crop_width = crop_right - crop_left
        crop_height = crop_bottom - crop_top

        if use_lossless and self.is_lossless_supported(source_path):
            crop_argument = f"{crop_width}x{crop_height}+{crop_left}+{crop_top}"
            command = [
                self.binary_path,
                "-crop",
                crop_argument,
                "-outfile",
                output_path,
                source_path,
            ]
            subprocess.run(
                command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        else:
            with Image.open(source_path) as img:
                cropped_image = img.crop((crop_left, crop_top, crop_right, crop_bottom))
                cropped_image.save(output_path)

    def rotate_image(self, pil_image, angle):
        return pil_image.rotate(angle, expand=True)
