import ctypes
import sys
from pathlib import Path

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    QTimer,
)
from PyQt6.QtGui import QIcon, QKeyEvent, QPixmap, QResizeEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QRubberBand,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from config import app_constants, ui_constants
from managers.crop_execution_manager import CropExecutionController
from managers.crop_geometry_engine import CropGeometryEngine, ViewportGeometry
from managers.file_manager import FileManager
from managers.image_manager import ImageProcessor
from managers.image_session import ImageSession
from managers.settings_manager import SettingsManager
from managers.status_manager import StatusManager
from models.app_settings import AppSettings
from widgets.control_toolbar import ControlToolbar
from widgets.floating_zoom_preview import FloatingZoomPreview
from widgets.infor_bar import InfoBar
from widgets.settings_drawer import SettingsDrawer

# Check for Pillow availability
try:
    from PIL import Image
    from PIL.ImageQt import ImageQt

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class FastCropApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LossLess Crop")
        self.resize(900, 700)
        self.settings_manager = SettingsManager()
        self.settings = AppSettings()
        self.file_manager = FileManager(self.settings_manager)
        self.image_manager = ImageProcessor()
        self.crop_executor = CropExecutionController(self.image_manager)
        #  Create a single-shot timer for layout throttling
        self.resize_throttle_timer = QTimer(self)
        self.resize_throttle_timer.setSingleShot(True)
        self.resize_throttle_timer.timeout.connect(self.execute_deferred_resize_recalc)

        #  Core Application Icon Registry Initialization
        icon_path = app_constants.APP_ROOT_DIR / ui_constants.ICON_FILENAME
        if icon_path.exists():
            # Convert Path to str since some older PyQt versions prefer string primitives for UI assets
            self.setWindowIcon(QIcon(str(icon_path)))  # Sets Title Bar Icon

        self.setStyleSheet(
            self.file_manager.load_asset(
                ui_constants.STYLE_MAIN, ui_constants.FOLDER_STYLES
            )
        )

        # Image Pipeline Management Variables
        self.image_session = ImageSession()

        # Bounding Box Memory Settings
        self.last_crop_geometry = None
        self.is_moving_box = False

        # Initialize User Interface
        self.init_ui()
        self.zoom_hud = FloatingZoomPreview(self)
        self.load_application_state()

    def init_ui(self):
        # Master Structural Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # -------------------------------------------------------------
        # TOP SYSTEM TOOLBAR
        # -------------------------------------------------------------
        self.control_toolbar = ControlToolbar(
            parent=self,
            image_manager=self.image_manager,
            file_manager=self.file_manager,
            ui_constants=ui_constants,
            pillow_available=PILLOW_AVAILABLE,
        )
        # Add the frame directly to your main layout tree channels
        self.main_layout.addWidget(self.control_toolbar)
        # -------------------------------------------------------------
        # MIDDLE VISUAL DISPLAY CANVAS PANEL
        # -------------------------------------------------------------
        self.build_main_canvas()
        # -------------------------------------------------------------
        # BOTTOM INFO BAR LAYOUT PANEL (Split Structure)
        # -------------------------------------------------------------
        self.info_bar_widget = InfoBar(self)
        self.main_layout.addWidget(self.info_bar_widget)
        # -------------------------------------------------------------
        #  INITIALIZE ORCHESTRATION & FLOATING OVERLAYS
        # -------------------------------------------------------------
        # The StatusManager handles creating your overlays (Splash, Commands, Toast)
        self.status_manager = StatusManager(
            main_app=self,
            canvas_container=self.image_display_container,
            info_bar_widget=self.info_bar_widget,
            file_manager=self.file_manager,
            ui_constants=ui_constants,
        )
        # -------------------------------------------------------------
        # SIDE DRAWER
        # -------------------------------------------------------------
        self.settings_drawer = SettingsDrawer(self, self.file_manager)
        # Maintain your legacy geometry tracking shortcuts
        self.drawer = self.settings_drawer
        self.drawer_width = self.settings_drawer.drawer_width
        self.drawer_is_open = False

        # Interactive Selection Component Initialization
        self.crop_box_selector = QRubberBand(
            QRubberBand.Shape.Rectangle, self.image_display_container
        )
        self.drag_start_origin = QPoint()

    def load_image_to_viewport(self):
        # 🚀 CHANGE ONLY: Evaluate session status instead of loose variables
        if not self.image_session.has_active_image:
            self.status_manager.set_empty_workspace_state()
            return

        # Update display views by drawing directly out of the active session context
        self.refresh_display_canvas()
        self.sync_workspace_after_loading_image()

    def sync_workspace_after_loading_image(self):
        # 🚀 CHANGE ONLY: Push the live session VRAM handle directly to the HUD tool!
        if hasattr(self, "zoom_hud"):
            self.zoom_hud.master_pixmap = self.image_session.master_pixmap

        # -----------------------------------------------------------------
        # RE-SYNC WORKSPACE SELECTION LAYER PRESERVATION (STATIONARY SNAP)
        # -----------------------------------------------------------------
        if self.chk_preserve.isChecked() and self.last_crop_geometry:
            if self.determine_if_lossless_active():
                self.last_crop_geometry = self.calculate_snapped_rect(
                    self.last_crop_geometry
                )

            self.crop_box_selector.setGeometry(self.last_crop_geometry)
            self.crop_box_selector.show()
            self.crop_box_selector.raise_()
        else:
            self.crop_box_selector.hide()
            self.last_crop_geometry = None
            if hasattr(self, "ghost_selector") and self.ghost_selector:
                self.ghost_selector.hide()

        # Update status manager system layout overlays
        self.status_manager.reposition_commands_overlay()
        self.status_manager.sync_drawer_visibility_rules()

        self.update_resolution_metrics_display()
        self.status_manager.invalidate_ui_state()

        if hasattr(self, "update_zoom_hud_payload"):
            self.update_zoom_hud_payload()

    def refresh_display_canvas(self):
        """Handles fast memory-side hardware viewport scaling from session data."""

        #  THE WATERMARK LOGO  If no active image session exists, paint the brand logo centerpiece!
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

        # 🚀 CHANGE ONLY: Read straight out of the active session
        scaled_pixmap = self.image_session.master_pixmap.scaled(
            container_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_display_container.setPixmap(scaled_pixmap)

    # -----------------------------------------------------------------
    # MOUSE INTERACTION & ASPECT BOX OVERLAYS
    # -----------------------------------------------------------------
    def on_mouse_press(self, event):

        if self.drawer_is_open:
            # If the user clicks on the image layout while the menu is open, smoothly retract it
            self.toggle_settings_drawer()
            return  # Block the click from drawing a box on this specific tap

        if (
            not self.image_display_container.pixmap()
            or not self.image_session.has_active_image
        ):
            return

        # Hide the commands panel instantly so it doesn't obstruct cropping fields
        self.status_manager.hide_overlays_on_mouse_press()

        if event.button() == Qt.MouseButton.LeftButton:
            # Left Click: Draw a new crop box
            self.drag_start_origin = event.position().toPoint()
            self.crop_box_selector.setGeometry(QRect(self.drag_start_origin, QSize()))
            self.crop_box_selector.show()
            self.is_moving_box = False

        elif event.button() == Qt.MouseButton.RightButton:
            # Right Click: Move the existing crop box if the cursor is inside it
            click_point = event.position().toPoint()
            if (
                not self.crop_box_selector.isHidden()
                and self.crop_box_selector.geometry().contains(click_point)
            ):
                self.is_moving_box = True
                self.drag_start_origin = (
                    click_point  # Track starting point of movement drag
                )
                self.box_start_pos = self.crop_box_selector.geometry().topLeft()
            else:
                self.is_moving_box = False
        self.update_zoom_hud_payload()

    def on_mouse_move(self, event):
        if self.drag_start_origin.isNull():
            return

        current_point = event.position().toPoint()

        use_lossless = self.determine_if_lossless_active()

        # -----------------------------------------------------------------
        # BRANCH A: RIGHT-CLICK DRAG LOGIC (Moving the box smoothly)
        # -----------------------------------------------------------------
        if self.is_moving_box:
            # Calculate the total distance the mouse has moved since the first right-click
            total_mouse_delta = current_point - self.drag_start_origin
            current_geometry = self.crop_box_selector.geometry()

            # Add that total distance to the box's initial starting coordinates
            target_x = self.box_start_pos.x() + total_mouse_delta.x()
            target_y = self.box_start_pos.y() + total_mouse_delta.y()

            # Apply 16x16 grid snap ONLY to the visible layout coordinates
            if use_lossless:
                render_x = round(target_x / 16) * 16
                render_y = round(target_y / 16) * 16
            else:
                render_x = target_x
                render_y = target_y

            # Keep the box inside the display window boundaries safely
            render_x = max(
                0,
                min(
                    render_x,
                    self.image_display_container.width() - current_geometry.width(),
                ),
            )
            render_y = max(
                0,
                min(
                    render_y,
                    self.image_display_container.height() - current_geometry.height(),
                ),
            )

            # Move the widget layout on the screen
            self.crop_box_selector.move(render_x, render_y)
            self.last_crop_geometry = self.crop_box_selector.geometry()
            self.status_manager.invalidate_ui_state()
        # -----------------------------------------------------------------
        # BRANCH B: LEFT-CLICK DRAW LOGIC (Drawing the box)
        # -----------------------------------------------------------------
        else:
            self.handle_left_click_drawing(current_point)

    def on_mouse_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_moving_box:
            self.handle_left_click_release()
        elif event.button() == Qt.MouseButton.RightButton:
            self.is_moving_box = False
            self.drag_start_origin = QPoint()

        self.status_manager.restore_overlays_on_mouse_release()
        # Keep recalculating your numeric scale spinbox fields as normal
        self.update_resolution_metrics_display()

    def on_ratio_changed(self):
        """Instantly morphs the active selection box when the aspect ratio dropdown changes."""
        # Exit early if the selection box is hidden or practically empty
        if self.crop_box_selector.isHidden() or self.crop_box_selector.width() <= 5:
            return

        ratio_type = self.combo_ratio.currentText()
        if ratio_type == "Freeform":
            return  # Freeform allows any shape, so don't alter the current frame

        # Use the current width as the master base and calculate the new height
        current_geom = self.crop_box_selector.geometry()
        new_width = current_geom.width()

        use_lossless = self.determine_if_lossless_active()

        if use_lossless:
            new_width = CropGeometryEngine.snap_to_grid(new_width)
        new_height = CropGeometryEngine.apply_aspect_lock_to_width(
            new_width, ratio_type, use_lossless
        )

        # Build the updated boundary layout
        new_rect = QRect(current_geom.x(), current_geom.y(), new_width, new_height)

        # Apply the new geometry dimensions to the canvas overlay
        self.crop_box_selector.setGeometry(new_rect)
        self.last_crop_geometry = new_rect
        self.crop_box_selector.raise_()
        if hasattr(self, "spin_width") and not self.crop_box_selector.isHidden():
            # Calling this function forces the engine to recalculate the source pixels
            # and push the brand new numbers straight into your toolbar input cells instantly
            self.update_resolution_metrics_display()

    def determine_if_lossless_active(self):
        """A single source of truth to check if Lossless operation is currently legal.
        Validates engine toggle, file extension, and binary file signatures.
        """

        if not self.image_session.has_active_image:
            return False

        # 1. Quick setting check
        if (
            self.combo_engine.currentText() != "Lossless"
            or not self.image_manager.is_lossless_available
        ):
            return False

        return self.image_session.is_true_jpeg

    def _build_viewport_geometry(self, pixmap: QPixmap) -> ViewportGeometry:
        """Snapshots the current label/pixmap/source dimensions into a
        ViewportGeometry for CropGeometryEngine. Call this fresh in every
        handler — pixmap size and label size can both change between calls
        (window resize, image navigation), so the snapshot must not be cached.
        """
        return ViewportGeometry(
            label_width=self.image_display_container.width(),
            label_height=self.image_display_container.height(),
            pixmap_width=pixmap.width(),
            pixmap_height=pixmap.height(),
            source_width=self.image_session.width,
            source_height=self.image_session.height,
        )

    # -----------------------------------------------------------------
    # CROPING ENGINES CALLS
    # -----------------------------------------------------------------
    def process_and_execute_crop(self) -> bool:
        """Coordinates view metrics and dispatches the crop to CropExecutionController,
        which runs the actual jpegtran/Pillow work off the UI thread. Returns True if a
        crop job was *submitted* (not necessarily finished — see on_crop_finished)."""
        if not self.image_session.has_active_image or self.crop_box_selector.isHidden():
            return False

        if self.crop_executor.has_pending_jobs():
            # A previous crop is still writing to disk; don't race a second submission.
            return False

        pixmap = self.image_display_container.pixmap()
        if not pixmap:
            return False

        # 1. Look up data states straight from your unified managers and models
        current_filepath = self.image_session.current_path
        use_lossless = self.determine_if_lossless_active()
        box_rect = self.crop_box_selector.geometry()
        file_ext = current_filepath.suffix.lower()
        ratio_label = self.combo_ratio.currentText()

        # 2. Build the viewport snapshot and constrain the selection to the pixmap bounds
        viewport = self._build_viewport_geometry(pixmap)
        clamped_rect = CropGeometryEngine.clamp_screen_rect_to_pixmap(
            box_rect, viewport
        )

        if clamped_rect.width() <= 0 or clamped_rect.height() <= 0:
            return False

        src_w, src_h = self.image_session.width, self.image_session.height

        # 3. AUTOMATED SAVE PATH ROUTING ENGINE
        if self.chk_overwrite.isChecked():
            output_filepath = str(current_filepath)
        else:
            unique_path = self.file_manager.generate_unique_crop_path(
                self.image_session.folder_path, current_filepath.name
            )
            output_filepath = str(unique_path)

        # 4. COMPUTE GEOMETRIC TARGET CROPS VIA THE SHARED GEOMETRY ENGINE
        if use_lossless:
            source_rect = CropGeometryEngine.screen_rect_to_source_rect(
                box_rect, viewport, lossless=True, ratio_label=ratio_label
            )
            crop_left, crop_top = max(0, source_rect.x()), max(0, source_rect.y())
            crop_width, crop_height = source_rect.width(), source_rect.height()
            crop_right = crop_left + crop_width
            crop_bottom = crop_top + crop_height
        else:
            crop_left = max(0, round(clamped_rect.x() * viewport.scale_x))
            crop_top = max(0, round(clamped_rect.y() * viewport.scale_y))
            crop_width = self.spin_width.value()
            crop_height = self.spin_height.value()
            crop_right = min(src_w, crop_left + crop_width)
            crop_bottom = min(src_h, crop_top + crop_height)

        # 5. CHANNELS DISPATCHER ROUTING
        crop_dimensions_tuple = (crop_width, crop_height, crop_left, crop_top)

        if use_lossless:
            self.image_manager.log_engine_activation(
                "LOSSLESS MODE (jpegtran)",
                current_filepath,
                output_filepath,
                (src_w, src_h),
                crop_dimensions_tuple,
            )
            crop_args = crop_dimensions_tuple
        else:
            self.image_manager.log_engine_activation(
                "PIXEL-PERFECT MODE (Pillow)",
                current_filepath,
                output_filepath,
                (src_w, src_h),
                crop_dimensions_tuple,
            )
            crop_args = (crop_left, crop_top, crop_right, crop_bottom)

        # 6. FIRE THE CROP OFF THE UI THREAD; UI sync happens in on_crop_finished
        def _on_finished(success: bool, finished_output_path: str, error_message: str):
            self.on_crop_finished(
                success=success,
                use_lossless=use_lossless,
                file_ext=file_ext,
                error_message=error_message,
            )

        self.crop_executor.submit_crop(
            lossless=use_lossless,
            source_path=current_filepath,
            output_path=output_filepath,
            crop_args=crop_args,
            on_finished=_on_finished,
        )
        return True

    def on_crop_finished(
        self, success: bool, use_lossless: bool, file_ext: str, error_message: str
    ) -> None:
        """Runs on the GUI thread (Qt marshals queued-connection signals back
        onto the thread that owns the receiver) once CropWorker completes.
        This is the workspace-sync pass that used to live directly after
        `if crop_success:` inside process_and_execute_crop.
        """
        if not success:
            if error_message:
                print(f"Critical Error: Crop failed: {error_message}")
            self.status_manager.show_center_notification("Crop Failed")
            return

        if self.chk_overwrite.isChecked():
            # Re-hydrate the active index memory cache instantly since its file was rewritten on disk
            self.image_session.hydrate_current_image()
            self.load_image_to_viewport()

        # CRITICAL RESYNC LAYER PRESERVATION & NAV BUG CLEANUP
        if self.chk_preserve.isChecked() and self.last_crop_geometry:
            if use_lossless:
                ratio_label = self.combo_ratio.currentText()
                snap_x = round(self.last_crop_geometry.x() / 16) * 16
                snap_y = round(self.last_crop_geometry.y() / 16) * 16
                snap_w = round(self.last_crop_geometry.width() / 16) * 16
                snap_h = round(self.last_crop_geometry.height() / 16) * 16

                if ratio_label != "Freeform":
                    aspect_ratio = (
                        CropGeometryEngine.resolve_aspect_ratio(ratio_label) or 1.0
                    )
                    snap_h = round((snap_w / aspect_ratio) / 16) * 16

                self.last_crop_geometry = QRect(snap_x, snap_y, snap_w, snap_h)

            self.crop_box_selector.setGeometry(self.last_crop_geometry)
            self.crop_box_selector.show()
            self.crop_box_selector.raise_()
        else:
            # Explicitly hide and purge old image selection boundaries during navigation
            self.crop_box_selector.hide()
            self.last_crop_geometry = None

        # DYNAMIC SYSTEM NOTIFICATIONS PIXELS DISPATCHER
        if use_lossless:
            self.status_manager.show_center_notification("Lossless Crop")
        else:
            # Check if the output file is a naturally lossless format like PNG
            if file_ext in (".png", ".bmp"):
                self.status_manager.show_center_notification("Lossless Crop")
            else:
                self.status_manager.show_center_notification("Lossy Crop")

        # Update layout readout boxes and the lazy engine tick
        self.update_resolution_metrics_display()
        self.status_manager.invalidate_ui_state()

    def rotate_current_image(self):
        """Delegates layout transformations directly to the core ImageProcessor engine."""
        if not self.image_session.has_active_image:
            return

        #  THE PROCESSOR UPGRADE: Hand off the session context to your processor utility!
        self.image_manager.rotate_session_view(self.image_session)

        # Immediately push the updated texture changes out to your UI views
        self.refresh_display_canvas()

        # Re-align the stationary selection frame box geometry
        if not self.crop_box_selector.isHidden() and self.last_crop_geometry:
            snapped_rect = self.calculate_snapped_rect(self.last_crop_geometry)
            self.last_crop_geometry = snapped_rect
            self.crop_box_selector.setGeometry(self.last_crop_geometry)
            self.crop_box_selector.show()
            self.crop_box_selector.raise_()

        # Synchronize status bars, spinboxes, and the zoom preview engine
        self.update_resolution_metrics_display()
        self.status_manager.invalidate_ui_state()

    # -----------------------------------------------------------------
    # GLOBAL APPLICATION HOTKEY INTERCEPT CAPABILITIES
    # -----------------------------------------------------------------
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.close()

        if event.key() == Qt.Key.Key_P:
            # Toggle the state of the configuration checkbox
            current_state = self.cfg_show_preview.isChecked()
            self.cfg_show_preview.setChecked(not current_state)
            event.accept()
            return

        elif key == Qt.Key.Key_Space:
            # Crop + Advance
            self.process_and_execute_crop()

            # 🚀 Forward Skip via the session engine!
            if alert := self.image_session.next():
                self.status_manager.show_center_notification(alert)
            else:
                self.load_image_to_viewport()

        elif key in (Qt.Key.Key_S, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Crop + Stay
            self.process_and_execute_crop()

        elif key in (Qt.Key.Key_F, Qt.Key.Key_Right):
            # 🚀 Forward Skip: Delegate entirely to the session engine!
            if alert := self.image_session.next():
                self.status_manager.show_center_notification(alert)
            else:
                self.load_image_to_viewport()

        elif key in (Qt.Key.Key_B, Qt.Key.Key_Left):
            # 🚀 Backward Skip: Delegate entirely to the session engine!
            if alert := self.image_session.previous():
                self.status_manager.show_center_notification(alert)
            else:
                self.load_image_to_viewport()

        elif key == Qt.Key.Key_R:
            # Rotate Action
            self.rotate_current_image()

        elif event.key() == Qt.Key.Key_O:
            self.select_directory()
            event.accept()
            return

        elif event.key() == Qt.Key.Key_I:
            self.select_individual_image_file()
            event.accept()
            return

        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # 🚀 THE COMPLETE LAYOUT FIX: Delegate ALL absolute overlay positioning
        # to the status manager, which natively tracks the fresh container sizes!
        if hasattr(self, "status_manager"):
            self.status_manager.reposition_all_overlays()

        # Keep sliding panels properly anchored on right edge on resize
        if hasattr(self, "drawer") and hasattr(self, "central_widget"):
            window_width = self.central_widget.width()
            top_offset_padding = 45
            available_height = self.central_widget.height() - top_offset_padding
            if getattr(self, "drawer_is_open", False):
                self.drawer.setGeometry(
                    window_width - getattr(self, "drawer_width", 250),
                    top_offset_padding,
                    getattr(self, "drawer_width", 250),
                    available_height,
                )
            else:
                self.drawer.setGeometry(
                    window_width,
                    top_offset_padding,
                    getattr(self, "drawer_width", 250),
                    available_height,
                )

        # Restart the timer on every pixel drag (prevents premature execution)
        if hasattr(self, "resize_throttle_timer"):
            self.resize_throttle_timer.start(50)  # 50 milliseconds delay

    def execute_deferred_resize_recalc(self):
        self.refresh_display_canvas()
        if hasattr(self, "zoom_hud"):
            self.update_zoom_hud_payload()

    def toggle_settings_drawer(self):
        """Triggers the smooth sliding sidebar animation from the right bezel edge."""
        # Grab accurate central window dimension states
        window_width = self.central_widget.width()
        total_window_height = self.central_widget.height()

        top_offset_padding = 45
        available_height = total_window_height - top_offset_padding

        self.drawer_animation = QPropertyAnimation(self.drawer, b"geometry")
        self.drawer_animation.setDuration(250)
        self.drawer_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        if self.drawer_is_open:
            # SLIDE SHUT: Pull panel back completely flush off the right screen limit
            self.drawer_animation.setStartValue(
                QRect(
                    window_width - self.drawer_width,
                    top_offset_padding,
                    self.drawer_width,
                    available_height,
                )
            )
            self.drawer_animation.setEndValue(
                QRect(
                    window_width,
                    top_offset_padding,
                    self.drawer_width,
                    available_height,
                )
            )
            self.drawer_is_open = False
        else:
            # SLIDE OPEN: Shift panel inward towards the left to display its full width dimensions
            self.drawer_animation.setStartValue(
                QRect(
                    window_width,
                    top_offset_padding,
                    self.drawer_width,
                    available_height,
                )
            )
            self.drawer_animation.setEndValue(
                QRect(
                    window_width - self.drawer_width,
                    top_offset_padding,
                    self.drawer_width,
                    available_height,
                )
            )
            self.drawer_is_open = True
            self.drawer.show()
            self.drawer.raise_()

        self.drawer_animation.start()

    def closeEvent(self, event):
        """Standard PyQt window intercept routine executing right before closing down."""
        # 0. Don't let a jpegtran subprocess or Pillow write get killed mid-flight
        if hasattr(self, "crop_executor"):
            self.crop_executor.wait_for_all()

        try:
            # 1. Capture current states, write to model, and commit via SettingsManager
            self.save_application_state()
        except Exception as e:
            print(f"Critical Error: Failed to save application state: {e}")

        # 2. Safely close your borderless floating zoom HUD component
        if hasattr(self, "zoom_hud") and self.zoom_hud is not None:
            # Using a try/except ensures an issue here won't block the main application from exiting
            try:
                self.zoom_hud.close()
            except RuntimeError:
                # Handles edge-case where zoom_hud might have already been deleted/cleaned up by Qt
                pass

        # 3. Allow the default window close process to proceed
        event.accept()

    def save_application_state(self):
        """Updates the internal settings data model and passes it to the manager to store."""

        #  Only update history if the user actually has a valid folder open
        if self.image_session.folder_path and self.image_session.folder_path.exists():
            self.settings.last_used_folder = str(self.image_session.folder_path)

        self.settings.remember_settings = self.cfg_remember_settings.isChecked()
        self.settings.main_window_geometry_blob = self.saveGeometry()

        if hasattr(self, "zoom_hud"):
            self.settings.hud_win_x = self.zoom_hud.x()
            self.settings.hud_win_y = self.zoom_hud.y()
            self.settings.hud_win_w = self.zoom_hud.width()
            self.settings.hud_win_h = self.zoom_hud.height()
            self.settings.show_preview_hud = self.cfg_show_preview.isChecked()

        # 2. Update toggle flags if 'Remember settings' is checked
        if self.settings.remember_settings:
            self.settings.persist_main_win = self.cfg_persist_main_win.isChecked()
            self.settings.persist_hud_win = self.cfg_persist_hud_win.isChecked()
            self.settings.auto_open_folder = self.cfg_auto_folder.isChecked()
            self.settings.show_shortcuts = self.cfg_show_shortcuts.isChecked()
            self.settings.show_toasts = self.cfg_show_toasts.isChecked()
            self.settings.show_infobar = self.cfg_show_infobar.isChecked()
            self.settings.show_filename = self.cfg_show_filename.isChecked()
            self.settings.show_imgsize = self.cfg_show_imgsize.isChecked()
            self.settings.conserve_selection = self.chk_preserve.isChecked()
            self.settings.overwrite_files = self.chk_overwrite.isChecked()
            self.settings.ratio_preference = self.combo_ratio.currentText()
            self.settings.engine_preference = self.combo_engine.currentText()
            self.settings.show_preview_hud = self.cfg_show_preview.isChecked()

        # 3. Offload the file IO entirely to the manager
        self.settings_manager.save(self.settings)

    def load_application_state(self):
        """Fetches the state data model from the manager and pushes it to the layout views."""
        # 1. Ask the manager to handle all disk/registry processing
        self.settings = self.settings_manager.load()

        # 2. Push the completed data container straight into the visual interface
        self.apply_settings_to_ui()
        QTimer.singleShot(0, self.status_manager.reposition_splash_hud)
        QTimer.singleShot(0, self.status_manager.update_status_and_telemetry)

    def apply_settings_to_ui(self):
        """Applies the internal data model properties directly to UI components."""

        # 1. Configure master settings control rule
        self.cfg_remember_settings.setChecked(self.settings.remember_settings)

        # If the user toggled off "remember settings", bypass visual layout population
        if not self.settings.remember_settings:
            self.status_manager.set_empty_workspace_state()
            return

        # 2. Restore Component Toggles & Checkboxes
        self.cfg_persist_main_win.setChecked(self.settings.persist_main_win)
        self.cfg_persist_hud_win.setChecked(self.settings.persist_hud_win)
        self.cfg_auto_folder.setChecked(self.settings.auto_open_folder)
        self.cfg_show_shortcuts.setChecked(self.settings.show_shortcuts)
        self.cfg_show_toasts.setChecked(self.settings.show_toasts)
        self.cfg_show_infobar.setChecked(self.settings.show_infobar)
        self.cfg_show_filename.setChecked(self.settings.show_filename)
        self.cfg_show_imgsize.setChecked(self.settings.show_imgsize)
        self.chk_preserve.setChecked(self.settings.conserve_selection)
        self.chk_overwrite.setChecked(self.settings.overwrite_files)
        self.cfg_show_preview.setChecked(self.settings.show_preview_hud)

        # 3. Handle Geometry Layout Constraints
        if self.settings.persist_main_win and self.settings.main_window_geometry_blob:
            self.restoreGeometry(self.settings.main_window_geometry_blob)

        # CENTRALIZED HUD GEOMETRY: Handle sizing, fallbacks, and user flags in ONE spot
        if hasattr(self, "zoom_hud"):
            if self.settings.persist_hud_win:
                # If they want to remember it, restore their exact coordinates
                self.zoom_hud.setGeometry(
                    self.settings.hud_win_x,
                    self.settings.hud_win_y,
                    self.settings.hud_win_w,
                    self.settings.hud_win_h,
                )
            else:
                # If they UNCHECKED "remember", force it to the clean default fallback spot
                main_geom = self.geometry()
                self.zoom_hud.setGeometry(
                    main_geom.right() + 10, main_geom.top() + 50, 250, 250
                )

        # 4. Handle Zoom HUD Window Trigger
        if self.settings.show_preview_hud:
            self.toggle_zoom_hud_window_visibility()

        # 5. Extract Dropdown String ComboBox Selections Safely
        if self.combo_ratio.findText(self.settings.ratio_preference) != -1:
            self.combo_ratio.setCurrentText(self.settings.ratio_preference)

        if self.combo_engine.findText(self.settings.engine_preference) != -1:
            self.combo_engine.setCurrentText(self.settings.engine_preference)

        # Refresh structural UI systems
        self.status_manager.sync_drawer_visibility_rules()
        self.update_resolution_metrics_display()

        # 6. Folder Automation & Boot Checks
        if self.settings.auto_open_folder and self.settings.last_used_folder:
            self.automate_folder_loading(self.settings.last_used_folder)
        else:
            self.status_manager.set_empty_workspace_state()

    def automate_folder_loading(self, target_folder_str: str):
        """Asks the FileManager to scan the directory and updates current tracking indices."""
        if not target_folder_str:
            self.status_manager.set_empty_workspace_state()
            return

        # 1. Process the folder string into our unified pipeline output tuple
        folder, _, valid_files = self.file_manager.process_path(target_folder_str)

        # 2. Match your old fallback logic if no valid image files are present
        if not valid_files:
            self.image_session.close_session()
            self.status_manager.set_empty_workspace_state()
            return

        # 3. Hand off the clean dataset to our central UI engine to paint the canvas
        self.update_ui_after_loadin_folder(
            folder_path=folder,
            valid_files=valid_files,
            target_file=None,  # Defaults index sorting directly to 0
            error_msg="",  # Not needed since splash handles the empty state above
        )

    def handle_left_click_release(self):
        """Finalizes left-click box drawing by processing grid alignment transformations."""
        if self.drag_start_origin.isNull() or not self.last_crop_geometry:
            return

        fluid_rect = self.crop_box_selector.geometry()
        use_lossless = self.determine_if_lossless_active()
        # If pixel-perfect mode is active, force "No snap feedback" behavior
        if not use_lossless:
            snap_mode = "No snap feedback"
        else:
            snap_mode = self.combo_snap.currentText()

        print(
            f"[DEBUG RELEASE] Mode: {snap_mode} | Executing Final Snap Settlement Routine."
        )

        if snap_mode == "Post-release snap":
            # Visually snap the blue selection box right over the 16px grid coordinates
            snapped_rect = self.calculate_snapped_rect(fluid_rect)
            self.crop_box_selector.setGeometry(snapped_rect)
            self.last_crop_geometry = snapped_rect
            print(
                f"[DEBUG RELEASE] Box Visually Snapped to: {snapped_rect.width()}x{snapped_rect.height()}"
            )

        elif snap_mode == "Ghosting":
            # Wipe away the secondary dashed visualization layer safely
            if hasattr(self, "ghost_selector") and self.ghost_selector:
                self.ghost_selector.hide()
            # Position the main selector box precisely over the ghost frame coordinates
            snapped_rect = self.calculate_snapped_rect(fluid_rect)
            self.crop_box_selector.setGeometry(snapped_rect)
            self.last_crop_geometry = snapped_rect

        elif snap_mode == "No snap feedback":
            # Intentionally leave the blue box looking perfectly smooth on-screen,
            # but lock down background geometry coordinates to match the snapped metrics
            self.last_crop_geometry = fluid_rect
            print(
                "[DEBUG RELEASE] Kept Fluid Visual Selection Frame. Math layer locked to grid."
            )

        # Clean out temporary coordinate tracking flags
        self.drag_start_origin = QPoint()

        # Unblock, update resolution readouts, and lock configuration structures
        self.update_resolution_metrics_display()
        if hasattr(self, "zoom_hud"):
            self.update_zoom_hud_payload()

    def handle_left_click_drawing(self, current_screen_pos):
        """Drives left-click drawing. Snaps strictly to a 16x16 grid ONLY in Lossless mode.
        Forces spinbox updates in real-time across ALL feedback modes.
        """
        if self.drag_start_origin.isNull() or not self.image_session.has_active_image:
            return

        pixmap = self.image_display_container.pixmap()
        if not pixmap:
            return

        # 1. Viewport geometry and centering padding offsets
        lbl_w, lbl_h = (
            self.image_display_container.width(),
            self.image_display_container.height(),
        )
        pix_w, pix_h = pixmap.width(), pixmap.height()
        offset_x, offset_y = (lbl_w - pix_w) // 2, (lbl_h - pix_h) // 2
        viewport = self._build_viewport_geometry(pixmap)

        # 2. Contain cursor positions securely inside the active image boundary
        x1, y1 = self.drag_start_origin.x(), self.drag_start_origin.y()
        x2 = max(offset_x, min(current_screen_pos.x(), offset_x + pix_w))
        y2 = max(offset_y, min(current_screen_pos.y(), offset_y + pix_h))

        raw_w = x2 - x1
        raw_h = y2 - y1

        # 3. Dynamic Aspect Ratio Handling
        ratio_type = self.combo_ratio.currentText()
        aspect = CropGeometryEngine.resolve_aspect_ratio(ratio_type)
        if aspect is not None:
            sign_w = 1 if raw_w >= 0 else -1
            sign_h = 1 if raw_h >= 0 else -1
            raw_h = sign_h * abs(int(raw_w / aspect))

            # Limit calculations to prevent drawing outside the canvas
            if y1 + raw_h < offset_y:
                raw_h = offset_y - y1
                raw_w = sign_w * abs(int(raw_h * aspect))
            elif y1 + raw_h > offset_y + pix_h:
                raw_h = (offset_y + pix_h) - y1
                raw_w = sign_w * abs(int(raw_h * aspect))

        fluid_rect = QRect(x1, y1, raw_w, raw_h).normalized()
        snap_mode = self.combo_snap.currentText()

        use_lossless = self.determine_if_lossless_active()

        # Calculate what the grid mapped rectangle represents
        if use_lossless:
            snapped_rect = self.calculate_snapped_rect(fluid_rect)
        else:
            snapped_rect = (
                fluid_rect  # Pixel-perfect mode: No layout snapping adjustments
            )

        # 5. Layer Visibility Routines
        if snap_mode in ("No snap feedback", "Post-release snap"):
            if hasattr(self, "ghost_selector") and self.ghost_selector:
                self.ghost_selector.hide()
            self.crop_box_selector.setGeometry(fluid_rect)
            self.crop_box_selector.show()
            self.crop_box_selector.raise_()
            self.last_crop_geometry = fluid_rect

        elif snap_mode == "Ghosting":
            if not hasattr(self, "ghost_selector") or not self.ghost_selector:
                self.ghost_selector = QRubberBand(
                    QRubberBand.Shape.Rectangle, self.central_widget
                )
                self.ghost_selector.setStyleSheet(
                    "background-color: rgba(255, 165, 0, 30); border: 1px dashed orange;"
                )

            self.crop_box_selector.setGeometry(fluid_rect)
            self.crop_box_selector.show()
            self.crop_box_selector.raise_()
            self.last_crop_geometry = fluid_rect

            # Show the ghost block grid overlay ONLY if we are operating in Lossless mode
            if use_lossless:
                self.ghost_selector.setGeometry(snapped_rect)
                self.ghost_selector.show()
                self.ghost_selector.raise_()
            else:
                self.ghost_selector.hide()

        # 6. Source-Pixel Mapping for Spinbox Synchronization
        # snapped_rect is already grid-snapped (lossless) or the raw fluid_rect
        # (pixel-perfect); screen_rect_to_source_rect re-derives width/height
        # from it using the exact same rules update_resolution_metrics_display
        # and calculate_snapped_rect use, so all three stay in sync.
        source_rect = CropGeometryEngine.screen_rect_to_source_rect(
            snapped_rect if use_lossless else fluid_rect,
            viewport,
            lossless=use_lossless,
            ratio_label=ratio_type,
        )
        final_w, final_h = source_rect.width(), source_rect.height()

        # 7. Force Spinbox Value Synchronizations Safely
        # Temporarily block signals so spinbox events don't trigger canvas recalculations mid-drag
        self.spin_width.blockSignals(True)
        self.spin_height.blockSignals(True)

        self.spin_width.setValue(final_w)
        self.spin_height.setValue(final_h)

        self.spin_width.blockSignals(False)
        self.spin_height.blockSignals(False)

        # Force status HUD calculations to refresh smoothly
        self.status_manager.invalidate_ui_state()

    def calculate_snapped_rect(self, screen_rect):
        """Translates a screen QRect to True Image Space, forces pure mathematical
        aspect ratios, snaps to 16x16 blocks if Lossless is active, and returns
        a perfectly symmetrical screen QRect. Delegates the actual math to
        CropGeometryEngine so this stays in lockstep with every other
        coordinate-transform call site in the app.
        """
        pixmap = self.image_display_container.pixmap()
        if not self.image_session.has_active_image or not pixmap:
            return screen_rect

        viewport = self._build_viewport_geometry(pixmap)
        ratio_label = self.combo_ratio.currentText()
        use_lossless = self.determine_if_lossless_active()

        source_rect = CropGeometryEngine.screen_rect_to_source_rect(
            screen_rect, viewport, lossless=use_lossless, ratio_label=ratio_label
        )
        return CropGeometryEngine.source_rect_to_screen_rect(
            source_rect, viewport, ratio_label=ratio_label
        )

    def update_resolution_metrics_display(self):
        """Updates the spinboxes and status bar metrics based on the current selection box,
        ensuring strict aspect ratio alignment to prevent visual mismatches.
        """
        if (
            not self.image_session.has_active_image
            or not self.image_session.pil_image
            or self.crop_box_selector.isHidden()
        ):
            return

        pixmap = self.image_display_container.pixmap()
        if not pixmap:
            return

        viewport = self._build_viewport_geometry(pixmap)
        ratio_label = self.combo_ratio.currentText()
        use_lossless = self.determine_if_lossless_active()

        source_rect = CropGeometryEngine.screen_rect_to_source_rect(
            self.crop_box_selector.geometry(),
            viewport,
            lossless=use_lossless,
            ratio_label=ratio_label,
        )
        final_w, final_h = source_rect.width(), source_rect.height()

        # Safely push the matching dimensions to the spinboxes without triggering loops
        if not self._updating_spinboxes:
            self._updating_spinboxes = True
            self.spin_width.setValue(final_w)
            self.spin_height.setValue(final_h)
            self._updating_spinboxes = False

    def toggle_zoom_hud_window_visibility(self):
        """Strictly displays or hides the floating zoom view based on checkbox rules."""
        if not hasattr(self, "zoom_hud"):
            return

        if self.cfg_show_preview.isChecked():
            # Simply bring the window into view at whatever size it currently is
            self.zoom_hud.show()
            self.zoom_hud.raise_()
            self.update_zoom_hud_payload()
        else:
            self.zoom_hud.hide()

    def update_zoom_hud_payload(self):
        """Calculates high-res coordinates and triggers instant GPU-side cropping."""
        if (
            not PILLOW_AVAILABLE
            or not self.cfg_show_preview.isChecked()
            or self.crop_box_selector.isHidden()
            or not self.image_session.has_active_image
        ):
            if hasattr(self, "zoom_hud"):
                self.zoom_hud.master_pixmap = None
                self.zoom_hud.lbl_canvas.clear()
            return

        box_rect = self.crop_box_selector.geometry()
        pixmap = self.image_display_container.pixmap()

        if pixmap and box_rect.width() > 5 and box_rect.height() > 5:
            src_w, src_h = self.image_session.width, self.image_session.height
            viewport = self._build_viewport_geometry(pixmap)
            clamped_rect = CropGeometryEngine.clamp_screen_rect_to_pixmap(
                box_rect, viewport
            )

            # Intentionally raw (no grid snap / aspect lock): the zoom HUD previews
            # exactly what's under the rubber band right now, not the eventual snapped crop.
            crop_left = int(clamped_rect.x() * viewport.scale_x)
            crop_top = int(clamped_rect.y() * viewport.scale_y)
            crop_right = int(
                (clamped_rect.x() + clamped_rect.width()) * viewport.scale_x
            )
            crop_bottom = int(
                (clamped_rect.y() + clamped_rect.height()) * viewport.scale_y
            )

            if (crop_right > crop_left) and (crop_bottom > crop_top):
                # Clamp coordinates safely
                crop_left = max(0, min(crop_left, src_w - 1))
                crop_top = max(0, min(crop_top, src_h - 1))
                crop_right = max(crop_left + 1, min(crop_right, src_w))
                crop_bottom = max(crop_top + 1, min(crop_bottom, src_h))

                pil_coords = (crop_left, crop_top, crop_right, crop_bottom)

                # 🚀 THE FIX: Pass your live, active master texture handle directly down!
                self.zoom_hud.refresh_scaled_preview_live(
                    self.image_session.master_pixmap, pil_coords
                )
                return

        if hasattr(self, "zoom_hud"):
            self.zoom_hud.lbl_canvas.clear()

    def dragEnterEvent(self, event):
        """Fires when a user hovers a dragging mouse cargo over the application frame."""
        # Check if the dragging item contains filesystem file links/URLs
        if event.mimeData().hasUrls():
            # Dynamically change the cursor arrow to a premium link/drop icon copy state
            event.acceptProposedAction()

    def get_current_forced_ratio(self):
        """Returns the active aspect ratio multiplier float based on toolbar combo selections."""
        return CropGeometryEngine.resolve_aspect_ratio(self.combo_ratio.currentText())

    def on_spin_width_changed(self, value):
        """Triggers when width spinbox is adjusted manually via arrows or keystrokes."""
        if (
            self._updating_spinboxes
            or not self.image_session.has_active_image
            or not self.image_session.pil_image
        ):
            return

        ratio = self.get_current_forced_ratio()
        if ratio is not None:
            # Aspect ratio locked! Calculate and push matching height value natively
            self._updating_spinboxes = True
            calculated_height = int(round(value / ratio))
            # Safely cap it to your image's physical maximum pixel bounds
            calculated_height = min(calculated_height, self.image_session.height)
            self.spin_height.setValue(calculated_height)
            self._updating_spinboxes = False

        # Push the finalized dimensions out to redraw on the preview image container
        self.apply_spinbox_dimensions_to_canvas()

    def on_spin_height_changed(self, value):
        """Triggers when height spinbox is adjusted manually via arrows or keystrokes."""
        if (
            self._updating_spinboxes
            or not self.image_session.has_active_image
            or not self.image_session.pil_image
        ):
            return

        ratio = self.get_current_forced_ratio()
        if ratio is not None:
            # Aspect ratio locked! Calculate and push matching width value natively
            self._updating_spinboxes = True
            calculated_width = int(round(value * ratio))
            # Safely cap it to your image's physical maximum pixel bounds
            calculated_width = min(calculated_width, self.image_session.width)
            self.spin_width.setValue(calculated_width)
            self._updating_spinboxes = False

        # Push the finalized dimensions out to redraw on the preview image container
        self.apply_spinbox_dimensions_to_canvas()

    def apply_spinbox_dimensions_to_canvas(self):
        if not self.image_session.has_active_image or not self.image_session.pil_image:
            return
        pixmap = self.image_display_container.pixmap()
        if not pixmap:
            return

        src_w, src_h = self.image_session.width, self.image_session.height
        tw, th = (
            min(self.spin_width.value(), src_w),
            min(self.spin_height.value(), src_h),
        )

        # Lossless snapping
        if self.determine_if_lossless_active():
            tw, th = (
                CropGeometryEngine.snap_to_grid(tw),
                CropGeometryEngine.snap_to_grid(th),
            )
            if not self._updating_spinboxes:
                self._updating_spinboxes = True
                self.spin_width.setValue(tw), self.spin_height.setValue(th)
                self._updating_spinboxes = False

        if tw <= 10 or th <= 10:
            self.crop_box_selector.hide()
            return

        # Geometry calculations
        lw, lh = (
            self.image_display_container.width(),
            self.image_display_container.height(),
        )
        pw, ph = pixmap.width(), pixmap.height()
        ox, oy = (lw - pw) // 2, (lh - ph) // 2
        sx, sy = pw / src_w, ph / src_h
        bw, bh = round(tw * sx), round(th * sy)

        if not self.crop_box_selector.isHidden():
            geom = self.crop_box_selector.geometry()
            bw, bh = min(bw, pw - (geom.x() - ox)), min(bh, ph - (geom.y() - oy))
        else:
            bx, by = ox + (pw - bw) // 2, oy + (ph - bh) // 2
            self.crop_box_selector.setGeometry(bx, by, bw, bh)
            self.crop_box_selector.show()
            self.last_crop_geometry = QRect(bx, by, bw, bh)

        self.crop_box_selector.setGeometry(
            self.crop_box_selector.x(), self.crop_box_selector.y(), bw, bh
        )
        if hasattr(self, "zoom_hud"):
            self.update_zoom_hud_payload()

    def update_ui_after_loadin_folder(
        self,
        folder_path: str,
        valid_files: list,
        target_file: str = None,
        error_msg: str = "",
    ):
        """Helper method to handle the shared UI update logic and index mapping."""
        if not valid_files:
            self.image_session.close_session()
            self.crop_box_selector.hide()
            self.status_manager.set_empty_workspace_state()
            alert_text = (
                error_msg if error_msg else "No valid images found in target folder."
            )
            self.status_manager.show_center_notification(alert_text)
            if error_msg:
                self.status_manager.info_bar.lbl_status.setText(error_msg)

            if hasattr(self, "resizeEvent"):
                # Pass a mock event matching your current physical window size metrics
                self.resizeEvent(QResizeEvent(self.size(), self.size()))
            return
        # 1. 🚀 Hand the list to the session. It returns True if the texture cache bakes successfully!
        session_ready = self.image_session.load_folder(
            folder_path, valid_files, target_file
        )

        # 2. 🚀 THE CHECK: Only update your UI components if the session loaded error-free
        if session_ready:
            folder_name = self.image_session.folder_path.name
            self.lbl_folder_name.setText(f"📁 {folder_name}")

            # Refresh views using our newly integrated session data
            self.load_image_to_viewport()
            self.settings.last_used_folder = str(folder_path)

    def select_directory(self):
        fallback_path = self.settings_manager.get_fallback_path_str()

        directory = QFileDialog.getExistingDirectory(
            self, "Select Image Directory", fallback_path
        )
        if not directory:
            return

        _, _, valid_files = self.file_manager.process_path(directory)

        self.update_ui_after_loadin_folder(
            folder_path=directory,
            valid_files=valid_files,
            error_msg="No valid, readable images found in directory.",
        )

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        dropped_path = urls[0].toLocalFile()
        if not dropped_path or not Path(dropped_path).exists():
            return

        folder, starting_file, valid_files = self.file_manager.process_path(
            dropped_path
        )

        self.update_ui_after_loadin_folder(
            folder_path=folder,
            valid_files=valid_files,
            target_file=starting_file,
            error_msg="No valid, readable images found in dropped payload.",
        )

    def select_individual_image_file(self):
        fallback_path = self.settings_manager.get_fallback_path_str()
        file_filter = "Images (*.png *.jpg *.jpeg *.webp *.bmp)"

        selected_file_path, _ = QFileDialog.getOpenFileName(
            self, "Target Starting Image File", fallback_path, file_filter
        )
        if not selected_file_path:
            return

        folder, starting_file, valid_files = self.file_manager.process_path(
            selected_file_path
        )

        self.update_ui_after_loadin_folder(
            folder_path=folder,
            valid_files=valid_files,
            target_file=starting_file,
            error_msg="No valid, readable images found in target folder directory.",
        )

    def build_main_canvas(self):

        self.image_display_container = QLabel()
        self.image_display_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_display_container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.image_display_container.setStyleSheet(
            "background-color: #1a1a1a; border: 1px solid #333;"
        )

        self.image_display_container.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )
        self.main_layout.addWidget(self.image_display_container, stretch=1)

        # Attach Interactive Mouse Targets
        self.image_display_container.mousePressEvent = self.on_mouse_press
        self.image_display_container.mouseMoveEvent = self.on_mouse_move
        self.image_display_container.mouseReleaseEvent = self.on_mouse_release


if __name__ == "__main__":
    myappid = (
        "losslesscropteam.losslesscrop.editor.1.0"  # Arbitrary unique ID string names
    )

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
    app = QApplication(sys.argv)
    window = FastCropApp()
    window.show()
    sys.exit(app.exec())
