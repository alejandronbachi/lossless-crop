from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from models.crop_model import CropModel
from models.image_model import ImageModel


class ImageSession(QObject):
    """The Parent Context / Orchestrator from the architecture doc. Owns
    folder-navigation state plus exactly one ImageModel and one CropModel for
    'whatever file is active right now'. This is where the Sync Chain lives:
    it listens for ImageModel.image_changed and, based on
    crop_settings.conserve_selection, tells CropModel to either re-clamp or
    flush.

    crop_settings is your existing AppSettings instance (models/app_settings.py)
    — pass FastCropApp.settings straight in. It's a plain dataclass, not a
    QObject, and that's fine here: this class only ever reads
    conserve_selection at the moment a new image loads, it doesn't need to
    react live to the checkbox changing mid-session. Bind
    chk_preserve.toggled to write into that same instance (see integration
    notes) instead of this class reading the checkbox itself.
    """

    workspace_changed = pyqtSignal()  # folder loaded/closed, or index moved

    def __init__(self, crop_settings, parent=None):
        super().__init__(parent)
        self.crop_settings = crop_settings

        self.folder_path: Path | None = None
        self.files: list[Path] = []
        self.current_index: int = -1

        self.image_model = ImageModel(self)
        self.crop_model = CropModel(self)

        self.image_model.image_changed.connect(self._on_image_changed)

    # -------------------------------------------------------------
    # DIRECTORY WORKSPACE NAVIGATION
    # -------------------------------------------------------------
    def load_folder(
        self, folder_path: str, valid_files: list[Path], target_filename: str = None
    ) -> bool:
        if not valid_files:
            self.close_session()
            return False

        self.folder_path = Path(folder_path)
        self.files = valid_files

        if target_filename:
            matched = next(
                (i for i, p in enumerate(self.files) if p.name == target_filename), 0
            )
            self.current_index = matched
        else:
            self.current_index = 0

        return self.hydrate_current_image()

    def next(self) -> str | None:
        if not self.files:
            return "No directory active"
        if self.current_index < len(self.files) - 1:
            self.current_index += 1
            self.hydrate_current_image()
            return None
        return "Last image of directory"

    def previous(self) -> str | None:
        if not self.files:
            return "No directory active"
        if self.current_index > 0:
            self.current_index -= 1
            self.hydrate_current_image()
            return None
        return "First image of directory"

    def hydrate_current_image(self) -> bool:
        if self.current_index == -1 or not self.files:
            self.close_session()
            return False
        return self.image_model.load(self.files[self.current_index])

    # -------------------------------------------------------------
    # THE SYNC CHAIN
    # -------------------------------------------------------------
    def _on_image_changed(self) -> None:
        """Fires every time ImageModel finishes hydrating a new file. Does
        NOT fire on rotation (that's rotation_changed, a separate signal) —
        rotating shouldn't touch the crop selection at all."""
        if self.crop_settings.conserve_selection:
            self.crop_model.clamp_to_bounds(self.image_model.width, self.image_model.height)
        else:
            self.crop_model.clear()
        self.workspace_changed.emit()

    def close_session(self) -> None:
        self.folder_path = None
        self.files = []
        self.current_index = -1
        self.image_model.clear()
        self.crop_model.clear()

    def apply_post_crop_selection_policy(self) -> None:
        """Call after a crop completes WITHOUT an image swap (overwrite is
        off, so hydrate_current_image() never ran and the Sync Chain never
        fired). When a swap DID happen, this is a no-op to call again —
        harmless, so FastCropApp doesn't need to branch on which case it's
        in, it can just always call this after a non-overwrite crop."""
        if not self.crop_settings.conserve_selection:
            self.crop_model.clear()

    # -------------------------------------------------------------
    # READ-ONLY CONVENIENCE PROPERTIES
    # -------------------------------------------------------------
    @property
    def has_active_image(self) -> bool:
        return self.current_index != -1 and bool(self.files)

    @property
    def current_path(self) -> Path | None:
        return self.files[self.current_index] if self.has_active_image else None

    @property
    def current_name(self) -> str:
        return self.files[self.current_index].name if self.has_active_image else ""

    @property
    def index_string(self) -> str:
        return (
            f"[{self.current_index + 1}/{len(self.files)}]"
            if self.has_active_image
            else ""
        )

    # -- back-compat passthroughs -------------------------------------------
    # Lets you migrate call sites gradually: anything reading
    # image_session.master_pixmap / .width / .height / .is_true_jpeg /
    # .current_rotation_angle keeps working unchanged. New code should prefer
    # image_session.image_model.<x> directly and stop going through these.
    @property
    def pil_image(self):
        return self.image_model.pil_image

    @property
    def master_pixmap(self):
        return self.image_model.pixmap

    @property
    def width(self):
        return self.image_model.width

    @property
    def height(self):
        return self.image_model.height

    @property
    def is_true_jpeg(self):
        return self.image_model.is_true_jpeg

    @property
    def current_rotation_angle(self):
        return self.image_model.rotation_angle
