import sys
import os
import platform
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QFileDialog, QPushButton, 
                             QComboBox, QCheckBox, QRubberBand, QSizePolicy, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QPixmap, QImage, QKeyEvent, QColor
from PyQt6.QtCore import Qt, QRect, QSize, QPoint, QTimer



# Check for Pillow availability
try:
    from PIL import Image, ImageDraw
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Check for Local Lossless Binaries on your drive
# Calculate the path to your new binaries folder
current_dir = os.path.dirname(os.path.abspath(__file__))

if os.name == 'nt':
    BINARY_FILE = "jpegtran.exe"
elif platform.system() == "Darwin":
    BINARY_FILE = "jpegtran_mac"
else:
    BINARY_FILE = "jpegtran_linux"

# Verify if the binary is sitting in your project directory
binary_path = os.path.join(current_dir, "binaries", BINARY_FILE)
LOSSLESS_AVAILABLE = os.path.exists(binary_path)


class FastCropApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LossLess Crop")
        self.resize(900, 700)
        
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
        self.load_application_state()
        
    def init_ui(self):
        # Master Structural Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # -------------------------------------------------------------
        # TOP SYSTEM TOOLBAR CONTROL PANELS
        # -------------------------------------------------------------
        self.toolbar = QHBoxLayout()
        self.toolbar.setSpacing(10)
        
        # Standard Directory Load Button
        self.btn_open = QPushButton("Open")
        self.btn_open.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_open.setToolTip("Open a directory containing images to start editing.")
        self.btn_open.clicked.connect(self.select_directory)
        self.toolbar.addWidget(self.btn_open)
        
        self.lbl_folder_name = QLabel("No directory loaded.")
        self.lbl_folder_name.setStyleSheet("font-weight: bold; color: #aaa; margin-left: 5px;")
        self.toolbar.addWidget(self.lbl_folder_name)
        
        self.toolbar.addStretch()
        
        # Engine Options Dropdown
        self.combo_engine = QComboBox()
        self.combo_engine.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_engine.setToolTip("Choose processing engine mode for saving operations.")
        if LOSSLESS_AVAILABLE:
            self.combo_engine.addItem("Lossless")
        if PILLOW_AVAILABLE:
            self.combo_engine.addItem("Pixel-Perfect")
        if not LOSSLESS_AVAILABLE and PILLOW_AVAILABLE:
            self.combo_engine.setCurrentText("Pixel-Perfect")
        self.toolbar.addWidget(self.combo_engine)
        
        # Aspect Ratio Dropdown
        self.combo_ratio = QComboBox()
        self.combo_ratio.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_ratio.setToolTip("Force the cropping rectangle selection box to lock onto specific aspect ratios.")
        self.combo_ratio.addItems(["Freeform", "1:1 Square", "16:9 Widescreen", "4:3 Standard"])
        self.combo_ratio.currentIndexChanged.connect(self.on_ratio_changed)
        self.toolbar.addWidget(self.combo_ratio)
        
        # Shortened Toolbar Checkboxes
        self.chk_preserve = QCheckBox("Conserve selection")
        self.chk_preserve.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.chk_preserve.setToolTip("Conserve current selection box size and position coordinates across images.")
        self.chk_preserve.setChecked(True)
        self.toolbar.addWidget(self.chk_preserve)
        
        self.chk_overwrite = QCheckBox("Overwrite")
        self.chk_overwrite.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.chk_overwrite.setToolTip("Directly overwrite original source image files instead of nesting copies in a subfolder.")
        self.chk_overwrite.setChecked(False)
        self.toolbar.addWidget(self.chk_overwrite)
        
        #  Custom Gear Button - Far Left & Borderless
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_settings.setToolTip("Toggle configuration choices")
        self.btn_settings.setFixedSize(36, 36) # Square and slightly larger
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                color: #aaaaaa;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        self.btn_settings.clicked.connect(self.toggle_settings_drawer)
        self.toolbar.addWidget(self.btn_settings)

        self.main_layout.addLayout(self.toolbar)

        # -------------------------------------------------------------
        # MIDDLE VISUAL DISPLAY CANVAS PANEL
        # -------------------------------------------------------------
        self.image_display_container = QLabel()
        self.image_display_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_display_container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.image_display_container.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333;")
        
        from PyQt6.QtWidgets import QSizePolicy
        self.image_display_container.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.main_layout.addWidget(self.image_display_container, stretch=1)
        
        # Attach Interactive Mouse Targets
        self.image_display_container.mousePressEvent = self.on_mouse_press
        self.image_display_container.mouseMoveEvent = self.on_mouse_move
        self.image_display_container.mouseReleaseEvent = self.on_mouse_release
        
        
        #  CONSTRUCT THE SLIDING CONFIGURATION DRAWER INTERFACE 
        # We nest the drawer widget inside the main window, floating over the canvas
        self.drawer_width = 240
        self.drawer = QWidget(self.central_widget)
        self.drawer.setObjectName("SettingsDrawer")
        
        # Style the drawer with semi-transparent obsidian glass aesthetics
        self.drawer.setStyleSheet("""
            QWidget#SettingsDrawer {
                background-color: rgba(20, 20, 20, 0.94);
                border-left: 1px solid rgba(255, 255, 255, 0.15);
            }
            QCheckBox {
                color: #e0e0e0;
                font-size: 13px;
                padding: 4px;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding-bottom: 5px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Build the structural menu inner checkboxes layout
        self.drawer_layout = QVBoxLayout(self.drawer)
        self.drawer_layout.setContentsMargins(15, 20, 15, 20)
        self.drawer_layout.setSpacing(12)
        
        # Header Label Section Title
        self.drawer_layout.addWidget(QLabel("UI Configuration"))
        
        # -------------------------------------------------------------
        # CATEGORY 1: SHOW / DISPLAY OPTIONS
        # -------------------------------------------------------------
        lbl_show_section = QLabel("Show / Display")
        lbl_show_section.setStyleSheet("color: #888888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; border: none; margin-top: 10px; padding-bottom: 2px;")
        self.drawer_layout.addWidget(lbl_show_section)
        
        divider1 = QWidget()
        divider1.setMinimumHeight(1)
        divider1.setMaximumHeight(1)
        divider1.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); margin-bottom: 5px;")
        self.drawer_layout.addWidget(divider1)
        
        self.cfg_show_shortcuts = QCheckBox("Shortcuts Guide")
        self.cfg_show_shortcuts.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_show_shortcuts.setChecked(True)
        self.cfg_show_shortcuts.stateChanged.connect(self.apply_drawer_visibility_rules)
        self.drawer_layout.addWidget(self.cfg_show_shortcuts)
        
        self.cfg_show_toasts = QCheckBox("Center Notifications")
        self.cfg_show_toasts.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_show_toasts.setChecked(True)
        self.drawer_layout.addWidget(self.cfg_show_toasts)
        
        self.cfg_show_infobar = QCheckBox("Bottom Info Bar")
        self.cfg_show_infobar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_show_infobar.setChecked(True)
        self.cfg_show_infobar.stateChanged.connect(self.apply_drawer_visibility_rules)
        self.drawer_layout.addWidget(self.cfg_show_infobar)

        # NEW: Target resolution display toggles
        self.cfg_show_imgsize = QCheckBox("Image Resolution")
        self.cfg_show_imgsize.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_show_imgsize.setChecked(True)
        self.cfg_show_imgsize.stateChanged.connect(self.update_resolution_metrics_display)
        self.drawer_layout.addWidget(self.cfg_show_imgsize)

        self.cfg_show_cropsize = QCheckBox("Live Crop Size")
        self.cfg_show_cropsize.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_show_cropsize.setChecked(True)
        self.cfg_show_cropsize.stateChanged.connect(self.update_resolution_metrics_display)
        self.drawer_layout.addWidget(self.cfg_show_cropsize)
        
        # -------------------------------------------------------------
        # CATEGORY 2: AUTOMATION & PERSISTENCE OPTIONS
        # -------------------------------------------------------------
        lbl_auto_section = QLabel("App Workspace Memory")
        lbl_auto_section.setStyleSheet("color: #888888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; border: none; margin-top: 15px; padding-bottom: 2px;")
        self.drawer_layout.addWidget(lbl_auto_section)
        
        divider2 = QWidget()
        divider2.setMinimumHeight(1)
        divider2.setMaximumHeight(1)
        divider2.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); margin-bottom: 5px;")
        self.drawer_layout.addWidget(divider2)

        self.cfg_remember_settings = QCheckBox("Remember settings")
        self.cfg_remember_settings.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_remember_settings.setChecked(True)
        self.drawer_layout.addWidget(self.cfg_remember_settings)

        self.cfg_auto_folder = QCheckBox("Auto-open last folder")
        self.cfg_auto_folder.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_auto_folder.setChecked(False)
        self.drawer_layout.addWidget(self.cfg_auto_folder)
        
        self.drawer_layout.addStretch()

        
        # Positions the drawer completely tucked away out of sight behind the left edge
        self.drawer.setGeometry(-self.drawer_width, 0, self.drawer_width, 0)
        self.drawer_is_open = False

        # Interactive Selection Component Initialization
        self.crop_box_selector = QRubberBand(QRubberBand.Shape.Rectangle, self.image_display_container)
        self.drag_start_origin = QPoint()

        #  ADD THIS NEW COMMAND OVERLAY PANEL 
        self.lbl_commands_overlay = QLabel(self.image_display_container)
        self.lbl_commands_overlay.hide()  # Will show once an image loads
        self.lbl_commands_overlay.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-family: monospace;
                font-size: 15px;
                background-color: rgba(0, 0, 0, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        # Populate the exact hotkey roadmap text
        self.lbl_commands_overlay.setText(
            "<b>[Hotkeys Layout]</b><br>"
            "Space       : Crop & Next Image<br>"
            "S / Enter   : Crop & Stay<br>"
            "F / ➡️      : Skip Forward<br>"
            "B / ⬅️      : Skip Backward<br>"
            "R           : Rotate Clockwise<br>"
            "Esc         : Exit App<br><br>"
            "<i>Left-Click Drag: Draw Box<br>"
            "Right-Click Drag: Move Box</i>"
        )
     
        # Cinematic Floating Notifications Setup
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor

        self.lbl_notification = QLabel(self.image_display_container)
        self.lbl_notification.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_notification.setWordWrap(True)
        self.lbl_notification.hide()

        self.lbl_notification.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 0.75);
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 12px;
                padding: 15px 30px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.lbl_notification.setGraphicsEffect(shadow)

        self.notification_timer = QTimer()
        self.notification_timer.setInterval(1000)
        self.notification_timer.setSingleShot(True)
        self.notification_timer.timeout.connect(self.lbl_notification.hide)
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
        self.lbl_metrics.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_metrics.setStyleSheet("color: #888888; font-family: monospace; font-size: 13px; font-weight: bold;")
        self.info_bar.addWidget(self.lbl_metrics)
        
        self.main_layout.addWidget(self.info_bar_widget)



    # -----------------------------------------------------------------
    # FILE PIPELINE AND RENDERING LOGIC
    # -----------------------------------------------------------------
    def select_directory(self):
        from PyQt6.QtCore import QSettings
        settings = QSettings("LossLessCropTeam", "LossLessCrop")
        # Pull down folder path registry memory fallback
        fallback_path = settings.value("last_used_folder", "", type=str)
        
        # Pass path memory directly as the starting browser location parameters argument
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Image Directory", 
            fallback_path if os.path.exists(fallback_path) else ""
        )
        if not directory: return
            
        self.image_folder = directory
        folder_name = os.path.basename(os.path.normpath(directory))
        self.lbl_folder_name.setText(f"📁 {folder_name}")
        
        # 1. Define our verified, universally safe format whitelist
        SAFE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
        
        # Pull all files matching the whitelist extension pool
        raw_files = [f for f in os.listdir(directory) if f.lower().endswith(SAFE_EXTENSIONS)]
        raw_files.sort()
        
        # 2. Defensive Pass: Filter out fake/corrupted images using binary headers
        self.image_files = []
        for filename in raw_files:
            test_path = os.path.join(self.image_folder, filename)
            try:
                # Open just the head bytes. If it's an exe or raw data block, it will fail here.
                with Image.open(test_path) as img:
                    img.verify() 
                self.image_files.append(filename)
            except Exception:
                # Silently log the bypass in the terminal and keep moving
                print(f"[SECURITY SHIELD] Discarded fake, renamed, or corrupted image file: {filename}")
        
        # 3. Viewport Dispatch
        if self.image_files:
            self.current_index = 0
            self.load_image_to_viewport()
        else:
            self.lbl_status.setText("No valid, readable images found in directory.")



    def load_image_to_viewport(self):
        if not (0 <= self.current_index < len(self.image_files)):
            return
            
        file_path = os.path.join(self.image_folder, self.image_files[self.current_index])
        self.lbl_status.setText(f"[{self.current_index + 1}/{len(self.image_files)}] - {self.image_files[self.current_index]}")
        
        # Load through Pillow memory pipelines safely
        self.current_pil_image = Image.open(file_path)
        self.refresh_display_canvas()
        
        # -----------------------------------------------------------------
        # RE-SYNC WORKSPACE SELECTION LAYER PRESERVATION
        # -----------------------------------------------------------------
        if self.chk_preserve.isChecked() and self.last_crop_geometry:
            # 1. Grab the fresh file extension properties
            _, file_ext = os.path.splitext(self.image_files[self.current_index].lower())
            is_jpeg = file_ext in ('.jpg', '.jpeg')
            is_lossless = (self.combo_engine.currentText() == "Lossless") and LOSSLESS_AVAILABLE and is_jpeg
            
            if is_lossless:
                current_geom = self.last_crop_geometry
                
                #  OPTIMIZATION CHECK: Only calculate if the box is NOT already aligned
                is_already_snapped = (current_geom.x() % 16 == 0) and \
                                     (current_geom.y() % 16 == 0) and \
                                     (current_geom.width() % 16 == 0) and \
                                     (current_geom.height() % 16 == 0)
                                     
                if not is_already_snapped:
                    # Snap the shunted selection box coordinates onto 16x16 grid markers
                    snap_x = round(current_geom.x() / 16) * 16
                    snap_y = round(current_geom.y() / 16) * 16
                    snap_w = round(current_geom.width() / 16) * 16
                    snap_h = round(current_geom.height() / 16) * 16
                    
                    ratio_type = self.combo_ratio.currentText()
                    if ratio_type != "Freeform":
                        aspect_ratio = 16.0 / 9.0 if ratio_type == "16:9 Widescreen" else (4.0 / 3.0 if ratio_type == "4:3 Standard" else 1.0)
                        snap_h = round((snap_w / aspect_ratio) / 16) * 16
                    
                    # Update our tracking memory with the safe, snapped grid block values
                    self.last_crop_geometry = QRect(snap_x, snap_y, snap_w, snap_h)
                    print(f"Snapping selection box")
            # Render the updated layout box onto your viewport canvas
            self.crop_box_selector.setGeometry(self.last_crop_geometry)
            self.crop_box_selector.show()
            self.crop_box_selector.raise_()
        else:
            self.crop_box_selector.hide()
            self.last_crop_geometry = None

        self.position_commands_overlay()
        self.apply_drawer_visibility_rules()
        self.update_resolution_metrics_display()

    def refresh_display_canvas(self):
        if not self.current_pil_image:
            return
            
        # Convert pillow imaging data states to native PyQt QImage arrays cleanly
        pil_img = self.current_pil_image.convert("RGBA")
        data = pil_img.tobytes("raw", "RGBA")
        qimg = QImage(data, pil_img.size[0], pil_img.size[1], QImage.Format.Format_RGBA8888)
        
        master_pixmap = QPixmap.fromImage(qimg)
        
        # Resize safely based on target constraints without stretching aspect values
        container_size = self.image_display_container.size()
        scaled_pixmap = master_pixmap.scaled(container_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        self.image_display_container.setPixmap(scaled_pixmap)

    # -----------------------------------------------------------------
    # MOUSE INTERACTION & ASPECT BOX OVERLAYS
    # -----------------------------------------------------------------
    def on_mouse_press(self, event):
        
        if self.drawer_is_open:
            # If the user clicks on the image layout while the menu is open, smoothly retract it
            self.toggle_settings_drawer()
            return # Block the click from drawing a box on this specific tap

        if not self.image_display_container.pixmap() or self.current_index == -1:
            return
        
        # Hide the commands panel instantly so it doesn't obstruct cropping fields
        self.lbl_commands_overlay.hide()

        if event.button() == Qt.MouseButton.LeftButton:
            # Left Click: Draw a new crop box
            self.drag_start_origin = event.position().toPoint()
            self.crop_box_selector.setGeometry(QRect(self.drag_start_origin, QSize()))
            self.crop_box_selector.show()
            self.is_moving_box = False

        elif event.button() == Qt.MouseButton.RightButton:
            # Right Click: Move the existing crop box if the cursor is inside it
            click_point = event.position().toPoint()
            if not self.crop_box_selector.isHidden() and self.crop_box_selector.geometry().contains(click_point):
                self.is_moving_box = True
                self.drag_start_origin = click_point  # Track starting point of movement drag
                self.box_start_pos = self.crop_box_selector.geometry().topLeft()            
            else:
                self.is_moving_box = False

    def on_mouse_move(self, event):
        if self.drag_start_origin.isNull():
            return
            
        current_point = event.position().toPoint()
        ratio_type = self.combo_ratio.currentText()
        
        # FIX: Extract extension from tuple correctly using index [1]
        _, file_ext = os.path.splitext(self.image_files[self.current_index].lower())
        file_ext = file_ext.lower()
        is_jpeg = file_ext in ('.jpg', '.jpeg')
        is_lossless = (self.combo_engine.currentText() == "Lossless") and LOSSLESS_AVAILABLE and is_jpeg

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
            if is_lossless:
                render_x = round(target_x / 16) * 16
                render_y = round(target_y / 16) * 16
            else:
                render_x = target_x
                render_y = target_y
            
            # Keep the box inside the display window boundaries safely
            render_x = max(0, min(render_x, self.image_display_container.width() - current_geometry.width()))
            render_y = max(0, min(render_y, self.image_display_container.height() - current_geometry.height()))
            
            # Move the widget layout on the screen
            self.crop_box_selector.move(render_x, render_y)
            self.last_crop_geometry = self.crop_box_selector.geometry()
            
        # -----------------------------------------------------------------
        # BRANCH B: LEFT-CLICK DRAW LOGIC (Drawing the box)
        # -----------------------------------------------------------------
        else:
            current_rect = QRect(self.drag_start_origin, current_point).normalized()
            
            if ratio_type == "Freeform":
                new_rect = current_rect
            else:
                aspect_ratio = 1.0
                if ratio_type == "16:9 Widescreen":
                    aspect_ratio = 16.0 / 9.0
                elif ratio_type == "4:3 Standard":
                    aspect_ratio = 4.0 / 3.0
                    
                width = current_rect.width()
                height = int(width / aspect_ratio)
                
                new_rect = QRect(self.drag_start_origin.x(), self.drag_start_origin.y(), 
                                 width if current_point.x() > self.drag_start_origin.x() else -width,
                                 height if current_point.y() > self.drag_start_origin.y() else -height).normalized()
            
            # FIX: Use correct native method name setGeometry
            self.crop_box_selector.setGeometry(new_rect)
    

    def on_mouse_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_moving_box:
            if self.crop_box_selector.width() > 5 and self.crop_box_selector.height() > 5:
                self.last_crop_geometry = self.crop_box_selector.geometry()
            self.drag_start_origin = QPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            self.is_moving_box = False
            self.drag_start_origin = QPoint()
        if self.cfg_show_shortcuts.isChecked() and self.current_index != -1:
            self.lbl_commands_overlay.show()
            self.lbl_commands_overlay.raise_()
        self.update_resolution_metrics_display()

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
        original_name = self.image_files[self.current_index]
        _, ext = os.path.splitext(original_name.lower())
        is_lossless = (self.combo_engine.currentText() == "Lossless") and (ext in ('.jpg', '.jpeg'))
        
        if is_lossless:
            new_width = round(new_width / 16) * 16
            new_height = round((new_width / aspect_ratio) / 16) * 16
        else:
            new_height = int(new_width / aspect_ratio)
        
        # Build the updated boundary layout
        new_rect = QRect(current_geom.x(), current_geom.y(), new_width, new_height)
        
        # Apply the new geometry dimensions to the canvas overlay
        self.crop_box_selector.setGeometry(new_rect)
        self.last_crop_geometry = new_rect
        self.crop_box_selector.raise_()

    # -----------------------------------------------------------------
    # PIPELINE EDITING SUBROUTINES AND WRITING LOGIC
    # -----------------------------------------------------------------
    def process_and_execute_crop(self):
        if not self.current_pil_image or self.crop_box_selector.isHidden():
            return False
            
        box_rect = self.crop_box_selector.geometry()
        pixmap = self.image_display_container.pixmap()
        
        if not pixmap:
            return False
            
        # Map raw window pixels back onto underlying higher-resolution source geometries
        lbl_w, lbl_h = self.image_display_container.width(), self.image_display_container.height()
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
        
        crop_left = int(adj_x * scale_factor_x)
        crop_top = int(adj_y * scale_factor_y)
        crop_right = int((adj_x + adj_w) * scale_factor_x)
        crop_bottom = int((adj_y + adj_h) * scale_factor_y)
        
        # Calculate width and height for jpegtran command arguments
        crop_width = crop_right - crop_left
        crop_height = crop_bottom - crop_top

        # Original asset fallback defaults
        original_name = self.image_files[self.current_index]
        current_filepath = os.path.join(self.image_folder, original_name)
        
        # SAVE PATH REDIRECTION LOGIC
        if self.chk_overwrite.isChecked():
            # If overwrite is active, save directly over the source file
            output_filepath = current_filepath
        else:
            # If overwrite is OFF, ensure we create unique versions
            output_subfolder = os.path.join(self.image_folder, "cropped")
            os.makedirs(output_subfolder, exist_ok=True)
            
            # Split filename and extension (e.g., 'photo' and '.jpg')
            name, ext = os.path.splitext(original_name)
            output_filepath = os.path.join(output_subfolder, original_name)
            
            # If the file already exists, loop until a unique _X index is found
            version_counter = 1
            while os.path.exists(output_filepath):
                new_filename = f"{name}_{version_counter}{ext}"
                output_filepath = os.path.join(output_subfolder, new_filename)
                version_counter += 1
        
        # CRITICAL STEP FOR OVERWRITING FILE LOCKS 
        # Close the Pillow memory handler connection to the source file before overwriting it
        self.current_pil_image.close()
        
        #  UPDATED ENGINE ROUTER WITH DETAILED LOGGING PIPELINES 

        _, file_ext = os.path.splitext(original_name)
        file_ext = file_ext.lower()  # ✅ Normalizes .JPG / .JPEG down to lowercase strings
        is_jpeg = file_ext in ('.jpg', '.jpeg')
        
        # Verify the actual internal file signature structure for JPEG
        is_true_jpeg = False
        if is_jpeg:
            try:
                with open(current_filepath, 'rb') as f:
                    is_true_jpeg = (f.read(3) == b'\xff\xd8\xff')
            except Exception:
                is_true_jpeg = False

        use_lossless = (self.combo_engine.currentText() == "Lossless") and LOSSLESS_AVAILABLE and is_true_jpeg

        if use_lossless:
            # 🚀 ENGINE A: TRUE LOSSLESS JPEG TRANSLATION
            print(f"\n[ENGINE ACTIVATION] ---> LOSSLESS MODE (jpegtran)")
            print(f" 📂 Source File   : {current_filepath}")
            print(f" 💾 Target Output : {output_filepath}")
            print(f" 📐 File Dimensions: {src_w}x{src_h}")
            print(f" 🧮 Crop Math     : X={crop_left}, Y={crop_top}, W={crop_width}, H={crop_height}")

            current_dir = os.path.dirname(os.path.abspath(__file__))
            if os.name == 'nt':
                bin_name = "jpegtran.exe"
            elif platform.system() == "Darwin":
                bin_name = "jpegtran_mac"
            else:
                bin_name = "jpegtran_linux"
            binary_path = os.path.join(current_dir, "binaries", bin_name)

            crop_argument = f"{crop_width}x{crop_height}+{crop_left}+{crop_top}"
            command = [
                binary_path,
                "-crop", crop_argument,
                "-outfile", output_filepath,
                current_filepath
            ]
            
            try:
                # Fire the background native command process execution
                subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("[SUCCESS] Lossless binary block transformation completed with 0% quality loss.")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                # Emergency safe fallback if jpegtran fails on a malformed JPEG block
                print(f"❌ [EMERGENCY FALLBACK] jpegtran failed, shifting to Pillow: {e}")
                img = Image.open(current_filepath)
                cropped_image = img.crop((crop_left, crop_top, crop_right, crop_bottom))
                cropped_image.save(output_filepath)
                img.close()
                print("[SUCCESS] Fallback image re-compression save finalized safely.")
        else:
            # 🎨 ENGINE B: STANDARD PILLOW RE-COMPRESSION
            print(f"\n[ENGINE ACTIVATION] ---> PIXEL-PERFECT MODE (Pillow)")
            print(f" 📂 Source File   : {current_filepath}")
            print(f" 💾 Target Output : {output_filepath}")
            print(f" 📐 File Dimensions: {src_w}x{src_h}")
            print(f" 🧮 Crop Math     : Left={crop_left}, Top={crop_top}, Right={crop_right}, Bottom={crop_bottom}")
            if not is_jpeg:
                print(f" 📝 Format Notice : Non-JPEG format ({file_ext.upper()}) dynamically routed to Pillow engine.")
            elif not LOSSLESS_AVAILABLE:
                print(f" ⚠️ Engine Notice : jpegtran binary missing from environment. Defaulting to pixel re-compression.")

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
            
            # ⬇️ UPDATED: Conserve the selection layer even after an overwrite! ⬇️
            if self.chk_preserve.isChecked() and self.last_crop_geometry:
                self.crop_box_selector.setGeometry(self.last_crop_geometry)
                self.crop_box_selector.show()
                self.crop_box_selector.raise_()
            else:
                self.crop_box_selector.hide()
                self.last_crop_geometry = None
        else:
            # If we saved a copy inside /cropped, re-open our original file
            self.current_pil_image = Image.open(current_filepath)
            
            if self.chk_preserve.isChecked() and self.last_crop_geometry:
                self.crop_box_selector.setGeometry(self.last_crop_geometry)
                self.crop_box_selector.show()
                self.crop_box_selector.raise_()
            else:
                self.crop_box_selector.hide()
                self.last_crop_geometry = None

        self.update_resolution_metrics_display()        
        return True






    def rotate_current_image(self):
        if self.current_pil_image:
            self.current_pil_image = self.current_pil_image.rotate(-90, expand=True)
            self.refresh_display_canvas()
            self.update_resolution_metrics_display()

    # -----------------------------------------------------------------
    # GLOBAL APPLICATION HOTKEY INTERCEPT CAPABILITIES
    # -----------------------------------------------------------------
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        
        if key == Qt.Key.Key_Escape:
            self.close()
            
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
            
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_display_canvas()
        self.position_commands_overlay()

        # Keep floating panels properly anchored on right edge on resize
        if hasattr(self, 'drawer'):
            window_width = self.central_widget.width()
            top_offset_padding = 45
            available_height = self.central_widget.height() - top_offset_padding
            if self.drawer_is_open:
                self.drawer.setGeometry(window_width - self.drawer_width, top_offset_padding, self.drawer_width, available_height)
            else:
                self.drawer.setGeometry(window_width, top_offset_padding, self.drawer_width, available_height)
               
        if self.lbl_notification.isVisible():
            parent_w = self.image_display_container.width()
            parent_h = self.image_display_container.height()
            x = (parent_w - self.lbl_notification.width()) // 2
            y = (parent_h - self.lbl_notification.height()) // 2
            self.lbl_notification.move(x, y)        

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
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        
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
            self.drawer_animation.setStartValue(QRect(window_width - self.drawer_width, top_offset_padding, self.drawer_width, available_height))
            self.drawer_animation.setEndValue(QRect(window_width, top_offset_padding, self.drawer_width, available_height))
            self.drawer_is_open = False
        else:
            # SLIDE OPEN: Shift panel inward towards the left to display its full width dimensions
            self.drawer_animation.setStartValue(QRect(window_width, top_offset_padding, self.drawer_width, available_height))
            self.drawer_animation.setEndValue(QRect(window_width - self.drawer_width, top_offset_padding, self.drawer_width, available_height))
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

    def closeEvent(self, event):
        """Standard PyQt window intercept routine executing right before closing down."""
        self.save_application_state()
        event.accept()

    def save_application_state(self):
        """Saves current tool states and path preferences into OS settings registries."""
        from PyQt6.QtCore import QSettings
        settings = QSettings("LossLessCropTeam", "LossLessCrop")
        
        # Always store the current folder directory no matter what
        if self.image_folder:
            settings.setValue("last_used_folder", self.image_folder)
            
        # 🌟 ALWAYS write the master preference toggle first!
        master_remember = self.cfg_remember_settings.isChecked()
        settings.setValue("remember_settings", master_remember)
        
        # Write state variables if 'Remember settings' checkbox rule is active
        if master_remember:
            settings.setValue("auto_open_folder", self.cfg_auto_folder.isChecked())
            settings.setValue("show_shortcuts", self.cfg_show_shortcuts.isChecked())
            settings.setValue("show_toasts", self.cfg_show_toasts.isChecked())
            settings.setValue("show_infobar", self.cfg_show_infobar.isChecked())
            settings.setValue("show_imgsize", self.cfg_show_imgsize.isChecked())
            settings.setValue("show_cropsize", self.cfg_show_cropsize.isChecked())
            settings.setValue("conserve_selection", self.chk_preserve.isChecked())
            settings.setValue("overwrite_files", self.chk_overwrite.isChecked())
            settings.setValue("ratio_preference", self.combo_ratio.currentText())
            settings.setValue("engine_preference", self.combo_engine.currentText())

    def load_application_state(self):
        """Restores previous session user state conditions on startup safely handling OS registries."""
        from PyQt6.QtCore import QSettings
        settings = QSettings("LossLessCropTeam", "LossLessCrop")
        
        # Helper function to safely translate OS string registries ("true"/"false") into Python booleans
        def safe_bool(val, default):
            if val is None: return default
            if isinstance(val, bool): return val
            if isinstance(val, int): return bool(val)
            return str(val).lower() in ("true", "1", "yes")

        # 1. Parse the master memory rule
        raw_remember = settings.value("remember_settings", True)
        remember = safe_bool(raw_remember, True)
        self.cfg_remember_settings.setChecked(remember)
        
        if remember:
            # 2. Extract and translate all Boolean states safely using EXACT matching keys
            self.cfg_auto_folder.setChecked(safe_bool(settings.value("auto_open_folder"), False))
            self.cfg_show_shortcuts.setChecked(safe_bool(settings.value("show_shortcuts"), True))
            self.cfg_show_toasts.setChecked(safe_bool(settings.value("show_toasts"), True))
            self.cfg_show_infobar.setChecked(safe_bool(settings.value("show_infobar"), True))
            self.cfg_show_imgsize.setChecked(safe_bool(settings.value("show_imgsize"), True))
            self.cfg_show_cropsize.setChecked(safe_bool(settings.value("show_cropsize"), True))
            self.chk_preserve.setChecked(safe_bool(settings.value("conserve_selection"), True))
            self.chk_overwrite.setChecked(safe_bool(settings.value("overwrite_files"), False))
            
            # 3. Extract Dropdown String Values Safely
            ratio = settings.value("ratio_preference", "Freeform")
            if ratio and self.combo_ratio.findText(str(ratio)) != -1: 
                self.combo_ratio.setCurrentText(str(ratio))
                
            engine = settings.value("engine_preference", "Pixel-Perfect")
            if engine and self.combo_engine.findText(str(engine)) != -1: 
                self.combo_engine.setCurrentText(str(engine))

        # Refresh the UI layout elements to reflect the loaded choices
        self.apply_drawer_visibility_rules()
        self.update_resolution_metrics_display()
        
        # 4. Folder Automation Check
        last_folder = settings.value("last_used_folder", "")
        if last_folder and isinstance(last_folder, str) and os.path.exists(last_folder):
            if remember and self.cfg_auto_folder.isChecked():
                self.image_folder = last_folder
                folder_name = os.path.basename(os.path.normpath(last_folder))
                self.lbl_folder_name.setText(f"📁 {folder_name}")
                
                SAFE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
                self.image_files = [f for f in os.listdir(last_folder) if f.lower().endswith(SAFE_EXTENSIONS)]
                self.image_files.sort()
                
                if self.image_files:
                    self.current_index = 0
                    self.load_image_to_viewport()


    def update_resolution_metrics_display(self):
        """Computes and formats current source resolution and mouse box coordinates strings."""
        if self.current_index == -1 or not self.current_pil_image:
            self.lbl_metrics.setText("")
            return
            
        metrics_text_parts = []
        src_w, src_h = self.current_pil_image.size
        
        # 1. Core Source Image Array Dimensions
        if self.cfg_show_imgsize.isChecked():
            metrics_text_parts.append(f"IMG: {src_w}x{src_h}")
            
        # 2. Translate Visual Screen Selection Space Dimensions back into Raw File Geometry Coordinates
        if self.cfg_show_cropsize.isChecked():
            # Check if the rubber band box is visible and actually contains shape dimensions
            has_selection = (not self.crop_box_selector.isHidden()) and \
                            (self.crop_box_selector.width() > 5) and \
                            (self.crop_box_selector.height() > 5)
                            
            if has_selection:
                box_rect = self.crop_box_selector.geometry()
                pixmap = self.image_display_container.pixmap()
                
                if pixmap:
                    # Extract accurate pixel dimension envelopes from current preview containers
                    lbl_w, lbl_h = self.image_display_container.width(), self.image_display_container.height()
                    pix_w, pix_h = pixmap.width(), pixmap.height()
                    
                    # Compute layout centering offset metrics
                    offset_x = (lbl_w - pix_w) // 2
                    offset_y = (lbl_h - pix_h) // 2
                    
                    # Clip current active drawing boundaries relative to raw image position bounds
                    adj_x = max(0, min(box_rect.x() - offset_x, pix_w))
                    adj_y = max(0, min(box_rect.y() - offset_y, pix_h))
                    adj_w = min(box_rect.width(), pix_w - adj_x)
                    adj_h = min(box_rect.height(), pix_h - adj_y)
                    
                    # Scaling transformations math steps
                    scale_x = src_w / pix_w
                    scale_y = src_h / pix_h
                    
                    real_crop_w = int(adj_w * scale_x)
                    real_crop_h = int(adj_h * scale_y)
                    
                    if real_crop_w > 0 and real_crop_h > 0:
                        metrics_text_parts.append(f"CROP: {real_crop_w}x{real_crop_h}")
                    else:
                        # Fallback placeholder if calculation boundaries collapse
                        metrics_text_parts.append("CROP: 0x0")
                else:
                    metrics_text_parts.append("CROP: 0x0")
            else:
                # 🌟 MAINTAIN UI CONSISTENCY: Always append 0x0 placeholder if no selection box is active 🌟
                metrics_text_parts.append("CROP: 0x0")
                
        # Inject the final calculated results text cleanly into layout label
        self.lbl_metrics.setText(" | ".join(metrics_text_parts) if metrics_text_parts else "")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FastCropApp()
    window.show()
    sys.exit(app.exec())
  
