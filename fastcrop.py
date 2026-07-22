import ctypes
import subprocess
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
from PyQt6.QtGui import QColor, QIcon, QImage, QKeyEvent, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QRubberBand,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import config.app_constants as app_constants
import config.ui_constants as ui_constants
from managers.file_manager import FileManager
from managers.image_manager import ImageProcessor
from managers.settings_manager import SettingsManager
from models.app_settings import AppSettings
from widgets.control_toolbar import ControlToolbar
from widgets.floating_zoom_preview import FloatingZoomPreview
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
        self.image_folder = ""
        self.image_files = []
        self.current_index = -1
        self.current_pil_image = None

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

        # Construct the secondary, floating text overlay widget
        self.lbl_telemetry_hud = QLabel(self.central_widget)
        self.lbl_telemetry_hud.setObjectName("TelemetryHUD")
        self.lbl_telemetry_hud.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )  # Clicks pass right through it!
        self.lbl_telemetry_hud.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        self.lbl_telemetry_hud.setStyleSheet(
            self.file_manager.load_asset(
                ui_constants.STYLE_TELEMETRY_HUD, ui_constants.FOLDER_STYLES
            )
        )

        self.lbl_telemetry_hud.hide()  # Hidden by default until bar collapses
        # -------------------------------------------------------------
        #           SIDE DRAWER
        # -----------------------------------------------------
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

        #   COMMAND OVERLAY PANEL
        self.lbl_commands_overlay = QLabel(self.image_display_container)
        self.lbl_commands_overlay.hide()  # Will show once an image loads
        self.lbl_commands_overlay.setStyleSheet(
            self.file_manager.load_asset(
                ui_constants.STYLE_COMMANDS, ui_constants.FOLDER_STYLES
            )
        )
        # Populate the exact hotkey roadmap text
        self.lbl_commands_overlay.setText(
            self.file_manager.load_asset(
                ui_constants.TEMPLATE_COMMANDS, ui_constants.FOLDER_TEMPLATES
            )
        )

        # 🌟 SHADOW EFFECT A: For your top-left Shortcut Commands Overlay
        commands_shadow = QGraphicsDropShadowEffect(self)
        commands_shadow.setBlurRadius(4)  # Softness of the shadow edge
        commands_shadow.setColor(QColor("#000000"))  # Pure black shadow mapping
        commands_shadow.setOffset(1, 1)  # Shunt the shadow down 1px and right 1px
        self.lbl_commands_overlay.setGraphicsEffect(commands_shadow)

        # 🌟 SHADOW EFFECT B: For your lower-left Telemetry HUD Card
        telemetry_shadow = QGraphicsDropShadowEffect(self)
        telemetry_shadow.setBlurRadius(3)
        telemetry_shadow.setColor(QColor("#000000"))
        telemetry_shadow.setOffset(1, 1)
        self.lbl_telemetry_hud.setGraphicsEffect(telemetry_shadow)

        self.lbl_notification = QLabel(self.image_display_container)
        self.lbl_notification.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_notification.setWordWrap(True)
        self.lbl_notification.hide()

        self.lbl_notification.setStyleSheet(
            self.file_manager.load_asset(
                ui_constants.STYLE_NOTIFICATIONS, ui_constants.FOLDER_STYLES
            )
        )

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.lbl_notification.setGraphicsEffect(shadow)

        self.notification_timer = QTimer()
        self.notification_timer.setInterval(1000)
        self.notification_timer.setSingleShot(True)
        self.notification_timer.timeout.connect(self.lbl_notification.hide)

        # =============================================================
        # FLOATING INTERACTIVE HUB SPLASH HUD OVERLAY (Collision-Proof)
        # =============================================================
        self.lbl_splash_hud = QLabel(self.central_widget)
        self.lbl_splash_hud.setObjectName("SplashHUD")
        # Ensure mouse clicks pass straight through the text box so they don't block canvas drops
        self.lbl_splash_hud.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self.lbl_splash_hud.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Premium Obsidian themed typography card styling layout with 85% translucent backing
        self.lbl_splash_hud.setStyleSheet(
            self.file_manager.load_asset(
                ui_constants.STYLE_SPLASH_HUD, ui_constants.FOLDER_STYLES
            )
        )

        # Build the exact typographic text block structure using clean Unicode pointers
        # We increase the padding gaps inside the inner line elements for greater vertical depth
        splash_text = self.file_manager.load_asset(
            ui_constants.TEMPLATE_SPLASH, ui_constants.FOLDER_TEMPLATES
        )
        self.lbl_splash_hud.setText(splash_text)
        self.lbl_splash_hud.hide()  # Maintained hidden by default until evaluated on launch

        # -------------------------------------------------------------
        # BOTTOM INFO BAR LAYOUT PANEL (Split Structure)
        # -------------------------------------------------------------
        self.info_bar_widget = QWidget()
        self.info_bar = QHBoxLayout(self.info_bar_widget)
        self.info_bar.setContentsMargins(10, 5, 10, 5)

        # Left spacing stretch item to balance center filenames tracking
        self.info_bar.addStretch(1)

        # Primary Centered File Status Label
        self.lbl_status = QLabel("Ready. Open a folder to start cropping.")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #bbb; font-size: 15px; font-weight: 500;")
        self.info_bar.addWidget(self.lbl_status)

        # Secondary Right Edge Metrics Tracker
        self.info_bar.addStretch(1)
        self.lbl_metrics = QLabel("")
        self.lbl_metrics.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.lbl_metrics.setStyleSheet(
            "color: #888888; font-family: monospace; font-size: 13px; font-weight: bold;"
        )
        self.info_bar.addWidget(self.lbl_metrics)

        self.main_layout.addWidget(self.info_bar_widget)

    def load_image_to_viewport(self):
        if (
            self.current_index == -1
            or not self.image_files
            or not (0 <= self.current_index < len(self.image_files))
        ):
            # ⬇️ No image active: Reveal the floating instruction overlay card over empty canvas space ⬇️
            if hasattr(self, "lbl_splash_hud"):
                self.lbl_splash_hud.show()
                # Force instant repositioning call
                self.lbl_splash_hud.adjustSize()
                cx = (self.central_widget.width() - self.lbl_splash_hud.width()) // 2
                cy = (self.central_widget.height() - self.lbl_splash_hud.height()) // 2
                self.lbl_splash_hud.move(cx, max(50, cy))
                self.lbl_splash_hud.raise_()
            return

        if hasattr(self, "lbl_splash_hud"):
            self.lbl_splash_hud.hide()
        current_image_path = self.image_files[self.current_index]
        self.lbl_status.setText(
            f"[{self.current_index + 1}/{len(self.image_files)}] - {current_image_path.name}"
        )
        # Load through Pillow memory pipelines safely
        self.current_pil_image = Image.open(current_image_path)
        # 2. Check if its a true jpeg file
        self.is_current_file_true_jpeg = ImageProcessor.is_true_jpeg(current_image_path)
        if self.is_current_file_true_jpeg:
            print("Real jpeg")
        else:
            print("Not a jpeg")
        self.refresh_display_canvas()

        # -----------------------------------------------------------------
        # RE-SYNC WORKSPACE SELECTION LAYER PRESERVATION (STATIONARY SNAP)
        # -----------------------------------------------------------------
        if self.chk_preserve.isChecked() and self.last_crop_geometry:
            # 1. Grab the fresh file extension properties
            use_lossless = self.determine_if_lossless_active()

            if use_lossless:
                # Force the stationary screen box geometry through our core math engine.
                # This leaves the box position alone but calculates the perfect 16x16 image-space conversion.
                self.last_crop_geometry = self.calculate_snapped_rect(
                    self.last_crop_geometry
                )
                print(
                    "[DEBUG NAV] Landed on Lossless JPEG. Selection aligned to underlying MCU grid."
                )

            # Render the stationary box onto your viewport canvas exactly where it belongs
            self.crop_box_selector.setGeometry(self.last_crop_geometry)
            self.crop_box_selector.show()
            self.crop_box_selector.raise_()
        else:
            self.crop_box_selector.hide()
            self.last_crop_geometry = None
            if hasattr(self, "ghost_selector") and self.ghost_selector:
                self.ghost_selector.hide()

        self.position_commands_overlay()
        self.apply_drawer_visibility_rules()
        self.update_resolution_metrics_display()
        self.update_telemetry_label()
        if hasattr(self, "update_zoom_hud_payload"):
            self.update_zoom_hud_payload()

    def refresh_display_canvas(self):
        if not self.current_pil_image:
            return
        # TODO should we load it like the preview?
        # Convert pillow imaging data states to native PyQt QImage arrays cleanly
        pil_img = self.current_pil_image.convert("RGBA")
        data = pil_img.tobytes("raw", "RGBA")
        qimg = QImage(
            data, pil_img.size[0], pil_img.size[1], QImage.Format.Format_RGBA8888
        )

        master_pixmap = QPixmap.fromImage(qimg)

        # Resize safely based on target constraints without stretching aspect values
        container_size = self.image_display_container.size()
        scaled_pixmap = master_pixmap.scaled(
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

        if not self.image_display_container.pixmap() or self.current_index == -1:
            return

        # Hide the commands panel instantly so it doesn't obstruct cropping fields
        self.lbl_commands_overlay.hide()

        if not self.cfg_show_infobar.isChecked() and hasattr(self, "lbl_telemetry_hud"):
            self.lbl_telemetry_hud.hide()
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
            self.update_zoom_hud_payload()
            self.update_resolution_metrics_display()
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
        if self.cfg_show_shortcuts.isChecked() and self.current_index != -1:
            self.lbl_commands_overlay.show()
            self.lbl_commands_overlay.raise_()
        self.update_resolution_metrics_display()
        self.update_telemetry_label()

    def position_commands_overlay(self):
        """Positions the command overlay in the top left corner of the container."""
        self.lbl_commands_overlay.adjustSize()

        # Define a clean 15-pixel padding buffer away from the left bezel edge
        padding = 15
        x = padding
        y = padding

        # Snap the floating panel smoothly to the top-left corner
        self.lbl_commands_overlay.move(x, y)

    def on_ratio_changed(self):
        """Instantly morphs the active selection box when the aspect ratio dropdown changes."""
        # Exit early if the selection box is hidden or practically empty
        if self.crop_box_selector.isHidden() or self.crop_box_selector.width() <= 5:
            return

        ratio_type = self.combo_ratio.currentText()
        if ratio_type == "Freeform":
            return  # Freeform allows any shape, so don't alter the current frame

        # Determine the target mathematical ratio scale
        aspect_ratio = 1.0
        if ratio_type == "16:9 Widescreen":
            aspect_ratio = 16.0 / 9.0
        elif ratio_type == "4:3 Standard":
            aspect_ratio = 4.0 / 3.0

        # Use the current width as the master base and calculate the new height
        current_geom = self.crop_box_selector.geometry()
        new_width = current_geom.width()
        # CHECK BOTH ENGINE AND EXTENSION

        use_lossless = self.determine_if_lossless_active()

        if use_lossless:
            new_width = round(new_width / 16) * 16
            new_height = round((new_width / aspect_ratio) / 16) * 16
        else:
            new_height = max(1, round(new_width / aspect_ratio))

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
        if self.current_index == -1 or not self.image_files:
            return False

        # 1. Quick setting check
        if (
            self.combo_engine.currentText() != "Lossless"
            or not self.image_manager.is_lossless_available
        ):
            return False

        return getattr(self, "is_current_file_true_jpeg", False)

    # -----------------------------------------------------------------
    # PIPELINE EDITING SUBROUTINES AND WRITING LOGIC
    # -----------------------------------------------------------------
    def process_and_execute_crop(self):
        if not self.current_pil_image or self.crop_box_selector.isHidden():
            return False

        # Original asset fallback defaults
        current_filepath = self.image_files[self.current_index]
        use_lossless = self.determine_if_lossless_active()

        box_rect = self.crop_box_selector.geometry()
        pixmap = self.image_display_container.pixmap()

        if not pixmap:
            return False

        # 1. Grab the active path object safely
        current_path = self.image_files[self.current_index]

        # 2. Extract the lowercase extension directly using pathlib suffix properties
        file_ext = current_path.suffix.lower()

        # Map raw window pixels back onto underlying higher-resolution source geometries
        lbl_w, lbl_h = (
            self.image_display_container.width(),
            self.image_display_container.height(),
        )
        pix_w, pix_h = pixmap.width(), pixmap.height()

        # Calculate viewport scaling canvas offsets offsets
        offset_x = (lbl_w - pix_w) // 2
        offset_y = (lbl_h - pix_h) // 2

        # Adjust screen selections box bounds relative to image canvas positioning metrics
        adj_x = box_rect.x() - offset_x
        adj_y = box_rect.y() - offset_y

        # Constrain dimensions safely inside bounding canvas rules
        adj_x = max(0, min(adj_x, pix_w))
        adj_y = max(0, min(adj_y, pix_h))
        adj_w = min(box_rect.width(), pix_w - adj_x)
        adj_h = min(box_rect.height(), pix_h - adj_y)

        if adj_w <= 0 or adj_h <= 0:
            return False

        # Transform viewport bounding values back into underlying raw image matrix mappings
        src_w, src_h = self.current_pil_image.size
        scale_factor_x = src_w / pix_w
        scale_factor_y = src_h / pix_h

        # SAVE PATH REDIRECTION LOGIC
        if self.chk_overwrite.isChecked():
            # If overwrite is active, save directly over the source file
            output_filepath = current_filepath
        else:
            # If overwrite is OFF, ensure we create unique versions
            unique_path_object = self.file_manager.generate_unique_crop_path(
                self.image_folder, current_filepath.name
            )
            output_filepath = str(unique_path_object)

        # CRITICAL STEP FOR OVERWRITING FILE LOCKS
        # Close the Pillow memory handler connection to the source file before overwriting it
        self.current_pil_image.close()

        #  UPDATED ENGINE ROUTER WITH DETAILED LOGGING PIPELINES

        # Fix: Pull directly from the accurate spinboxes in Pixel-Perfect mode
        if use_lossless:
            # Lossless Mode: Keep the mathematically secure 16x16 MCU block snapping
            crop_left = max(0, round((adj_x * scale_factor_x) / 16) * 16)
            crop_top = max(0, round((adj_y * scale_factor_y) / 16) * 16)
            crop_right = crop_left + max(16, round((adj_w * scale_factor_x) / 16) * 16)
            crop_bottom = crop_top + max(16, round((adj_h * scale_factor_y) / 16) * 16)

        else:
            # Pixel-Perfect Mode: Trust the spinbox dimensions as the true target size
            # Calculate the top-left starting position precisely from the screen offset
            crop_left = max(0, round(adj_x * scale_factor_x))
            crop_top = max(0, round(adj_y * scale_factor_y))

            # Read the absolute intended dimensions directly from the UI elements
            target_width = self.spin_width.value()
            target_height = self.spin_height.value()

            # Force the right and bottom boundaries to yield those exact pixel dimensions
            crop_right = min(src_w, crop_left + target_width)
            crop_bottom = min(src_h, crop_top + target_height)

        # Calculate width and height for jpegtran command arguments
        crop_width = crop_right - crop_left
        crop_height = crop_bottom - crop_top

        if use_lossless:
            # 🚀 ENGINE A: TRUE LOSSLESS JPEG TRANSLATION
            print("\n[ENGINE ACTIVATION] ---> LOSSLESS MODE (jpegtran)")
            print(f" 📂 Source File   : {current_filepath}")
            print(f" 💾 Target Output : {output_filepath}")
            print(f" 📐 File Dimensions: {src_w}x{src_h}")
            print(
                f" 🧮 Crop Math     : X={crop_left}, Y={crop_top}, W={crop_width}, H={crop_height}"
            )

            crop_argument = f"{crop_width}x{crop_height}+{crop_left}+{crop_top}"
            command = [
                self.image_manager.binary_path,
                "-crop",
                crop_argument,
                "-outfile",
                output_filepath,
                current_filepath,
            ]

            try:
                # Fire the background native command process execution
                subprocess.run(
                    command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                print(
                    "[SUCCESS] Lossless binary block transformation completed with 0% quality loss."
                )
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                # Emergency safe fallback if jpegtran fails on a malformed JPEG block
                print(
                    f"❌ [EMERGENCY FALLBACK] jpegtran failed, shifting to Pillow: {e}"
                )
                img = Image.open(current_filepath)
                cropped_image = img.crop((crop_left, crop_top, crop_right, crop_bottom))
                cropped_image.save(output_filepath)
                img.close()
                print("[SUCCESS] Fallback image re-compression save finalized safely.")
        else:
            # 🎨 ENGINE B: STANDARD PILLOW RE-COMPRESSION
            print("\n[ENGINE ACTIVATION] ---> PIXEL-PERFECT MODE (Pillow)")
            print(f" 📂 Source File   : {current_filepath}")
            print(f" 💾 Target Output : {output_filepath}")
            print(f" 📐 File Dimensions: {src_w}x{src_h}")
            print(
                f" 🧮 Crop Math     : Left={crop_left}, Top={crop_top}, Right={crop_right}, Bottom={crop_bottom}"
            )
            if not getattr(self, "is_current_file_true_jpeg", False):
                print(
                    f" 📝 Format Notice : Non-JPEG format ({file_ext.upper()}) dynamically routed to Pillow engine."
                )
            elif not self.image_manager.is_lossless_available:
                print(
                    " ⚠️ Engine Notice : jpegtran binary missing from environment. Defaulting to pixel re-compression."
                )

            img = Image.open(current_filepath)
            cropped_image = img.crop((crop_left, crop_top, crop_right, crop_bottom))
            cropped_image.save(output_filepath)
            img.close()
            print("[SUCCESS] Image pixel re-compression slice saved successfully.")
        # -------------------------------------------------------------

        # Reload the newly saved file back into memory so navigation doesn't throw errors
        if self.chk_overwrite.isChecked():
            # Load the newly overwritten file path directly
            self.current_pil_image = Image.open(output_filepath)
            self.refresh_display_canvas()

            # 3. CRITICAL RESYNC LAYER PRESERVATION & NAV BUG CLEANUP
            if self.chk_preserve.isChecked() and self.last_crop_geometry:
                if use_lossless:
                    # Re-snap to 16x16 grid to prevent leaking raw off-grid coordinates
                    snap_x, snap_y = (
                        round(self.last_crop_geometry.x() / 16) * 16,
                        round(self.last_crop_geometry.y() / 16) * 16,
                    )
                    snap_w, snap_h = (
                        round(self.last_crop_geometry.width() / 16) * 16,
                        round(self.last_crop_geometry.height() / 16) * 16,
                    )

                    if self.combo_ratio.currentText() != "Freeform":
                        aspect_ratio = (
                            16.0 / 9.0
                            if "16:9" in self.combo_ratio.currentText()
                            else (
                                4.0 / 3.0
                                if "4:3" in self.combo_ratio.currentText()
                                else 1.0
                            )
                        )
                        snap_h = round((snap_w / aspect_ratio) / 16) * 16

                    self.last_crop_geometry = QRect(snap_x, snap_y, snap_w, snap_h)

                self.crop_box_selector.setGeometry(self.last_crop_geometry)
                self.crop_box_selector.show()
                self.crop_box_selector.raise_()
            else:
                # FIX: Explicitly hide and purge old image selection boundaries during navigation
                self.crop_box_selector.hide()
                self.last_crop_geometry = None

        else:
            # TODO why
            # If we saved a copy inside /cropped, re-open our original file
            self.current_pil_image = Image.open(current_filepath)

            if self.chk_preserve.isChecked() and self.last_crop_geometry:
                self.crop_box_selector.setGeometry(self.last_crop_geometry)
                self.crop_box_selector.show()
                self.crop_box_selector.raise_()
            else:
                self.crop_box_selector.hide()
                self.last_crop_geometry = None

        if use_lossless:
            self.show_center_notification("Lossless Crop")
        else:
            # Check if the output file is a naturally lossless format like PNG
            if file_ext in (".png", ".bmp"):
                self.show_center_notification("Lossless Crop")
            else:
                self.show_center_notification("Lossy Crop")

        self.update_resolution_metrics_display()
        self.update_zoom_hud_payload()
        return True

    def rotate_current_image(self):
        """Rotates the image matrix underneath the stationary viewport selection frame,
        instantly re-aligning the box to the new underlying grid.
        """
        if not self.current_pil_image:
            return

        # 1. Update our tracking angle so the Zoom Preview HUD knows what to do
        if not hasattr(self, "current_rotation_angle"):
            self.current_rotation_angle = 0
        self.current_rotation_angle = (self.current_rotation_angle - 90) % 360

        # 2. Execute the literal rotation layout expansion
        self.current_pil_image = self.current_pil_image.rotate(-90, expand=True)
        self.refresh_display_canvas()

        # 3. Re-align the stationary screen stencil to the new underlying JPEG blocks
        if not self.crop_box_selector.isHidden() and self.last_crop_geometry:
            # Let our unified utility process the snap to prevent 1-pixel rounding drift
            snapped_rect = self.calculate_snapped_rect(self.last_crop_geometry)

            self.last_crop_geometry = snapped_rect
            self.crop_box_selector.setGeometry(self.last_crop_geometry)
            self.crop_box_selector.show()
            self.crop_box_selector.raise_()

        # 4. Synchronize status bars, spinboxes, and the zoom preview engine
        self.update_resolution_metrics_display()
        if hasattr(self, "update_zoom_hud_payload"):
            self.update_zoom_hud_payload()

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
            if self.current_index < len(self.image_files) - 1:
                self.current_index += 1
                self.load_image_to_viewport()
            else:
                # Feedback fallback when hitting space on the last image
                self.show_center_notification("Last image of directory")

        elif key in (Qt.Key.Key_S, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Crop + Stay
            self.process_and_execute_crop()

        elif key in (Qt.Key.Key_F, Qt.Key.Key_Right):
            # Forward Skip
            if self.current_index < len(self.image_files) - 1:
                self.current_index += 1
                self.load_image_to_viewport()
            else:
                # Feedback fallback when trying to skip past the last image
                self.show_center_notification("Last image of directory")

        elif key in (Qt.Key.Key_B, Qt.Key.Key_Left):
            # Backward Skip
            if self.current_index > 0:
                self.current_index -= 1
                self.load_image_to_viewport()
            else:
                self.show_center_notification("First image of directory")

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

        self.position_commands_overlay()

        #  CENTER THE FLOATING SPLASH HUD CARD IN ABSOLUTE WORKSPACE ROOM
        if hasattr(self, "lbl_splash_hud") and not self.lbl_splash_hud.isHidden():
            self.lbl_splash_hud.adjustSize()

            # Compute perfect centering math targets across the workspace geometry footprint
            cx = (self.central_widget.width() - self.lbl_splash_hud.width()) // 2
            cy = (self.central_widget.height() - self.lbl_splash_hud.height()) // 2

            # Snap it seamlessly into place over the center empty canvas
            self.lbl_splash_hud.move(cx, max(50, cy))

        # FLOATING OVERLAY SNAP ALIGNER #
        if hasattr(self, "lbl_telemetry_hud") and not self.lbl_telemetry_hud.isHidden():
            self.lbl_telemetry_hud.adjustSize()
            # Position it 15 pixels up from the very base margin line of the main window workspace
            padding = 15
            x = padding
            y = self.central_widget.height() - self.lbl_telemetry_hud.height() - padding
            self.lbl_telemetry_hud.move(x, y)

        # Keep floating panels properly anchored on right edge on resize
        if hasattr(self, "drawer"):
            window_width = self.central_widget.width()
            top_offset_padding = 45
            available_height = self.central_widget.height() - top_offset_padding
            if self.drawer_is_open:
                self.drawer.setGeometry(
                    window_width - self.drawer_width,
                    top_offset_padding,
                    self.drawer_width,
                    available_height,
                )
            else:
                self.drawer.setGeometry(
                    window_width,
                    top_offset_padding,
                    self.drawer_width,
                    available_height,
                )

        if self.lbl_notification.isVisible():
            parent_w = self.image_display_container.width()
            parent_h = self.image_display_container.height()
            x = (parent_w - self.lbl_notification.width()) // 2
            y = (parent_h - self.lbl_notification.height()) // 2
            self.lbl_notification.move(x, y)

        # 2. Restart the timer on every pixel drag (prevents premature execution)
        self.resize_throttle_timer.start(50)  # 50 milliseconds delay

    def execute_deferred_resize_recalc(self):
        self.refresh_display_canvas()
        if hasattr(self, "zoom_hud"):
            self.update_zoom_hud_payload()

    def show_center_notification(self, text):
        """Displays a cinematic floating alert in the exact middle of the image area."""
        if not self.cfg_show_toasts.isChecked():
            return
        self.lbl_notification.setText(text)
        self.lbl_notification.adjustSize()

        # Center calculation math relative to the viewport container size
        parent_w = self.image_display_container.width()
        parent_h = self.image_display_container.height()
        box_w = self.lbl_notification.width()
        box_h = self.lbl_notification.height()

        x = (parent_w - box_w) // 2
        y = (parent_h - box_h) // 2

        # Snap to position and bring to the very front layer
        self.lbl_notification.move(x, y)
        self.lbl_notification.show()
        self.lbl_notification.raise_()

        # Restart the 3-second countdown clock
        self.notification_timer.start()

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

    def apply_drawer_visibility_rules(self):
        """Instantly toggles layout components visibility mapping based on drawer checkbox inputs."""
        # 1. Evaluate shortcuts guide cheat-sheet overlay
        if self.cfg_show_shortcuts.isChecked() and self.current_index != -1:
            self.lbl_commands_overlay.show()
            self.lbl_commands_overlay.raise_()
        else:
            self.lbl_commands_overlay.hide()

        # 2. Evaluate lower status-bar tracking panel labels
        if self.cfg_show_infobar.isChecked():
            self.info_bar_widget.show()
        else:
            self.info_bar_widget.hide()

        self.central_widget.layout().activate()
        self.refresh_display_canvas()

        # 3. Trigger telemetry router recalculations to shift paths matching the updated layout
        self.update_resolution_metrics_display()
        self.update_telemetry_label()

    def closeEvent(self, event):
        """Standard PyQt window intercept routine executing right before closing down."""
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

        #  SAFE TRAP: Only update history if the user actually has a valid folder open!
        if hasattr(self, "image_folder") and self.image_folder:
            from pathlib import Path

            if Path(self.image_folder).exists():
                self.settings.last_used_folder = self.image_folder

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

    def apply_settings_to_ui(self):
        """Applies the internal data model properties directly to UI components."""

        # 1. Configure master settings control rule
        self.cfg_remember_settings.setChecked(self.settings.remember_settings)

        # If the user toggled off "remember settings", bypass visual layout population
        if not self.settings.remember_settings:
            self.show_startup_splash_hud()
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
        self.apply_drawer_visibility_rules()
        self.update_resolution_metrics_display()

        # 6. Folder Automation & Boot Checks
        if self.settings.auto_open_folder and self.settings.last_used_folder:
            self.automate_folder_loading(self.settings.last_used_folder)
        else:
            self.show_startup_splash_hud()

    def automate_folder_loading(self, target_folder_str: str):
        """Asks the FileManager to scan the directory and updates current tracking indices."""
        if not target_folder_str:
            self.show_startup_splash_hud()
            return

        # 1. Process the folder string into our unified pipeline output tuple
        folder, _, valid_files = self.file_manager.process_path(target_folder_str)

        # 2. Match your old fallback logic if no valid image files are present
        if not valid_files:
            self.current_index = -1
            self.show_startup_splash_hud()
            return

        # 3. Hand off the clean dataset to our central UI engine to paint the canvas
        self.update_ui_after_loadin_folder(
            folder_path=folder,
            valid_files=valid_files,
            target_file=None,  # Defaults index sorting directly to 0
            error_msg="",  # Not needed since splash handles the empty state above
        )

    def show_startup_splash_hud(self):
        """Centers and prints your custom floating guide HUD card over an empty project workspace."""
        if hasattr(self, "lbl_splash_hud"):
            self.lbl_splash_hud.show()
            self.lbl_splash_hud.adjustSize()
            cx = (self.central_widget.width() - self.lbl_splash_hud.width()) // 2
            cy = (self.central_widget.height() - self.lbl_splash_hud.height()) // 2
            self.lbl_splash_hud.move(cx, max(50, cy))
            self.lbl_splash_hud.raise_()

    def handle_left_click_release(self):
        """Finalizes left-click box drawing by processing grid alignment transformations."""
        if self.drag_start_origin.isNull() or not self.last_crop_geometry:
            return

        snap_mode = self.combo_snap.currentText()
        fluid_rect = self.crop_box_selector.geometry()
        snapped_rect = self.calculate_snapped_rect(fluid_rect)

        print(
            f"[DEBUG RELEASE] Mode: {snap_mode} | Executing Final Snap Settlement Routine."
        )

        if snap_mode == "Post-release snap":
            # Visually snap the blue selection box right over the 16px grid coordinates
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
        if self.drag_start_origin.isNull() or not self.current_pil_image:
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

        # 2. Contain cursor positions securely inside the active image boundary
        x1, y1 = self.drag_start_origin.x(), self.drag_start_origin.y()
        x2 = max(offset_x, min(current_screen_pos.x(), offset_x + pix_w))
        y2 = max(offset_y, min(current_screen_pos.y(), offset_y + pix_h))

        raw_w = x2 - x1
        raw_h = y2 - y1

        # 3. Dynamic Aspect Ratio Handling
        ratio_type = self.combo_ratio.currentText()
        if ratio_type != "Freeform":
            aspect = (
                16.0 / 9.0
                if "16:9" in ratio_type
                else 4.0 / 3.0
                if "4:3" in ratio_type
                else 1.0
            )
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
        src_w, src_h = self.current_pil_image.size
        scale_x = src_w / pix_w
        scale_y = src_h / pix_h

        if use_lossless:
            # Map width/height based on the 16-pixel snapped matrix footprint
            img_raw_w = snapped_rect.width() * scale_x
            img_raw_h = snapped_rect.height() * scale_y
            final_w = max(16, round(img_raw_w / 16) * 16)
            final_h = max(16, round(img_raw_h / 16) * 16)

            if ratio_type != "Freeform":
                aspect = (
                    16.0 / 9.0
                    if "16:9" in ratio_type
                    else 4.0 / 3.0
                    if "4:3" in ratio_type
                    else 1.0
                )
                final_h = max(16, round((final_w / aspect) / 16) * 16)
        else:
            # Standard Pixel-Perfect Mode: Map 1:1 with continuous integer pixels
            final_w = max(1, round(fluid_rect.width() * scale_x))
            final_h = max(1, round(fluid_rect.height() * scale_y))
            if ratio_type != "Freeform":
                aspect = (
                    16.0 / 9.0
                    if "16:9" in ratio_type
                    else 4.0 / 3.0
                    if "4:3" in ratio_type
                    else 1.0
                )
                # Multiply/divide directly on final_w to eliminate floating-point rounding errors
                final_h = max(1, round(final_w / aspect))

        # 7. Force Spinbox Value Synchronizations Safely
        # Temporarily block signals so spinbox events don't trigger canvas recalculations mid-drag
        self.spin_width.blockSignals(True)
        self.spin_height.blockSignals(True)

        self.spin_width.setValue(final_w)
        self.spin_height.setValue(final_h)

        self.spin_width.blockSignals(False)
        self.spin_height.blockSignals(False)

        # Force status HUD calculations to refresh smoothly
        if hasattr(self, "zoom_hud"):
            self.update_zoom_hud_payload()

    def calculate_snapped_rect(self, screen_rect):
        """Translates a screen QRect to True Image Space, forces pure mathematical
        aspect ratios, snaps to 16x16 blocks if Lossless is active, and returns
        a perfectly symmetrical screen QRect.
        """
        if not self.current_pil_image or not self.image_display_container.pixmap():
            return screen_rect

        pixmap = self.image_display_container.pixmap()

        # 1. Viewport metrics and centering offsets
        lbl_w, lbl_h = (
            self.image_display_container.width(),
            self.image_display_container.height(),
        )
        pix_w, pix_h = pixmap.width(), pixmap.height()
        offset_x, offset_y = (lbl_w - pix_w) // 2, (lbl_h - pix_h) // 2

        # 2. Convert Screen Coordinates directly to True Image Pixel Space
        src_w, src_h = self.current_pil_image.size
        scale_x, scale_y = src_w / pix_w, src_h / pix_h

        img_x = (screen_rect.x() - offset_x) * scale_x
        img_y = (screen_rect.y() - offset_y) * scale_y
        img_w = screen_rect.width() * scale_x
        img_h = screen_rect.height() * scale_y

        # 3. Read the Selected Engine and Aspect Ratio rules
        ratio_type = self.combo_ratio.currentText()
        aspect = (
            16.0 / 9.0
            if "16:9" in ratio_type
            else 4.0 / 3.0
            if "4:3" in ratio_type
            else 1.0
        )

        use_lossless = self.determine_if_lossless_active()

        # 4. Enforce Math Transformations Directly in True Image Space
        if use_lossless:
            # Step A: Snap the width onto the 16px MCU block boundary first
            img_w = max(16, round(img_w / 16) * 16)

            # Step B: Calculate height strictly from that width to maintain aspect ratio
            if ratio_type != "Freeform":
                img_h = max(16, round((img_w / aspect) / 16) * 16)
            else:
                img_h = max(16, round(img_h / 16) * 16)

            # Step C: Align the top-left origin coordinates to the 16px grid
            img_x = round(img_x / 16) * 16
            img_y = round(img_y / 16) * 16
        else:
            # Pixel-Perfect Mode: Round directly to whole image pixels
            img_w = max(1, round(img_w))
            if ratio_type != "Freeform":
                img_h = max(1, round(img_w / aspect))
            else:
                img_h = max(1, round(img_h))

            img_x = round(img_x)
            img_y = round(img_y)

        # 5. Project back to Screen Layout Pixels with Strict Aspect Constraints
        screen_x = int(img_x * (pix_w / src_w)) + offset_x
        screen_y = int(img_y * (pix_h / src_h)) + offset_y
        screen_w = int(img_w * (pix_w / src_w))

        # CRITICAL FIX: Drive the screen height directly from the screen width calculation
        if ratio_type != "Freeform":
            screen_h = max(1, round(screen_w / aspect))
        else:
            screen_h = int(img_h * (pix_h / src_h))

        return QRect(screen_x, screen_y, screen_w, screen_h)

    def update_resolution_metrics_display(self):
        """Updates the spinboxes and status bar metrics based on the current selection box,
        ensuring strict aspect ratio alignment to prevent visual mismatches.
        """
        if (
            self.current_index == -1
            or not self.current_pil_image
            or self.crop_box_selector.isHidden()
        ):
            return

        pixmap = self.image_display_container.pixmap()
        if not pixmap:
            return

        # 1. Get current selection box screen geometry
        geom = self.crop_box_selector.geometry()
        lbl_w, lbl_h = (
            self.image_display_container.width(),
            self.image_display_container.height(),
        )
        pix_w, pix_h = pixmap.width(), pixmap.height()
        # TODO
        offset_x, offset_y = (lbl_w - pix_w) // 2, (lbl_h - pix_h) // 2

        # 2. Map back to true source image pixel dimensions
        src_w, src_h = self.current_pil_image.size
        scale_x = src_w / pix_w
        scale_y = src_h / pix_h

        img_w = geom.width() * scale_x
        img_h = geom.height() * scale_y

        # 3. CRITICAL ASPECT RATIO UI CORRECTION
        ratio_type = self.combo_ratio.currentText()
        use_lossless = self.determine_if_lossless_active()

        if use_lossless:
            # Force lossless increments to line up with 16px MCU blocks
            final_w = max(16, round(img_w / 16) * 16)
            if ratio_type != "Freeform":
                aspect = (
                    16.0 / 9.0
                    if "16:9" in ratio_type
                    else 4.0 / 3.0
                    if "4:3" in ratio_type
                    else 1.0
                )
                final_h = max(16, round((final_w / aspect) / 16) * 16)
            else:
                final_h = max(16, round(img_h / 16) * 16)
        else:
            # Standard pixel-perfect mode whole integer rounding
            final_w = max(1, round(img_w))
            if ratio_type != "Freeform":
                aspect = (
                    16.0 / 9.0
                    if "16:9" in ratio_type
                    else 4.0 / 3.0
                    if "4:3" in ratio_type
                    else 1.0
                )
                final_h = max(1, round(final_w / aspect))
            else:
                final_h = max(1, round(img_h))

        # 4. Safely push the matching dimensions to the spinboxes without triggering loops
        if not self._updating_spinboxes:
            self._updating_spinboxes = True
            self.spin_width.setValue(final_w)
            self.spin_height.setValue(final_h)
            self._updating_spinboxes = False

    def update_telemetry_label(self):
        """
        Synchronize the status bar HUD text labels
        """
        if self.current_index == -1 or not self.current_pil_image:
            self.lbl_status.setText("Ready. Open a folder to start cropping.")
            self.lbl_metrics.setText("")
            self.lbl_telemetry_hud.setText("")
            self.lbl_telemetry_hud.hide()
            return

        # 1. Compile file status tracking elements
        src_w, src_h = self.current_pil_image.size

        filename_string = ""
        if self.cfg_show_filename.isChecked():
            filename_string = f"[{self.current_index + 1}/{len(self.image_files)}] {self.image_files[self.current_index]}"

        metrics_string = ""
        if self.cfg_show_imgsize.isChecked():
            metrics_string = f"IMG: {src_w}x{src_h}"

        if self.cfg_show_infobar.isChecked():
            # PIPELINE A: Info bar is active. Populate layouts cleanly and hide floating HUD
            self.lbl_telemetry_hud.hide()
            self.lbl_status.setText(filename_string if filename_string else "")
            self.lbl_metrics.setText(metrics_string)
        else:
            # PIPELINE B: Info bar is collapsed! Divert elements onto floating HUD overlay card
            self.lbl_status.setText("")
            self.lbl_metrics.setText("")
            is_user_actively_editing = getattr(self, "is_moving_box", False) or (
                hasattr(self, "drag_start_origin")
                and not self.drag_start_origin.isNull()
                and not getattr(self, "is_moving_box", False)
            )
            hud_lines = []
            if filename_string:
                hud_lines.append(filename_string)
            if metrics_string:
                hud_lines.append(metrics_string)

            if hud_lines and not is_user_actively_editing:
                # Update text array layout and force a layout redraw pass
                self.lbl_telemetry_hud.setText("\n".join(hud_lines))
                self.lbl_telemetry_hud.show()
                self.lbl_telemetry_hud.adjustSize()
                self.lbl_telemetry_hud.raise_()

                # Re-calculate geometry offsets so card sits perfectly at lower-left margin bounds
                padding = 15
                x = padding
                y = (
                    self.central_widget.height()
                    - self.lbl_telemetry_hud.height()
                    - padding
                )
                self.lbl_telemetry_hud.move(x, y)
            else:
                self.lbl_telemetry_hud.hide()

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
        """Calculates coordinates, slices memory, and passes the payload to the HUD."""
        # Abort if the HUD window is hidden or no image selection is active

        if not PILLOW_AVAILABLE:
            self.show_center_notification("Preview not possible without Pillow")
        if (
            not PILLOW_AVAILABLE
            or not self.cfg_show_preview.isChecked()
            or self.crop_box_selector.isHidden()
        ):
            self.zoom_hud.update_zoom_payload(None)
            return

        box_rect = self.crop_box_selector.geometry()
        pixmap = self.image_display_container.pixmap()

        if pixmap and box_rect.width() > 5 and box_rect.height() > 5:
            # Map screen pixel coordinates back into high-resolution image space
            lbl_w, lbl_h = (
                self.image_display_container.width(),
                self.image_display_container.height(),
            )
            pix_w, pix_h = pixmap.width(), pixmap.height()
            offset_x = (lbl_w - pix_w) // 2
            offset_y = (lbl_h - pix_h) // 2

            adj_x = max(0, min(box_rect.x() - offset_x, pix_w))
            adj_y = max(0, min(box_rect.y() - offset_y, pix_h))
            adj_w = min(box_rect.width(), pix_w - adj_x)
            adj_h = min(box_rect.height(), pix_h - adj_y)

            src_w, src_h = self.current_pil_image.size
            scale_x = src_w / pix_w
            scale_y = src_h / pix_h

            crop_left = int(adj_x * scale_x)
            crop_top = int(adj_y * scale_y)
            crop_right = int((adj_x + adj_w) * scale_x)
            crop_bottom = int((adj_y + adj_h) * scale_y)

            if (crop_right > crop_left) and (crop_bottom > crop_top):
                try:
                    # Slice the high-speed image array straight from our memory handle
                    # We open a tiny separate copy so it doesn't collide with saving rules
                    file_path = self.image_files[self.current_index]
                    with Image.open(file_path) as img:
                        # Apply orientation rotations if the user flipped the canvas
                        if (
                            hasattr(self, "current_rotation_angle")
                            and self.current_rotation_angle != 0
                        ):
                            img = img.rotate(self.current_rotation_angle, expand=True)

                        crop_slice = img.crop(
                            (crop_left, crop_top, crop_right, crop_bottom)
                        )
                        self.zoom_hud.update_zoom_payload(crop_slice)
                        return
                except Exception:
                    pass

        self.zoom_hud.update_zoom_payload(None)

    def dragEnterEvent(self, event):
        """Fires when a user hovers a dragging mouse cargo over the application frame."""
        # Check if the dragging item contains filesystem file links/URLs
        if event.mimeData().hasUrls():
            # Dynamically change the cursor arrow to a premium link/drop icon copy state
            event.acceptProposedAction()

    def get_current_forced_ratio(self):
        """Returns the active aspect ratio multiplier float based on toolbar combo selections."""
        ratio_type = self.combo_ratio.currentText()
        if ratio_type == "1:1 Square":
            return 1.0
        if ratio_type == "16:9 Widescreen":
            return 16.0 / 9.0
        if ratio_type == "4:3 Standard":
            return 4.0 / 3.0
        return None  # Freeform

    def on_spin_width_changed(self, value):
        """Triggers when width spinbox is adjusted manually via arrows or keystrokes."""
        if (
            self._updating_spinboxes
            or self.current_index == -1
            or not self.current_pil_image
        ):
            return

        ratio = self.get_current_forced_ratio()
        if ratio is not None:
            # Aspect ratio locked! Calculate and push matching height value natively
            self._updating_spinboxes = True
            calculated_height = int(round(value / ratio))
            # Safely cap it to your image's physical maximum pixel bounds
            calculated_height = min(calculated_height, self.current_pil_image.size[1])
            self.spin_height.setValue(calculated_height)
            self._updating_spinboxes = False

        # Push the finalized dimensions out to redraw on the preview image container
        self.apply_spinbox_dimensions_to_canvas()

    def on_spin_height_changed(self, value):
        """Triggers when height spinbox is adjusted manually via arrows or keystrokes."""
        if (
            self._updating_spinboxes
            or self.current_index == -1
            or not self.current_pil_image
        ):
            return

        ratio = self.get_current_forced_ratio()
        if ratio is not None:
            # Aspect ratio locked! Calculate and push matching width value natively
            self._updating_spinboxes = True
            calculated_width = int(round(value * ratio))
            # Safely cap it to your image's physical maximum pixel bounds
            calculated_width = min(calculated_width, self.current_pil_image.size[0])
            self.spin_width.setValue(calculated_width)
            self._updating_spinboxes = False

        # Push the finalized dimensions out to redraw on the preview image container
        self.apply_spinbox_dimensions_to_canvas()

    def apply_spinbox_dimensions_to_canvas(self):
        if self.current_index == -1 or not self.current_pil_image:
            return
        pixmap = self.image_display_container.pixmap()
        if not pixmap:
            return

        src_w, src_h = self.current_pil_image.size
        tw, th = (
            min(self.spin_width.value(), src_w),
            min(self.spin_height.value(), src_h),
        )

        # Lossless snapping
        if self.determine_if_lossless_active():
            tw, th = max(16, round(tw / 16) * 16), max(16, round(th / 16) * 16)
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
            self.image_files = []
            self.current_index = -1

            if error_msg:
                self.lbl_status.setText(error_msg)
            else:
                self.show_startup_splash_hud()
            return

        self.image_folder = folder_path
        self.image_files = valid_files

        folder_name = Path(folder_path).name
        self.lbl_folder_name.setText(f"📁 {folder_name}")

        # 🚨 FIX: Match string target_file against the .name property of Path elements
        if target_file:
            # Find matching Path element by its filename string
            matched_index = next(
                (i for i, p in enumerate(self.image_files) if p.name == target_file),
                None,
            )
            self.current_index = matched_index if matched_index is not None else 0
        else:
            self.current_index = 0

        # Refresh interface views and save path history
        self.load_image_to_viewport()
        self.settings_manager.save_last_used_folder(folder_path)

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
