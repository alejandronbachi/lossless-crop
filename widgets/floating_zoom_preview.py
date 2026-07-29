import logging

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class FloatingZoomPreview(QWidget):
    def __init__(self, parent_window):
        super().__init__(None)

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.main_app = parent_window
        self.master_pixmap = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_canvas = QLabel()
        self.lbl_canvas.setStyleSheet(
            "background-color: #000000; border: 2px solid #4a6fa5;"
        )
        self.lbl_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_canvas)

        self.setMinimumSize(150, 150)
        self.resize(250, 250)

        # Tracking states
        self.drag_start_global = QPoint()
        self.initial_window_geom = QRect()
        self.is_resizing = False
        self.is_moving = False

    #  Accept the live texture reference straight from the caller parameters
    def refresh_scaled_preview_live(
        self, current_pixmap, fit_enabled, crop_box_pil_coords: tuple
    ):
        """Hardware-accelerated slice and scale directly inside VRAM (Instant)."""
        # Read directly from the incoming texture parameter instead of self.master_pixmap
        if current_pixmap is None or current_pixmap.isNull():
            self.lbl_canvas.clear()
            return

        try:
            left, top, right, bottom = crop_box_pil_coords
            width = right - left
            height = bottom - top

            if width <= 0 or height <= 0:
                return

            # 1. Define target rectangle matching full high-res image pixels
            target_rect = QRect(int(left), int(top), int(width), int(height))

            # 2. ⚡ INSTANT VRAM TEXTURE COPY (Slices directly out of the active image memory!)
            cropped_pixmap = current_pixmap.copy(target_rect)

            current_window_size = self.size()
            if current_window_size.width() <= 0 or current_window_size.height() <= 0:
                return

            # 3. Scale the sub-section to fit HUD view layout rules
            aspect_mode = (
                Qt.AspectRatioMode.KeepAspectRatio
                if fit_enabled
                else Qt.AspectRatioMode.KeepAspectRatioByExpanding
            )

            scaled_pixmap = cropped_pixmap.scaled(
                current_window_size,
                aspect_mode,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.lbl_canvas.setPixmap(scaled_pixmap)

        except Exception as e:
            logger.error("[HUD INTERCEPT] GPU Render pipeline block: %s", e)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        #  Instead of forcing an immediate heavy update,
        # tell the main app's lazy engine to redraw the frame on its next 16ms tick!
        if hasattr(self, "main_app") and hasattr(self.main_app, "status_manager"):
            self.main_app.status_manager.invalidate_ui_state()

    # =================================================================
    # 🖱️ FINALIZED COHESIVE INPUT MAPS: LEFT = RESIZE, RIGHT = MOVE ANYWHERE
    # =================================================================
    def mousePressEvent(self, event):
        # Capture absolute global starting anchors to prevent tracking jitter
        self.drag_start_global = event.globalPosition().toPoint()
        self.initial_window_geom = self.geometry()

        if event.button() == Qt.MouseButton.LeftButton:
            # 🌟 MATCHED COHESION: Left click handles resizing!
            self.is_resizing = True
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            # 🌟 MATCHED COHESION: Right click handles moving the position!
            self.is_moving = True
            event.accept()

    def mouseMoveEvent(self, event):
        if not event.buttons():
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        current_global_pos = event.globalPosition().toPoint()
        delta = current_global_pos - self.drag_start_global

        # 🌟 MATCHED COHESION: LEFT-CLICK DRAG TO RESIZE (Expands toward drag direction)
        if self.is_resizing and (event.buttons() == Qt.MouseButton.LeftButton):
            new_w = max(
                self.minimumWidth(), self.initial_window_geom.width() + delta.x()
            )
            new_h = max(
                self.minimumHeight(), self.initial_window_geom.height() + delta.y()
            )
            self.resize(new_w, new_h)
            event.accept()

        # 🌟 MATCHED COHESION: RIGHT-CLICK DRAG TO MOVE ANYWHERE
        elif self.is_moving and (event.buttons() == Qt.MouseButton.RightButton):
            target_x = self.initial_window_geom.x() + delta.x()
            target_y = self.initial_window_geom.y() + delta.y()
            self.move(target_x, target_y)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.is_resizing = False
        self.is_moving = False
        event.accept()

    def mouseDoubleClickEvent(self, event):
        # 🌟 MATCHED COHESION: Double right-click to close (so double-left doesn't misfire during resizing)
        if event.button() == Qt.MouseButton.RightButton:
            self.hide()
            #  Bulletproof Guard: Check that the checkbox widget object actually exists
            if (
                hasattr(self.main_app, "cfg_show_preview")
                and self.main_app.cfg_show_preview is not None
            ):
                self.main_app.cfg_show_preview.setChecked(False)
            event.accept()

    def keyPressEvent(self, event):
        """Listens for specific keystrokes when the preview window has active focus."""
        # 🌟 CLOSE ON ESCAPE: If the user hits Esc, cleanly dismiss the HUD panel
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_P):
            self.hide()

            # Uncheck the matching drawer checkbox in the main window for sync consistency
            if (
                hasattr(self.main_app, "cfg_show_preview")
                and self.main_app.cfg_show_preview is not None
                and self.main_app.cfg_show_preview
            ):
                self.main_app.cfg_show_preview.setChecked(False)

            event.accept()
        else:
            super().keyPressEvent(event)
