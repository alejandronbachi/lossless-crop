from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPen, QPixmap

from config import app_constants, ui_constants
from managers import theme_manager
from managers.crop_geometry_engine import CropGeometryEngine
from managers.image_session import ImageSession
from managers.selection_overlay_renderer import SelectionOverlayRenderer

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
        image_session: ImageSession,
        selection_manager,
        status_manager,
        image_display_container,
        zoom_hud,
        crop_box_selector,
        spin_width,
        spin_height,
        combo_ratio,
        chk_preserve,
        cfg_show_preview,
        cfg_fit_preview,
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
        self.chk_preserve = chk_preserve
        self.cfg_show_preview = cfg_show_preview
        self.cfg_fit_preview = cfg_fit_preview
        self.viewport_factory = viewport_factory
        self._updating_spinboxes = False
        self._selection_overlay = SelectionOverlayRenderer(selection_manager)
        self._selection_overlay.blur_changed.connect(self.repaint_selection_overlay)

    def load_image_to_viewport(self):
        if not self.image_session.has_active_image:
            self.status_manager.set_empty_workspace_state()
            return

        self.refresh_display_canvas()
        self.sync_workspace_after_loading_image()

    def sync_workspace_after_loading_image(self):
        if self.zoom_hud is not None:
            self.zoom_hud.master_pixmap = self.image_session.master_pixmap

            # Ensure the selection box stays inside the new canvas, otherwise move it to the center of the image
            if (
                self.chk_preserve.isChecked()
                and self.selection_manager.selector.geometry()
            ):
                adjusted_rect = CropGeometryEngine.constrain_and_slide_rect_to_pixmap(
                    self.selection_manager.selector.geometry(),
                    self.selection_manager._current_viewport(),
                )

                # Apply it to your selector UI element
                self.selection_manager.selector.setGeometry(adjusted_rect)
                self.selection_manager.last_crop_geometry = adjusted_rect

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
            self._selection_overlay.set_base_pixmap(None)
            icon_path = (
                app_constants.APP_ROOT_DIR
                / ui_constants.FOLDER_ASSETS
                / ui_constants.FOLDER_ICONS
                / ui_constants.ICON_FILENAME
            )
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

        # -----------------------------------------------------------------
        # Enforce alpha format safety & draw a true canvas divider line
        # -----------------------------------------------------------------

        # 1. Strip out any accidental solid scaling background fills
        alpha_img = scaled_pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        scaled_pixmap = QPixmap.fromImage(alpha_img)

        # 2. Build a drawing layer to safely inject our visual border frame
        bordered_pixmap = QPixmap(scaled_pixmap.size())
        bordered_pixmap.fill(
            QColor(Qt.GlobalColor.transparent)
        )  # Maintain transparency

        painter = QPainter(bordered_pixmap)
        painter.drawPixmap(0, 0, scaled_pixmap)  # Paint the image pixels first

        # -----------------------------------------------------------------
        # FIXED: Changed Pen Style from SolidLine to DashLine
        # -----------------------------------------------------------------
        grid_color = theme_manager.get_color("@CANVAS_GRID")
        pen = QPen(QColor(grid_color), 1)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)

        # Draw the frame precisely tracing the image's layout edges
        painter.drawRect(
            0, 0, bordered_pixmap.width() - 1, bordered_pixmap.height() - 1
        )
        painter.end()

        scaled_pixmap = bordered_pixmap
        # Baseline: identical to today's behavior when there's no selection.
        self.image_display_container.setPixmap(scaled_pixmap)
        # Feed the fresh frame to the blur-mask renderer and repaint the
        # selection cutout on top of it, if a selection is currently active.
        self._selection_overlay.set_base_pixmap(scaled_pixmap)
        self.repaint_selection_overlay()

    def _selection_rect_in_pixmap_space(self) -> QRect | None:
        """Same label->pixmap centering translation SelectionManager already
        performs inline in update_draw()/apply_target_dimensions(): the
        selector's geometry is in image_display_container's (label)
        coordinate space, and the base pixmap is centered inside that label
        whenever the label is larger than the pixmap. Subtract that offset to
        land in the pixmap's own (0,0)-origin space, which is what
        SelectionOverlayRenderer composites against."""
        selector = self.selection_manager.selector
        pixmap = self.image_display_container.pixmap()
        if selector.isHidden() or not pixmap:
            return None

        lbl_w = self.image_display_container.width()
        lbl_h = self.image_display_container.height()
        pix_w, pix_h = pixmap.width(), pixmap.height()
        offset_x, offset_y = (lbl_w - pix_w) // 2, (lbl_h - pix_h) // 2

        return selector.geometry().translated(-offset_x, -offset_y)

    def repaint_selection_overlay(self):
        """Recomposites the canvas pixmap around the live selection rect.
        Wired as the single repaint hook for every selection-geometry change
        (see the on_selection_changed callback passed into SelectionManager
        in LossLessCropApp.init_ui) -- mouse drag, move, spinbox resize,
        snap, ratio changes, and model-sync all funnel through here already,
        so this method needs no other call sites."""
        if not self.image_session.has_active_image:
            return

        rect = self._selection_rect_in_pixmap_space()
        composite = self._selection_overlay.render(rect)
        if composite is not None:
            self.image_display_container.setPixmap(composite)

    def get_current_forced_ratio(self):
        """Returns the active aspect ratio multiplier float based on toolbar combo selections."""
        dims = (
            (self.image_session.width, self.image_session.height)
            if self.image_session.has_active_image
            else None
        )
        return CropGeometryEngine.resolve_aspect_ratio(
            self.combo_ratio.currentText(), dims
        )

    def update_resolution_metrics_display(self):
        """Updates the spinboxes and status bar metrics based on the current selection box,
        ensuring strict aspect ratio alignment to prevent visual mismatches.
        """
        if (
            self._updating_spinboxes
            or not self.image_session.has_active_image
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
        if self._updating_spinboxes or not self.image_session.has_active_image:
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
        if self._updating_spinboxes or not self.image_session.has_active_image:
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
        # 1. Guard: Check if the HUD should be active at all
        if not self._is_hud_activation_allowed():
            self._clear_zoom_hud_completely()
            return

        # 2. Guard: Validate UI elements and dimensions
        box_rect = self.crop_box_selector.geometry()
        pixmap = self.image_display_container.pixmap()
        if not pixmap or box_rect.width() <= 5 or box_rect.height() <= 5:
            self._clear_zoom_hud_canvas_only()
            return

        # 3. Calculate and clamp boundaries
        pil_coords = self._calculate_clamped_crop_coords(box_rect, pixmap)

        # 4. Final Guard & Execution: Update HUD if coordinates are valid
        if pil_coords and self.zoom_hud is not None:
            self.zoom_hud.refresh_scaled_preview_live(
                self.image_session.master_pixmap,
                self.cfg_fit_preview.isChecked(),
                pil_coords,
            )
        else:
            self._clear_zoom_hud_canvas_only()

    # --- Extracted Helper Methods ---

    def _is_hud_activation_allowed(self) -> bool:
        """Evaluates the core business rules for HUD visibility."""
        return (
            self.cfg_show_preview.isChecked()
            and not self.crop_box_selector.isHidden()
            and self.image_session.has_active_image
        )

    def _calculate_clamped_crop_coords(self, box_rect, pixmap) -> tuple | None:
        """Handles mapping viewport coordinates back to original source pixels."""
        viewport = self.viewport_factory(pixmap)
        source_rect = CropGeometryEngine.screen_rect_to_source_rect(
            box_rect,
            viewport,
            lossless=False,
            ratio_label=self.combo_ratio.currentText(),
        )

        crop_left, crop_top = source_rect.x(), source_rect.y()
        crop_right = crop_left + source_rect.width()
        crop_bottom = crop_top + source_rect.height()

        if crop_right <= crop_left or crop_bottom <= crop_top:
            return None

        src_w, src_h = self.image_session.width, self.image_session.height

        # Clamping boundaries safely
        clamped_left = max(0, min(crop_left, src_w - 1))
        clamped_top = max(0, min(crop_top, src_h - 1))
        clamped_right = max(clamped_left + 1, min(crop_right, src_w))
        clamped_bottom = max(clamped_top + 1, min(crop_bottom, src_h))

        return (clamped_left, clamped_top, clamped_right, clamped_bottom)

    def _clear_zoom_hud_completely(self):
        """Resets master pixmap and clears the HUD canvas."""
        if self.zoom_hud is not None:
            self.zoom_hud.master_pixmap = None
            self.zoom_hud.lbl_canvas.clear()

    def _clear_zoom_hud_canvas_only(self):
        """Clears just the visual preview without flushing the master pixmap cache."""
        if self.zoom_hud is not None:
            self.zoom_hud.lbl_canvas.clear()
