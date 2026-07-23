from pathlib import Path

from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt6.QtGui import QPixmap

from managers.image_manager import ImageProcessor


class ImageSession:
    def __init__(self):
        # --- 📁 The Active Directory Workspace State ---
        self.folder_path: Path | None = None
        self.files: list[Path] = []
        self.current_index: int = -1

        # --- 🧠 Master High-Fidelity Memory Caches (Single Source of Truth) ---
        self.pil_image: Image.Image | None = None
        self.master_pixmap: QPixmap | None = None
        self._qimg_ref: ImageQt | None = (
            None  # Crucial: Blocks C++ Garbage Collection Segfaults
        )

        # --- 📊 Metadata Tracking Variables ---
        self.current_rotation_angle: int = 0
        self.is_true_jpeg: bool = False
        self.width: int = 0
        self.height: int = 0

    # -------------------------------------------------------------
    # 🏎️ DIRECTORY WORKSPACE NAVIGATION ENGINE
    # -------------------------------------------------------------
    def load_folder(
        self, folder_path: str, valid_files: list[Path], target_filename: str = None
    ) -> bool:
        """Initializes a brand new folder workspace, automatically tracking the file target index."""
        if not valid_files:
            self.close_session()
            return False

        self.folder_path = Path(folder_path)
        self.files = valid_files
        self.current_rotation_angle = 0  # Reset rotation state on fresh folder loads

        # Cleanly isolate target index mapping calculations
        if target_filename:
            matched = next(
                (i for i, p in enumerate(self.files) if p.name == target_filename), 0
            )
            self.current_index = matched
        else:
            self.current_index = 0

        return self.hydrate_current_image()

    def next(self) -> str | None:
        """Advances index without looping. Returns an alert string if blocked."""
        if not self.files:
            return "No directory active"

        if self.current_index < len(self.files) - 1:
            self.current_index += 1
            self.hydrate_current_image()
            return None
        else:
            return "Last image of directory"

    def previous(self) -> str | None:
        """Regresses index without looping. Returns an alert string if blocked."""
        if not self.files:
            return "No directory active"

        if self.current_index > 0:
            self.current_index -= 1
            self.hydrate_current_image()
            return None
        else:
            return "First image of directory"

    # -------------------------------------------------------------
    # ⚡ AUTOMATED HARDWARE CACHE PIPELINE
    # -------------------------------------------------------------
    def hydrate_current_image(self) -> bool:
        """
        Bakes data from CPU space (PIL) straight into GPU VRAM space (QPixmap) once.
        Forces an immediate memory-load insulation to clear operating system file locks.
        """
        if self.current_index == -1 or not self.files:
            self.close_session()
            return False

        try:
            current_path = self.files[self.current_index]

            # 1. Read file and immediately unlock it from the operating system
            self.pil_image = Image.open(current_path)
            self.pil_image.load()  # Crucial: Forces immediate RAM copy so the disk file stays free

            # Record original, unrotated raw source tracking metrics
            self.width, self.height = self.pil_image.size

            # 2. Extract JPEG grid attributes using your existing image processor engine

            self.is_true_jpeg = ImageProcessor.is_true_jpeg(current_path)

            # 3. Convert and cache the unscaled hardware texture into memory securely
            self._qimg_ref = ImageQt(self.pil_image)
            self.master_pixmap = QPixmap.fromImage(self._qimg_ref)
            return True

        except Exception as e:
            print(
                f"[SESSION ERROR] Failed to automatically hydrate image memory cache maps: {e}"
            )
            return False

    def close_session(self):
        """Safely purges all tracking references and clear application RAM buffers completely."""
        self.folder_path = None
        self.files = []
        self.current_index = -1
        self.pil_image = None
        self.master_pixmap = None
        self._qimg_ref = None
        self.current_rotation_angle = 0
        self.is_true_jpeg = False
        self.width = 0
        self.height = 0

    # -------------------------------------------------------------
    # 🔍 LEAN READ-ONLY CONVENIENCE REAL-TIME PROPERTIES
    # -------------------------------------------------------------
    @property
    def has_active_image(self) -> bool:
        """Returns True if the current session contains loaded valid files."""
        return self.current_index != -1 and bool(self.files)

    @property
    def current_path(self) -> Path | None:
        """Returns the complete Path object of the active on-screen file."""
        return self.files[self.current_index] if self.has_active_image else None

    @property
    def current_name(self) -> str:
        """Returns only the filename string (e.g. 'photo.jpg') of the active file."""
        return self.files[self.current_index].name if self.has_active_image else ""

    @property
    def index_string(self) -> str:
        """Returns a formatted index tracker string (e.g. '[1/45]') for direct UI rendering."""
        return (
            f"[{self.current_index + 1}/{len(self.files)}]"
            if self.has_active_image
            else ""
        )
