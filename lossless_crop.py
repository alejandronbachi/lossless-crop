import ctypes
import logging
import sys
from pathlib import Path

from config.logging_setup import initialize_logging

initialize_logging()
from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
    QTimer,
)
from PyQt6.QtGui import QIcon, QPixmap, QResizeEvent
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
from managers import theme_manager
from managers.canvas_presenter import CanvasPresenter
from managers.crop_execution_manager import CropExecutionController
from managers.crop_geometry_engine import ViewportGeometry
from managers.file_manager import FileManager
from managers.image_manager import ImageProcessor
from managers.image_session import ImageSession
from managers.keyboard_controller import KeyboardController
from managers.selection_manager import SelectionManager
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

    Image.MAX_IMAGE_PIXELS = None
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

logger = logging.getLogger(__name__)


class LossLessCropApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Lossless Crop  - {app_constants.APP_VERSION}")
        self.resize(900, 700)
        self.settings_manager = SettingsManager()
        self.settings = AppSettings()
        self.file_manager = FileManager(self.settings_manager)
        theme_manager.init_theme(
            file_manager_instance=self.file_manager,
            default_mode=theme_manager.THEME_DARK,
        )
        self.image_manager = ImageProcessor()
        self.crop_executor = CropExecutionController(self.image_manager)
        #  Create a single-shot timer for layout throttling
        self.resize_throttle_timer = QTimer(self)
        self.resize_throttle_timer.setSingleShot(True)
        self.resize_throttle_timer.timeout.connect(self.execute_deferred_resize_recalc)

        #  Core Application Icon Registry Initialization
        icon_path = (
            app_constants.APP_ROOT_DIR
            / ui_constants.FOLDER_ASSETS
            / ui_constants.FOLDER_ICONS
            / ui_constants.ICON_FILENAME
        )
        if icon_path.exists():
            # Convert Path to str since some older PyQt versions prefer string primitives for UI assets
            self.setWindowIcon(QIcon(str(icon_path)))  # Sets Title Bar Icon

        # Image Pipeline Management Variables
        self.image_session = ImageSession(self.settings)

        # Initialize User Interface
        self.zoom_hud = FloatingZoomPreview(self)
        self.keyboard_controller = KeyboardController(self)
        self.init_ui()
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
            ui_constants_obj=ui_constants,
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

        # Visual replaced by CanvasPresenter's blurred-background overlay;
        # this widget still exists purely as a geometry/state carrier for
        # SelectionManager (isHidden()/geometry()/show()/hide() calls
        # throughout the codebase all key off it), so keep it fully
        # invisible instead of removing it.
        self.crop_box_selector.paintEvent = lambda event: None
        self.selection_manager = SelectionManager(
            canvas=self.image_display_container,
            selector=self.crop_box_selector,
            ghost_parent=self.central_widget,  # matches old ghost_selector's parent
            image_session=self.image_session,
            crop_model=self.image_session.crop_model,
            ratio_combo=self.combo_ratio,
            snap_combo=self.combo_snap,
            viewport_factory=self._build_viewport_geometry,
            lossless_check=self.determine_if_lossless_active,
            on_selection_changed=self._on_selection_changed,
        )

        # Register UI controls with SettingsBinder for automatic 2-way sync
        self.settings_manager.bind_ui(self)

        self.canvas_presenter = CanvasPresenter(
            image_session=self.image_session,
            selection_manager=self.selection_manager,
            status_manager=self.status_manager,
            image_display_container=self.image_display_container,
            zoom_hud=self.zoom_hud,
            crop_box_selector=self.crop_box_selector,
            spin_width=self.spin_width,
            spin_height=self.spin_height,
            combo_ratio=self.combo_ratio,
            cfg_show_preview=self.cfg_show_preview,
            cfg_fit_preview=self.cfg_fit_preview,
            viewport_factory=self._build_viewport_geometry,
        )
        self.image_display_container.setFocus()
        self.image_session.image_model.file_deleted.connect(self.reload_directory)

    def load_image_to_viewport(self):
        return self.canvas_presenter.load_image_to_viewport()

    def sync_workspace_after_loading_image(self):
        return self.canvas_presenter.sync_workspace_after_loading_image()

    def refresh_display_canvas(self):
        return self.canvas_presenter.refresh_display_canvas()

    def _on_selection_changed(self):
        self.status_manager.invalidate_ui_state()
        self.canvas_presenter.repaint_selection_overlay()

    # -----------------------------------------------------------------
    # MOUSE INTERACTION & ASPECT BOX OVERLAYS
    # -----------------------------------------------------------------
    def on_mouse_press(self, event):
        if self.drawer_is_open:
            self.toggle_settings_drawer()
            return

        if (
            not self.image_display_container.pixmap()
            or not self.image_session.has_active_image
        ):
            return

        self.status_manager.hide_overlays_on_mouse_press()
        click_point = event.position().toPoint()

        if event.button() == Qt.MouseButton.LeftButton:
            # 🚀 INTERCEPTION: Check if a corner handle was clicked to drag-resize
            detected_grip = self.selection_manager.detect_grip_zone(click_point)
            static_anchor = self.selection_manager.get_opposite_corner_anchor(
                detected_grip
            )

            if static_anchor is not None:
                # Freeze opposite corner and take control of the grabbed handle point
                self.selection_manager.begin_draw(static_anchor)
            else:
                # Normal behavior: No grip clicked, clear and draw a fresh box from scratch
                self.selection_manager.begin_draw(click_point)

        elif event.button() == Qt.MouseButton.RightButton:
            self.selection_manager.begin_move(click_point)

        self.update_zoom_hud_payload()

    def on_mouse_move(self, event):
        current_point = event.position().toPoint()

        # 🚀 HOVER EFFECT: Track and swap the mouse cursor shapes when hovering over grips
        if event.buttons() == Qt.MouseButton.NoButton:
            grip = self.selection_manager.detect_grip_zone(current_point)
            if grip in (1, 4):  # Top-Left or Bottom-Right corner grips
                self.image_display_container.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif grip in (2, 3):  # Top-Right or Bottom-Left corner grips
                self.image_display_container.setCursor(Qt.CursorShape.SizeBDiagCursor)
            else:
                # Default back to standard crosshair when floating in open space
                self.image_display_container.setCursor(Qt.CursorShape.CrossCursor)

        # Safety baseline protection block guard (Kept exactly intact)
        if self.selection_manager.drag_start_origin.isNull():
            return

        if self.selection_manager.is_moving_box:
            self.selection_manager.update_move(current_point)
        else:
            source_rect = self.selection_manager.update_draw(current_point)
            if source_rect is not None:
                self.spin_width.blockSignals(True)
                self.spin_height.blockSignals(True)
                self.spin_width.setValue(source_rect.width())
                self.spin_height.setValue(source_rect.height())
                self.spin_width.blockSignals(False)
                self.spin_height.blockSignals(False)

    def on_mouse_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 🚀 FIXED: Check if the user just performed a static single-click without dragging
            start_pt = self.selection_manager.drag_start_origin
            end_pt = event.position().toPoint()

            # If the cursor barely moved (tolerance of 2 pixels), treat it as a deliberate single click
            if not start_pt.isNull() and (end_pt - start_pt).manhattanLength() <= 2:
                active_box = self.selection_manager.last_crop_geometry
                self.selection_manager.drag_start_origin = QPoint()
                self.selection_manager.is_moving_box = False

                # If a box is active and the click happened completely outside its borders, clear it!
                if active_box and not active_box.contains(end_pt):
                    self.selection_manager.clear_selection()
                    # Restore the standard crosshair cursor for a clean drawing environment
                    self.image_display_container.setCursor(Qt.CursorShape.CrossCursor)

                    # Run your original clean teardown handlers and exit early
                    self.status_manager.restore_overlays_on_mouse_release()
                    self.update_resolution_metrics_display()
                    return

            # Your original standard finalize routine (safely preserved)
            if not self.selection_manager.is_moving_box:
                self.selection_manager.finalize_draw()

        elif event.button() == Qt.MouseButton.RightButton:
            self.selection_manager.end_move()

        self.status_manager.restore_overlays_on_mouse_release()
        self.update_resolution_metrics_display()

    def on_ratio_changed(self):
        self.snap_selector_widget()
        self.selection_manager.apply_ratio_to_selector_widget()

    def determine_if_lossless_active(self):
        """A single source of truth to check if Lossless operation is currently legal.
        Validates engine toggle, file extension, and binary file signatures.
        """

        if not self.image_session.has_active_image:
            return False

        # 1. Quick setting check
        if (
            self.combo_engine.currentText() != ui_constants.ENGINE_LOSSLESS
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

        # 1. Look up data states straight from your unified managers and models
        current_filepath = self.image_session.current_path
        use_lossless = self.determine_if_lossless_active()
        file_ext = current_filepath.suffix.lower()

        # 3. AUTOMATED SAVE PATH ROUTING ENGINE
        if self.chk_overwrite.isChecked():
            output_filepath = str(current_filepath)
        else:
            unique_path = self.file_manager.generate_unique_crop_path(
                self.image_session.folder_path, current_filepath.name
            )
            output_filepath = str(unique_path)

        source_rect = self.image_session.crop_model.source_pixel_rect
        if source_rect.width() <= 0 or source_rect.height() <= 0:
            return False

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
            source_rect=source_rect,  # Pass unified QRect
            image_dimensions=(
                self.image_session.width,
                self.image_session.height,
            ),  # Pass base source size
            on_finished=_on_finished,
            rotation_angle=self.image_session.current_rotation_angle,
            is_true_jpeg=self.image_session.is_true_jpeg,
        )
        return True

    def on_crop_finished(
        self, success: bool, use_lossless: bool, file_ext: str, error_message: str
    ) -> None:
        if not success:
            if error_message:
                logger.error("Critical Error: Crop failed: %s", error_message)
            self.status_manager.show_center_notification(ui_constants.TEXT_CROP_FAILED)
            return

        if self.chk_overwrite.isChecked():
            # hydrate_current_image() reloads the file, which fires
            # ImageModel.image_changed -> ImageSession's Sync Chain already
            # runs the keep-vs-clear decision. load_image_to_viewport()
            # repaints the canvas and then calls sync_view_from_model()
            # (via sync_workspace_after_loading_image) to paint it.
            self.image_session.hydrate_current_image()
            self.load_image_to_viewport()
        else:
            # No image swap happened, so the Sync Chain never ran — apply
            # the same conserve_selection policy explicitly, then repaint.
            self.image_session.apply_post_crop_selection_policy()
            self.selection_manager.sync_view_from_model()

        if use_lossless:
            self.status_manager.show_center_notification(
                ui_constants.TEXT_LOSSLESS_CROP
            )
        else:
            if file_ext in app_constants.ALWAYS_LOSSLESS_IMAGE_EXTENSIONS:
                self.status_manager.show_center_notification(
                    ui_constants.TEXT_LOSSLESS_CROP
                )
            else:
                self.status_manager.show_center_notification(
                    ui_constants.TEXT_LOSSY_CROP
                )

        self.status_manager.invalidate_ui_state()

    def rotate_current_image(self):
        if not self.image_session.has_active_image:
            return

        self.image_session.image_model.rotate()
        self.refresh_display_canvas()

        if (
            not self.crop_box_selector.isHidden()
            and self.selection_manager.last_crop_geometry
        ):
            self.selection_manager.snap_selection()

        self.status_manager.invalidate_ui_state()

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
        if hasattr(self, ui_constants.WIDGET_ZOOM_HUD):
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
            logger.error("Critical Error: Failed to save application state: %s", e)

        # 2. Safely close your borderless floating zoom HUD component
        if hasattr(self, ui_constants.WIDGET_ZOOM_HUD) and self.zoom_hud is not None:
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
            self.settings_manager.save_last_used_folder(self.image_session.folder_path)

        # Capture window and HUD geometry
        self.settings_manager.capture_window_geometry(
            main_window=self,
            hud_window=getattr(self, ui_constants.WIDGET_ZOOM_HUD, None),
        )

        # Sync any un-committed state from bound UI components to AppSettings
        self.settings_manager.binder.update_model_from_ui()

        # Offload the file/registry IO entirely to the manager
        self.settings_manager.save()

    def load_application_state(self):
        """Fetches the state data model from the manager and pushes it to the layout views."""
        # 1. Ask the manager to handle all disk/registry processing
        self.settings = self.settings_manager.load()

        # self.image_session was constructed with the placeholder AppSettings()
        # from __init__, before this loaded instance existed — repoint it, or
        # ImageSession's Sync Chain would keep reading defaults forever.
        self.image_session.crop_settings = self.settings

        # 2. Push the completed data container straight into the visual interface
        self.apply_settings_to_ui()
        QTimer.singleShot(0, self.status_manager.reposition_splash_hud)
        QTimer.singleShot(0, self.status_manager.update_status_and_telemetry)

    def apply_settings_to_ui(self):
        """Applies the internal data model properties directly to UI components via binder."""

        # 1. Push model values to bound UI controls via binder
        self.settings_manager.binder.apply_to_ui()

        # If the user toggled off "remember settings", bypass visual layout population
        if not self.settings.remember_settings:
            self.status_manager.set_empty_workspace_state()
            return

        # 2. Restore Main Window & HUD Window Geometries
        self.settings_manager.restore_window_geometry(
            main_window=self,
            hud_window=getattr(self, ui_constants.WIDGET_ZOOM_HUD, None),
        )

        # 3. Handle Zoom HUD Window Trigger
        if self.settings.show_preview_hud:
            self.toggle_zoom_hud_window_visibility()

        # Refresh structural UI systems
        self.status_manager.sync_drawer_visibility_rules()
        self.update_resolution_metrics_display()

        # 4. Folder Automation & Boot Checks
        if self.settings.auto_open_folder and self.settings.last_used_folder:
            self.automate_folder_loading(self.settings.last_used_folder)
        else:
            self.status_manager.set_empty_workspace_state()

        if self.cfg_dark_theme.isChecked():
            current_theme = theme_manager.THEME_DARK
        else:
            current_theme = theme_manager.THEME_LIGHT
        theme_manager.apply_theme(current_theme)

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

    def update_resolution_metrics_display(self):
        """Updates the spinboxes and status bar metrics based on the current selection box,
        ensuring strict aspect ratio alignment to prevent visual mismatches.
        """
        return self.canvas_presenter.update_resolution_metrics_display()

    def toggle_zoom_hud_window_visibility(self):
        """Strictly displays or hides the floating zoom view based on checkbox rules."""
        if not hasattr(self, ui_constants.WIDGET_ZOOM_HUD):
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
        return self.canvas_presenter.update_zoom_hud_payload()

    def dragEnterEvent(self, event):
        """Fires when a user hovers a dragging mouse cargo over the application frame."""
        # Check if the dragging item contains filesystem file links/URLs
        if event.mimeData().hasUrls():
            # Dynamically change the cursor arrow to a premium link/drop icon copy state
            event.acceptProposedAction()

    def on_spin_width_changed(self, value=None):
        """Triggers when width spinbox is adjusted manually via arrows or keystrokes."""
        return self.canvas_presenter.on_spin_width_changed(value)

    def on_spin_height_changed(self, value=None):
        """Triggers when height spinbox is adjusted manually via arrows or keystrokes."""
        return self.canvas_presenter.on_spin_height_changed(value)

    def apply_spinbox_dimensions_to_canvas(self):
        return self.canvas_presenter.apply_spinbox_dimensions_to_canvas()

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
            alert_text = error_msg if error_msg else ui_constants.TEXT_NO_VALID_IMAGES
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
            self.btn_folder_name.setText(f"📁 {folder_name}")

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
            error_msg=ui_constants.TEXT_NO_VALID_IMAGES_DIR,
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
            error_msg=ui_constants.TEXT_NO_VALID_IMAGES_DROP,
        )

    def select_individual_image_file(self):
        fallback_path = self.settings_manager.get_fallback_path_str()
        file_filter = ui_constants.IMAGE_FILE_FILTER

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
            error_msg=ui_constants.TEXT_NO_VALID_IMAGES_DIR,
        )

    def reload_directory(self):
        """Triggered automatically via ImageModel.file_deleted when file is missing."""
        active_folder = self.image_session.folder_path
        if not active_folder or not active_folder.exists():
            self.image_session.close_session()
            return

        self.status_manager.show_center_notification("Syncing workspace...")

        # Hard rescan of disk contents
        folder, _, valid_files = self.file_manager.process_path(str(active_folder))

        # Overwrites state, wiping the temporary blacklist and rendering fresh files
        self.update_ui_after_loadin_folder(
            folder_path=folder,
            valid_files=valid_files,
            target_file=None,  # Falls back gracefully to index 0
            error_msg="Synchronized folder changes",
        )

    def build_main_canvas(self):

        self.image_display_container = QLabel()
        self.image_display_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_display_container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.image_display_container.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )
        self.main_layout.addWidget(self.image_display_container, stretch=1)

        # Attach Interactive Mouse Targets
        self.image_display_container.mousePressEvent = self.on_mouse_press
        self.image_display_container.mouseMoveEvent = self.on_mouse_move
        self.image_display_container.mouseReleaseEvent = self.on_mouse_release

    def snap_selector_widget(self):
        self.selection_manager.snap_selection()

    def on_engine_changed(self):
        self.snap_selector_widget()


if __name__ == "__main__":
    myappid = (
        "losslesscropteam.losslesscrop.editor.1.0"  # Arbitrary unique ID string names
    )

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
    app = QApplication(sys.argv)
    window = LossLessCropApp()
    window.show()
    sys.exit(app.exec())
