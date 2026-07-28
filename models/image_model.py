from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError
from PIL.ImageQt import ImageQt
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPixmap, QTransform

from managers.image_manager import ImageProcessor


class ImageModel(QObject):
    """The immutable-per-file truth of whatever image is currently in the
    viewport. Replaces the fields that currently live directly on
    ImageSession: master_pixmap, width, height,
    current_rotation_angle, is_true_jpeg.

    ImageSession now OWNS one instance of this and calls .load(path) on
    navigation instead of mutating those five fields on itself. Two knock-on
    fixes come from this split:

    1. Rotation was previously reset only in ImageSession.load_folder(), NOT
       in hydrate_current_image() — so pressing Next/Previous after rotating
       left a stale current_rotation_angle sitting on the session while the
       freshly-loaded pixmap was actually unrotated. .load() below resets it
       unconditionally, every time, because rotation is per-file state.
    2. ImageProcessor.rotate_session_view() was a staticmethod reaching into
       a session object to mutate five of its fields (feature envy) — that
       logic is now a method on the object it actually mutates.
    """

    image_changed = pyqtSignal()  # a new file was hydrated
    rotation_changed = pyqtSignal(int)  # cumulative angle, for HUD/status text
    file_deleted = pyqtSignal()  # Signal for missing files
    file_corrupted = pyqtSignal(Path)  # Signal for bad image files

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path: Path | None = None
        self._qimg_ref: ImageQt | None = None  # blocks C++ GC segfaults
        self._pixmap: QPixmap | None = None
        self._width = 0
        self._height = 0
        self._rotation_angle = 0
        self._is_true_jpeg = False

    # -- read-only state ---------------------------------------------------
    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def pixmap(self) -> QPixmap | None:
        return self._pixmap

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def dimensions(self) -> tuple[int, int]:
        return self._width, self._height

    @property
    def rotation_angle(self) -> int:
        return self._rotation_angle

    @property
    def is_true_jpeg(self) -> bool:
        return self._is_true_jpeg

    @property
    def is_loaded(self) -> bool:
        return self._pixmap is not None and not self._pixmap.isNull()

    # -- mutators ------------------------------------------------------------
    def load(self, path: Path) -> bool:
        """Hydrates this model from disk. Emits image_changed on success —
        that signal is what ImageSession's Sync Chain listens for to decide
        whether CropModel re-clamps or flushes."""
        try:
            with Image.open(path) as pil_image:
                pil_image = Image.open(path)
                pil_image.load()  # force RAM copy so the disk file stays free

                self._path = path

                self._width, self._height = pil_image.size
                self._rotation_angle = 0  # per-file: always resets on a fresh load
                self._is_true_jpeg = ImageProcessor.is_true_jpeg(path)
                self._qimg_ref = ImageQt(pil_image)
                self._pixmap = QPixmap.fromImage(self._qimg_ref)

            self.image_changed.emit()
            return True
        except FileNotFoundError:
            self.file_deleted.emit()
        except UnidentifiedImageError:
            self.file_corrupted.emit(path)
        except Exception as e:
            print(f"[ImageModel] Failed to hydrate '{path}': {e}")
            return False

    def rotate(self, degrees: int = -90) -> int:
        """Rotates the cached VRAM texture and flips width/height bookkeeping
        in one place. Call this instead of ImageProcessor.rotate_session_view().
        Returns the new cumulative angle."""
        if self._pixmap is None:
            return self._rotation_angle

        self._rotation_angle = (self._rotation_angle + degrees) % 360
        self._pixmap = self._pixmap.transformed(QTransform().rotate(degrees))
        self._width, self._height = self._height, self._width

        self.rotation_changed.emit(self._rotation_angle)
        return self._rotation_angle

    def clear(self) -> None:
        self._path = None
        self._qimg_ref = None
        self._pixmap = None
        self._width = 0
        self._height = 0
        self._rotation_angle = 0
        self._is_true_jpeg = False
        self.image_changed.emit()
