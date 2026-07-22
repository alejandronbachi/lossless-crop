from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

# Check for Pillow availability
try:
    from PIL import Image
    from PIL.ImageQt import ImageQt

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


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
        self.cached_crop_slice = None

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

    def update_zoom_payload(self, pil_crop_slice):
        self.cached_crop_slice = pil_crop_slice
        self.refresh_scaled_image()

    def refresh_scaled_image(self):
        if not self.cached_crop_slice:
            self.lbl_canvas.clear()
            return
        try:
            if PILLOW_AVAILABLE:
                self._current_qimg = ImageQt(self.cached_crop_slice)
                pixmap = QPixmap.fromImage(self._current_qimg)
            else:
                print("Pillow not available not possible to use preview hud")

            current_window_size = self.size()
            if current_window_size.width() <= 0 or current_window_size.height() <= 0:
                return

            scaled_pixmap = pixmap.scaled(
                current_window_size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.lbl_canvas.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"[HUD INTERCEPT] Render pipeline block: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.is_resizing and hasattr(self.main_app, "update_zoom_hud_payload"):
            self.main_app.update_zoom_hud_payload()
        else:
            self.refresh_scaled_image()

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
            if hasattr(self.main_app, "cfg_show_preview"):
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
                and self.main_app.cfg_show_preview
            ):
                self.main_app.cfg_show_preview.setChecked(False)

            event.accept()
        else:
            super().keyPressEvent(event)
