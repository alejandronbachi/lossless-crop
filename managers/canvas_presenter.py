from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from config import app_constants, ui_constants
from managers.crop_geometry_engine import CropGeometryEngine

# Check for Pillow availability
try:
    from PIL import Image

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class CanvasPresenter:
    """Presenter responsible for managing viewport rendering, canvas refreshing,
    workspace synchronization after loading images, resolution metrics display updates,
    zoom HUD payload calculations, and spinbox-to-canvas synchronization with re-entrancy protection.
    """

    def __init__(
        self,
        image_session,
        selection_manager,
        status_manager,
        image_display_container,
        zoom_hud,
        crop_box_selector,
        spin_width,
        spin_height,
        combo_ratio,
        cfg_show_preview,
        viewport_factory,
    ):
        self.image_session = image_session
        self.selection_manager = selection_manager
        self.status_manager = status_manager
        self.image_display_container = image_display_container
        self.zoom_hud = zoom_hud
        self.crop_box_selector = crop_box_selector
        self.spin_width = spin_width
        self.spin_height = spin_height
        self.combo_ratio = combo_ratio
        self.cfg_show_preview = cfg_show_preview
        self.viewport_factory = viewport_factory
        self._updating_spinboxes = False

    def load_image_to_viewport(self):
        if not self.image_session.has_active_image:
            self.status_manager.set_empty_workspace_state()
            return

        self.refresh_display_canvas()
        self.sync_workspace_after_loading_image()

    def sync_workspace_after_loading_image(self):
        if self.zoom_hud is not None:
            self.zoom_hud.master_pixmap = self.image_session.master_pixmap

        self.selection_manager.sync_view_from_model()

        self.status_manager.reposition_commands_overlay()
        self.status_manager.sync_drawer_visibility_rules()
        self.status_manager.invalidate_ui_state()

    def refresh_display_canvas(self):
        """Handles fast memory-side hardware viewport scaling from session data."""
        if (
            not self.image_session.master_pixmap
            or self.image_session.master_pixmap.isNull()
        ):
            icon_path = app_constants.APP_ROOT_DIR / ui_constants.ICON_FILENAME
            if icon_path.exists():
                logo_pixmap = QPixmap(str(icon_path))
                scaled_logo = logo_pixmap.scaled(
                    512,
                    512,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.image_display_container.setPixmap(scaled_logo)
            else:
                self.image_display_container.clear()
            return

        container_size = self.image_display_container.size()
        if container_size.width() <= 0 or container_size.height() <= 0:
            return

        scaled_pixmap = self.image_session.master_pixmap.scaled(
            container_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_display_container.setPixmap(scaled_pixmap)

    def get_current_forced_ratio(self):
        """Returns the active aspect ratio multiplier float based on toolbar combo selections."""
        return CropGeometryEngine.resolve_aspect_ratio(self.combo_ratio.currentText())

    def update_resolution_metrics_display(self):
        """Updates the spinboxes and status bar metrics based on the current selection box,
        ensuring strict aspect ratio alignment to prevent visual mismatches.
        """
        if (
            self._updating_spinboxes
            or not self.image_session.has_active_image
            or not self.image_session.pil_image
            or self.crop_box_selector.isHidden()
        ):
            return

        pixmap = self.image_display_container.pixmap()
        if not pixmap:
            return

        crop_model = self.selection_manager.crop_model
        if not crop_model.has_selection:
            return
        source_rect = crop_model.source_pixel_rect

        # Safely push the matching dimensions to the spinboxes without triggering loops
        self._updating_spinboxes = True
        try:
            self.spin_width.setValue(source_rect.width())
            self.spin_height.setValue(source_rect.height())
        finally:
            self._updating_spinboxes = False

    def on_spin_width_changed(self, value=None):
        """Triggers when width spinbox is adjusted manually via arrows or keystrokes."""
        if (
            self._updating_spinboxes
            or not self.image_session.has_active_image
            or not self.image_session.pil_image
        ):
            return

        if value is None:
            value = self.spin_width.value()

        ratio = self.get_current_forced_ratio()
        if ratio is not None:
            self._updating_spinboxes = True
            try:
                calculated_height = int(round(value / ratio))
                calculated_height = min(calculated_height, self.image_session.height)
                self.spin_height.setValue(calculated_height)
            finally:
                self._updating_spinboxes = False

        self.apply_spinbox_dimensions_to_canvas()

    def on_spin_height_changed(self, value=None):
        """Triggers when height spinbox is adjusted manually via arrows or keystrokes."""
        if (
            self._updating_spinboxes
            or not self.image_session.has_active_image
            or not self.image_session.pil_image
        ):
            return
        if value is None:
            value = self.spin_height.value()

        ratio = self.get_current_forced_ratio()
        if ratio is not None:
            self._updating_spinboxes = True
            try:
                calculated_width = int(round(value * ratio))
                calculated_width = min(calculated_width, self.image_session.width)
                self.spin_width.setValue(calculated_width)
            finally:
                self._updating_spinboxes = False

        self.apply_spinbox_dimensions_to_canvas()

    def apply_spinbox_dimensions_to_canvas(self):
        self._updating_spinboxes = True
        try:
            tw, th, applied = self.selection_manager.apply_target_dimensions(
                self.spin_width.value(), self.spin_height.value()
            )
            # Only update spinboxes if lossless grid-snapping changed the dimensions
            if (tw, th) != (self.spin_width.value(), self.spin_height.value()):
                self.spin_width.setValue(tw)
                self.spin_height.setValue(th)
        finally:
            self._updating_spinboxes = False

        if applied and self.zoom_hud is not None:
            self.update_zoom_hud_payload()

    def update_zoom_hud_payload(self):
        """Calculates high-res coordinates and triggers instant GPU-side cropping."""
        if (
            not PILLOW_AVAILABLE
            or not self.cfg_show_preview.isChecked()
            or self.crop_box_selector.isHidden()
            or not self.image_session.has_active_image
        ):
            if self.zoom_hud is not None:
                self.zoom_hud.master_pixmap = None
                self.zoom_hud.lbl_canvas.clear()
            return

        box_rect = self.crop_box_selector.geometry()
        pixmap = self.image_display_container.pixmap()

        if pixmap and box_rect.width() > 5 and box_rect.height() > 5:
            src_w, src_h = self.image_session.width, self.image_session.height
            viewport = self.viewport_factory(pixmap)

            source_rect = CropGeometryEngine.screen_rect_to_source_rect(
                box_rect,
                viewport,
                lossless=False,
                ratio_label=self.combo_ratio.currentText(),
            )

            crop_left = source_rect.x()
            crop_top = source_rect.y()
            crop_right = crop_left + source_rect.width()
            crop_bottom = crop_top + source_rect.height()

            if (crop_right > crop_left) and (crop_bottom > crop_top):
                crop_left = max(0, min(crop_left, src_w - 1))
                crop_top = max(0, min(crop_top, src_h - 1))
                crop_right = max(crop_left + 1, min(crop_right, src_w))
                crop_bottom = max(crop_top + 1, min(crop_bottom, src_h))

                pil_coords = (crop_left, crop_top, crop_right, crop_bottom)

                if self.zoom_hud is not None:
                    self.zoom_hud.refresh_scaled_preview_live(
                        self.image_session.master_pixmap, pil_coords
                    )
                return

        if self.zoom_hud is not None:
            self.zoom_hud.lbl_canvas.clear()
