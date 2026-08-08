from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from config import ui_constants
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
    — pass LossLessCropApp.settings straight in. It's a plain dataclass, not a
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
        self.blacklist: set[Path] = set()

        self.image_model.file_corrupted.connect(self.blacklist_and_skip)
        self.image_model.image_changed.connect(self._on_image_changed)

    # -------------------------------------------------------------
    # DIRECTORY WORKSPACE NAVIGATION
    # -------------------------------------------------------------
    def load_folder(
        self, folder_path: str, valid_files: list[Path], target_filename: str = None
    ) -> bool:
        self.blacklist.clear()
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
            return ui_constants.translate_constant(
                ui_constants.NOTIFICATION_NO_ACTIVE_DIRECTORY
            )
        if self.current_index < len(self.files) - 1:
            self.current_index += 1
            self.hydrate_current_image()
            return None
        # --- EDGE CASE SHIELD (At the Last File / Single File left) ---
        # User is trying to press 'Next' but index cannot advance. Check if file was deleted!
        if not self.files[self.current_index].exists():
            self.image_model.file_deleted.emit()  # Trigger hard folder reload
            return ui_constants.translate_constant(
                ui_constants.NOTIFICATION_FILE_MISSING
            )

        return ui_constants.translate_constant(ui_constants.NOTIFICATION_LAST_IMAGE)

    def previous(self) -> str | None:
        if not self.files:
            return ui_constants.translate_constant(
                ui_constants.NOTIFICATION_NO_ACTIVE_DIRECTORY
            )
        if self.current_index > 0:
            self.current_index -= 1
            self.hydrate_current_image()
            return None

        # --- EDGE CASE SHIELD (At the First File / Single File left) ---
        # User is trying to press 'Prev' but index cannot advance. Check if file was deleted!
        if not self.files[self.current_index].exists():
            self.image_model.file_deleted.emit()  # Trigger hard folder reload
            return ui_constants.translate_constant(
                ui_constants.NOTIFICATION_FILE_MISSING
            )

        return ui_constants.translate_constant(ui_constants.NOTIFICATION_FIRST_IMAGE)

    def hydrate_current_image(self) -> bool:
        if self.current_index == -1 or not self.files:
            self.close_session()
            return False
        return self.image_model.load(self.files[self.current_index])

    # -------------------------------------------------------------
    # THE SYNC CHAIN
    # -------------------------------------------------------------
    def _on_image_changed(self) -> None:
        """Fires every time ImageModel finishes hydrating a new file — a
        navigation, a fresh folder load, or an overwrite-crop reload. Does
        NOT fire on rotation (that's rotation_changed, a separate signal) —
        rotating shouldn't touch the crop selection at all.

        This only decides whether the selection survives at all.
        Previously this also tried to fit the old source_pixel_rect into
        the new image's bounds (clamp_to_bounds) — that's gone; see
        CropModel's docstring for why, and SelectionManager.sync_view_from_model()
        for where that refresh correctly happens now, once there's an
        actual repainted viewport to compute against."""
        if not self.crop_settings.conserve_selection:
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
        harmless, so LossLessCropApp doesn't need to branch on which case it's
        in, it can just always call this after a non-overwrite crop."""
        if not self.crop_settings.conserve_selection:
            self.crop_model.clear()

    def blacklist_and_skip(self, broken_path: Path):
        """Instantly drops a corrupt file from memory and steps forward."""
        self.blacklist.add(broken_path)

        if broken_path in self.files:
            self.files.remove(broken_path)

        # If the folder has run completely dry of uncorrupted files
        if not self.files:
            self.close_session()
            self.workspace_changed.emit()
            return

        # Ensure index isn't pointing out of bounds after removal
        if self.current_index >= len(self.files):
            self.current_index = len(self.files) - 1

        # Step instantly over the bad file to the next one in memory
        self.hydrate_current_image()

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
