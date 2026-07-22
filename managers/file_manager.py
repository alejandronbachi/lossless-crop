# managers/file_manager.py
from pathlib import Path
from typing import List

from config.app_constants import APP_ROOT_DIR


class FileManager:
    def __init__(self):
        # Universal supported media formats
        self.SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

    def load_asset(self, filename: str, folder_name: str) -> str:
        """Dynamically loads layout styling text / HTML / QSS content safely."""
        file_path = APP_ROOT_DIR / folder_name / filename
        try:
            return file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"Warning: Asset missing at: {file_path}")
            return ""

    def scan_image_directory(self, folder_path_str: str) -> List[Path]:
        """
        Scans a target directory path and returns a sorted list of Path objects
        matching our supported image extensions.
        """
        folder = Path(folder_path_str)
        if not folder.exists() or not folder.is_dir():
            return []

        # Find all files, filter by extension, and sort them alphabetically
        valid_images = [
            file
            for file in folder.iterdir()
            if file.is_file() and file.suffix.lower() in self.SUPPORTED_EXTENSIONS
        ]

        # Sort by filename string
        valid_images.sort(key=lambda path: path.name.lower())
        return valid_images

    def generate_unique_crop_path(
        self, parent_folder_str: str, original_filename_str: str
    ) -> Path:
        """
        Creates a 'cropped' subfolder if missing and increments filename
        indexes (_1, _2, etc.) to ensure a completely unique save location.
        """
        # 1. Initialize structural components via smart paths
        base_dir = Path(parent_folder_str)
        output_subfolder = base_dir / "cropped"
        output_subfolder.mkdir(parents=True, exist_ok=True)  # Replaces os.makedirs

        # 2. Extract traits from target file name
        original_file = Path(original_filename_str)
        name_stem = original_file.stem  # e.g., 'photo' (No extension)
        file_suffix = original_file.suffix  # e.g., '.jpg' (With dot)

        # 3. Setup default destination path target
        output_filepath = output_subfolder / original_filename_str

        # 4. Increment numeric version counter strings if path conflict exists
        version_counter = 1
        while output_filepath.exists():
            new_filename = f"{name_stem}_{version_counter}{file_suffix}"
            output_filepath = output_subfolder / new_filename
            version_counter += 1

        return output_filepath
