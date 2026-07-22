# managers/file_manager.py
from pathlib import Path

from PIL import Image

from config.app_constants import APP_ROOT_DIR, SUPPORTED_IMAGE_EXTENSIONS
from managers.settings_manager import SettingsManager


class FileManager:
    def __init__(self, settings_manager: SettingsManager):
        # Dependency Injection keeps components loosely coupled and testable
        self.settings = settings_manager

    def load_asset(self, filename: str, folder_name: str) -> str:
        """Dynamically loads layout styling text / HTML / QSS content safely."""
        file_path = APP_ROOT_DIR / folder_name / filename
        try:
            return file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"Warning: Asset missing at: {file_path}")
            return ""

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

    def scan_and_validate_directory(self, directory: Path) -> list[Path]:
        """Scans a directory using pathlib path loops and verifies image headers."""
        if not directory or not directory.exists():
            return []

        raw_files = [
            item
            for item in directory.iterdir()
            if item.is_file() and item.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        ]
        raw_files.sort(key=lambda x: x.name)

        # 🚨 FIX: Save the full Path object, not just file_path.name
        valid_paths = []
        for file_path in raw_files:
            try:
                with Image.open(file_path) as img:
                    img.verify()
                valid_paths.append(file_path)  # Keep the full Path object!
            except Exception:
                print(
                    f"[SECURITY SHIELD] Discarded fake or corrupted image: {file_path.name}"
                )

        return valid_paths

    def process_path(self, target_str_path: str) -> tuple[str, str | None, list[str]]:
        """
        Processes any input file or folder string path using Path objects.
        Returns a tuple of (folder_path_str, starting_file_name_str, list_of_valid_filenames)
        """
        path = Path(target_str_path)
        target_folder = path if path.is_dir() else path.parent
        target_starting_file = None if path.is_dir() else path.name

        valid_files = self.scan_and_validate_directory(target_folder)

        # Return string primitives back to the main UI functions
        return str(target_folder), target_starting_file, valid_files
