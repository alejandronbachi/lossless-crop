import ctypes
import os
import platform
import subprocess
import sys

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSettings,
    QSize,
    Qt,
    QTimer,
)
from PyQt6.QtGui import QColor, QFont, QIcon, QImage, QKeyEvent, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QRubberBand,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

# Check for Pillow availability
try:
    from PIL import Image, ImageDraw

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Check for Local Lossless Binaries on your drive
# Calculate the path to your new binaries folder
current_dir = os.path.dirname(os.path.abspath(__file__))

if os.name == "nt":
    BINARY_FILE = "jpegtran.exe"
elif platform.system() == "Darwin":
    BINARY_FILE = "jpegtran_mac"
else:
    BINARY_FILE = "jpegtran_linux"

# Verify if the binary is sitting in your project directory
binary_path = os.path.join(current_dir, "binaries", BINARY_FILE)
LOSSLESS_AVAILABLE = os.path.exists(binary_path)


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
            pil_rgba = self.cached_crop_slice.convert("RGBA")
            data = pil_rgba.tobytes("raw", "RGBA")
            img_w, img_h = pil_rgba.size
            qimg = QImage(data, img_w, img_h, QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)

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


class FastCropApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LossLess Crop")
        self.resize(900, 700)

        # 🌟 NEW: Core Application Icon Registry Initialization 🌟
        icon_path = os.path.join(
            os.path.dirname(__index__ if "__index__" in locals() else __file__),
            "icon.png",
        )
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            self.setWindowIcon(app_icon)  # Sets Title Bar Icon

        self.setStyleSheet("""
            /* Main Window Workspace Context Background */

            /*  Main Window Workspace Context Background (Explicitly target QMainWindow) */
            QMainWindow {
                background-color: #121212;
            }
            
            /*  Target actual visual widgets individually instead of a broad QWidget wrapper 
               This keeps internal dropdown delegate lists safe from -1 font inheritance death! */
            QLabel, QCheckBox, QPushButton, QComboBox {
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
                color: #e0e0e0;
            }
                            
            /* Premium Micro flat Interactive Toolbar Buttons */
            QPushButton {
                background-color: #222222;
                border: 1px solid #333333;
                border-radius: 4px;
                color: #ffffff;
                padding: 5px 12px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2b2b2b;
                border: 1px solid #444444;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
                border: 1px solid #222222;
            }
            
            QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 4px 25px 4px 10px;
                color: #ffffff;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #444444;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                selection-background-color: #2d2d2d;
                selection-color: #ffffff;
                color: #cccccc;
            }
            
            /* Bottom Split Structural Information Framework Widget */
            QWidget#info_bar_widget {
                background-color: #0a0a0a;
                border-top: 1px solid #222222;
            }

            
                        /* Sleek Space-Saving Checkboxes Layout Options */
            QCheckBox {
                font-size: 13px;
                color: #cccccc;
                spacing: 6px;
                background-color: transparent;
            }
            QCheckBox:hover {
                color: #ffffff;
            }
            
            /* Base layout definition for ALL checkbox indicator boxes */
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #444444;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            
            /* Unchecked Hover State */
            QCheckBox::indicator:unchecked:hover {
                border: 1px solid #666666;
                background-color: #252525;
            }
            
            /* Safe, fully-quoted Base64 data string blocks all console logs & syntax warnings  */
            QCheckBox::indicator:checked {
                background-color: #3b5998;
                border: 1px solid #4a6fa5;
                image: url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjIwIDYgOSAxNyA0IDEyIi8+PC9zdmc+");
            }
            
            /* Checked Hover State */
            QCheckBox::indicator:checked:hover {
                background-color: #4a6fa5;
                border: 1px solid #5a7fb5;
            }
            
            /* Bottom Split Structural Information Framework Widget */
            QWidget#info_bar_widget {
                background-color: #0a0a0a;
                border-top: 1px solid #222222;
            }
        """)

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
        # TOP SYSTEM TOOLBAR CONTROL PANELS
        # -------------------------------------------------------------
        self.toolbar = QHBoxLayout()
        self.toolbar.setSpacing(10)

        self.lbl_folder_name = QPushButton("No directory loaded")
        self.lbl_folder_name.setStyleSheet(
            "font-weight: bold; color: #aaa; margin-left: 5px; min-width: 140px;text-align: left;"
        )
        self.lbl_folder_name.clicked.connect(self.select_directory)

        self.toolbar.addWidget(self.lbl_folder_name)

        self.toolbar.addStretch()

        # Engine Options Dropdown
        self.combo_engine = QComboBox()
        self.combo_engine.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_engine.setToolTip(
            "Choose processing engine mode for saving operations."
        )

        native_font = QFont(
            "Segoe UI", 10
        )  # Binds a solid, valid 10pt/13px font profile
        self.combo_engine.setFont(native_font)
        self.combo_engine.view().setFont(
            native_font
        )  # Binds the internal dropdown view list too!

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
        self.combo_ratio.setToolTip(
            "Force the cropping rectangle selection box to lock onto specific aspect ratios."
        )
        self.combo_ratio.setFont(native_font)
        self.combo_ratio.view().setFont(native_font)
        self.combo_ratio.addItems(
            ["Freeform", "1:1 Square", "16:9 Widescreen", "4:3 Standard"]
        )
        self.combo_ratio.currentIndexChanged.connect(self.on_ratio_changed)
        self.toolbar.addWidget(self.combo_ratio)

        self.combo_snap = QComboBox()
        self.combo_snap.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_snap.setToolTip(
            "Select layout feedback mode for Left-Click mouse drawing."
        )
        self.combo_snap.setFont(native_font)
        self.combo_snap.view().setFont(native_font)
        self.combo_snap.addItems(["No snap feedback", "Post-release snap", "Ghosting"])
        self.toolbar.addWidget(self.combo_snap)

        # -------------------------------------------------------------
        # TOP TOOLBAR: PRECISION MANUAL CROP INPUT SPINBOXES
        # -------------------------------------------------------------

        # Guard flag variable to block recursive input echo storms
        self._updating_spinboxes = False

        # Build a small layout container frame to hold our spinboxes on the toolbar row
        self.spin_container = QFrame()
        self.spin_container.setStyleSheet(
            "background-color: transparent; border: none; margin: 0; padding: 0;"
        )
        spin_layout = QHBoxLayout(self.spin_container)
        spin_layout.setContentsMargins(5, 0, 5, 0)
        spin_layout.setSpacing(6)

        # s
        #  SPINBOX STYLESHEET: Explicit internal target routing prevents mouse click hijacking! 🌟
        spin_box_stylesheet = """
            /* Main base container footprint */
            QSpinBox {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 4px;
                color: #ffffff;
                font-family: monospace;
                font-size: 13px;
                font-weight: bold;
                min-width: 95px;
            }
            QSpinBox:hover {
                border: 1px solid #444444;
            }
            
            /* Clean structural positioning for the text cursor layer */
            QSpinBox::editor {
                background-color: #1e1e1e;
                color: #ffffff;
                padding-top: 3px;
                padding-bottom: 3px;
                padding-left: 5px;
                padding-right: 20px; /* Keep text safely clear of the buttons layer zone */
            }
            
            /* 🌟 THE REAL FIX PART 1: Explicitly lock the top right position for the Up Button 🌟 */
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 18px;
                height: 12px; /* Force an explicit height so it can NEVER collapse to zero! */
                border-left: 1px solid #333333;
                border-bottom: 1px solid #333333;
                background-color: #252525;
            }
            QSpinBox::up-button:hover {
                background-color: #353535;
            }
            QSpinBox::up-button:pressed {
                background-color: #151515;
            }
            
            /* 🌟 THE REAL FIX PART 2: Explicitly lock the bottom right position for the Down Button 🌟 */
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 18px;
                height: 12px; /* Force an explicit height to match the Up button perfectly */
                border-left: 1px solid #333333;
                background-color: #252525;
            }
            QSpinBox::down-button:hover {
                background-color: #353535;
            }
            QSpinBox::down-button:pressed {
                background-color: #151515;
            }
            
            /* Optional: Render clean native geometric triangle pointers inside the boxes */
            QSpinBox::up-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjE4IDE1IDEyIDkgNiAxNSIvPjwvc3ZnPg==);
                width: 10px;
                height: 10px;
            }
            QSpinBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjYgOSAxMiAxNSAxOCA5Ii8+PC9zdmc+);
                width: 10px;
                height: 10px;
            }

        """

        # 1. Custom Numeric Width Input Field Cell
        self.spin_width = QSpinBox()
        self.spin_width.setRange(10, 10000)  # Support massive high-res cameras safely
        self.spin_width.setValue(0)
        self.spin_width.setPrefix("W: ")
        self.spin_width.setSuffix(" px")
        self.spin_width.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.spin_width.setStyleSheet(spin_box_stylesheet)

        # Connect input changing events straight to our mapping engine
        self.spin_width.valueChanged.connect(self.on_spin_width_changed)
        spin_layout.addWidget(self.spin_width)

        # 2. Custom Numeric Height Input Field Cell
        self.spin_height = QSpinBox()
        self.spin_height.setRange(10, 10000)
        self.spin_height.setValue(0)
        self.spin_height.setPrefix("H: ")
        self.spin_height.setSuffix(" px")
        self.spin_height.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.spin_height.setStyleSheet(spin_box_stylesheet)
        self.spin_height.valueChanged.connect(self.on_spin_height_changed)
        spin_layout.addWidget(self.spin_height)

        # Add the spin container frame directly to your top toolbar stack right next to the dropdown!
        self.toolbar.addWidget(self.spin_container)

        # Shortened Toolbar Checkboxes
        self.chk_preserve = QCheckBox("Keep selection")
        self.chk_preserve.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.chk_preserve.setToolTip(
            "Conserve current selection box size and position coordinates across images."
        )
        self.chk_preserve.setChecked(True)
        self.toolbar.addWidget(self.chk_preserve)

        self.chk_overwrite = QCheckBox("Overwrite")
        self.chk_overwrite.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.chk_overwrite.setToolTip(
            "Directly overwrite original source image files instead of nesting copies in a subfolder."
        )
        self.chk_overwrite.setChecked(False)
        self.toolbar.addWidget(self.chk_overwrite)

        #  Custom Gear Button - Far Left & Borderless

        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_settings.setToolTip("Toggle configuration choices")
        self.btn_settings.setFixedSize(38, 38)  # Slightly larger bounding frame layout
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                font-size: 16px; /* Perfectly optimized glyph scaling */
                color: #888888;
                padding: 0px;   /* Clears implicit layout margins blocking edges */
                margin: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.04);
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
        self.lbl_telemetry_hud.setStyleSheet("""
            QLabel#TelemetryHUD {
                color: #888888;
                font-family: monospace;
                font-size: 13px;
                font-weight: bold;
                background-color: rgba(10, 10, 10, 0.75);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 10px;
            }
        """)

        self.lbl_telemetry_hud.hide()  # Hidden by default until bar collapses

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

        # -------------------------------------------------------------
        # CATEGORY 1: AUTOMATION & PERSISTENCE OPTIONS
        # -------------------------------------------------------------
        lbl_auto_section = QLabel("General")
        lbl_auto_section.setStyleSheet(
            "color: #888888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; border: none; margin-top: 15px; padding-bottom: 2px;"
        )
        self.drawer_layout.addWidget(lbl_auto_section)

        divider2 = QWidget()
        divider2.setMinimumHeight(1)
        divider2.setMaximumHeight(1)
        divider2.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.1); margin-bottom: 5px;"
        )
        self.drawer_layout.addWidget(divider2)

        self.cfg_remember_settings = QCheckBox("Save settings")
        self.cfg_remember_settings.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_remember_settings.setChecked(True)
        self.drawer_layout.addWidget(self.cfg_remember_settings)

        self.cfg_auto_folder = QCheckBox("Auto-open last folder")
        self.cfg_auto_folder.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_auto_folder.setChecked(False)
        self.drawer_layout.addWidget(self.cfg_auto_folder)

        # -------------------------------------------------------------
        # CATEGORY 2: SHOW / DISPLAY OPTIONS
        # -------------------------------------------------------------
        lbl_show_section = QLabel("Show / Display")
        lbl_show_section.setStyleSheet(
            "color: #888888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; border: none; margin-top: 10px; padding-bottom: 2px;"
        )
        self.drawer_layout.addWidget(lbl_show_section)

        divider1 = QWidget()
        divider1.setMinimumHeight(1)
        divider1.setMaximumHeight(1)
        divider1.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.1); margin-bottom: 5px;"
        )
        self.drawer_layout.addWidget(divider1)

        self.cfg_show_shortcuts = QCheckBox("Shortcuts Guide")
        self.cfg_show_shortcuts.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_show_shortcuts.setChecked(True)
        self.cfg_show_shortcuts.stateChanged.connect(self.apply_drawer_visibility_rules)
        self.drawer_layout.addWidget(self.cfg_show_shortcuts)

        self.cfg_show_toasts = QCheckBox("Notifications")
        self.cfg_show_toasts.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_show_toasts.setChecked(True)
        self.drawer_layout.addWidget(self.cfg_show_toasts)

        self.cfg_show_infobar = QCheckBox("Bottom Info Bar")
        self.cfg_show_infobar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_show_infobar.setChecked(True)
        self.cfg_show_infobar.stateChanged.connect(self.apply_drawer_visibility_rules)
        self.drawer_layout.addWidget(self.cfg_show_infobar)

        self.cfg_show_filename = QCheckBox("Image Filename")
        self.cfg_show_filename.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_show_filename.setChecked(True)
        self.cfg_show_filename.stateChanged.connect(
            self.update_resolution_metrics_display
        )
        self.drawer_layout.addWidget(self.cfg_show_filename)
        #  Target resolution display toggles
        self.cfg_show_imgsize = QCheckBox("Image Resolution")
        self.cfg_show_imgsize.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_show_imgsize.setChecked(True)
        self.cfg_show_imgsize.stateChanged.connect(
            self.update_resolution_metrics_display
        )
        self.drawer_layout.addWidget(self.cfg_show_imgsize)

        self.cfg_show_preview = QCheckBox("Preview")
        self.cfg_show_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_show_preview.setToolTip("Display Zoom Preview HUD")
        self.cfg_show_preview.setChecked(False)
        self.cfg_show_preview.stateChanged.connect(
            self.toggle_zoom_hud_window_visibility
        )
        self.drawer_layout.addWidget(self.cfg_show_preview)

        # -------------------------------------------------------------
        # CATEGORY 3: WINDOW LAYOUT MEMORY PERMANENCE
        # -------------------------------------------------------------
        lbl_layout_section = QLabel("Layout Memory")
        lbl_layout_section.setStyleSheet("""
            QLabel {
                color: #888888; 
                font-size: 11px; 
                font-weight: bold; 
                text-transform: uppercase; 
                letter-spacing: 1px; 
                border: none; 
                margin-top: 15px; 
                padding-bottom: 2px;
            }
        """)
        self.drawer_layout.addWidget(lbl_layout_section)

        divider3 = QWidget()
        divider3.setMinimumHeight(1)
        divider3.setMaximumHeight(1)
        divider3.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.1); margin-bottom: 5px;"
        )
        self.drawer_layout.addWidget(divider3)

        self.cfg_persist_main_win = QCheckBox("Main Window")
        self.cfg_persist_main_win.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_persist_main_win.setChecked(
            True
        )  # Checked by default for convenient startup
        self.drawer_layout.addWidget(self.cfg_persist_main_win)

        self.cfg_persist_hud_win = QCheckBox("Preview HUD")
        self.cfg_persist_hud_win.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cfg_persist_hud_win.setChecked(
            True
        )  # Checked by default for convenient startup
        self.drawer_layout.addWidget(self.cfg_persist_hud_win)

        ##########################
        self.drawer_layout.addStretch()

        # Positions the drawer completely tucked away out of sight behind the left edge
        self.drawer.setGeometry(-self.drawer_width, 0, self.drawer_width, 0)
        self.drawer_is_open = False

        # Interactive Selection Component Initialization
        self.crop_box_selector = QRubberBand(
            QRubberBand.Shape.Rectangle, self.image_display_container
        )

        self.drag_start_origin = QPoint()

        #  ADD THIS NEW COMMAND OVERLAY PANEL
        self.lbl_commands_overlay = QLabel(self.image_display_container)
        self.lbl_commands_overlay.hide()  # Will show once an image loads
        self.lbl_commands_overlay.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: monospace;
                font-size: 13px;
                font-weight: bold;
                background-color: rgba(10, 10, 10, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                padding: 10px;
            }
        """)
        # Populate the exact hotkey roadmap text
        self.lbl_commands_overlay.setText(
            "<b>[Hotkeys Layout]</b><br>"
            "[<b>Space</b>]       : Crop & Next Image<br>"
            "[<b>S</b>] / <b>Enter</b>]   : Crop & Stay<br>"
            "[<b>O</b>]           : Open Directory<br>"
            "[<b>I</b>]           : Open Image<br>"
            "[<b>F</b>] / [<b>→</b>]      : Skip Forward<br>"
            "[<b>B</b>] / [<b>←</b>]      : Skip Backward<br>"
            "[<b>R</b>]           : Rotate Clockwise<br>"
            "[<b>P</b>] Toggle Zoom HUD Preview<br>"
            "[<b>Esc</b>]         : Exit App<br><br>"
            "<i>Left-Click Drag: Draw Box<br>"
            "Right-Click Drag: Move Box</i>"
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
        self.lbl_splash_hud.setStyleSheet("""
            QLabel#SplashHUD {
                color: #ffffff;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                background-color: rgba(15, 15, 15, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 35px 50px;
                line-height: 150%;
            }
        """)

        # Build the exact typographic text block structure using clean Unicode pointers
        # We increase the padding gaps inside the inner line elements for greater vertical depth
        splash_text = (
            "<div style='text-align: center; font-family: \"Segoe UI\", -apple-system, sans-serif;'>"
            # Row 1: The Core Hotkey Prompt
            "<div style='margin-bottom: 22px;'>"
            "<span style='font-size: 26px; font-weight: bold; color: #ffffff;'>[O] &nbsp;▸&nbsp; Open Directory &nbsp;|&nbsp; [I] &nbsp;▸&nbsp; Open Image </span>"
            "</div>"
            # Row 2: Minimalist Small "OR" Divider 1
            "<div style='margin-bottom: 22px;'>"
            "<span style='font-size: 11px; font-weight: 800; color: #555555; letter-spacing: 2px; text-transform: uppercase;'>— or —</span>"
            "</div>"
            # Row 3: Drag Folder Guideline
            "<div style='margin-bottom: 22px;'>"
            "<span style='font-size: 19px; font-weight: 500; color: #bbbbbb;'>Drag & Drop a Directory Folder</span>"
            "</div>"
            # Row 4: Second Small "OR" Divider 2
            "<div style='margin-bottom: 22px;'>"
            "<span style='font-size: 11px; font-weight: 800; color: #555555; letter-spacing: 2px; text-transform: uppercase;'>— or —</span>"
            "</div>"
            # Row 5: Drag File Guideline (No bottom margin needed on the final line element)
            "<div>"
            "<span style='font-size: 19px; font-weight: 500; color: #bbbbbb;'>Drag & Drop an Image File</span>"
            "</div>"
            "</div>"
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
        self.lbl_crop_metrics = QLabel("")
        self.lbl_crop_metrics.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.lbl_crop_metrics.setStyleSheet(
            "color: #888888; font-family: monospace; font-size: 13px; font-weight: bold;"
        )
        self.info_bar.addWidget(self.lbl_crop_metrics)

        self.main_layout.addWidget(self.info_bar_widget)

        # -----------------------------------------------------------------

    # FILE PIPELINE AND RENDERING LOGIC
    # -----------------------------------------------------------------
    def select_directory(self):
        settings = QSettings("LossLessCropTeam", "LossLessCrop")
        # Pull down folder path registry memory fallback
        fallback_path = settings.value("last_used_folder", "", type=str)

        # Pass path memory directly as the starting browser location parameters argument
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Image Directory",
            fallback_path if os.path.exists(fallback_path) else "",
        )
        if not directory:
            return

        self.image_folder = directory
        folder_name = os.path.basename(os.path.normpath(directory))
        self.lbl_folder_name.setText(f"📁 {folder_name}")

        # 1. Define our verified, universally safe format whitelist
        SAFE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

        # Pull all files matching the whitelist extension pool
        raw_files = [
            f for f in os.listdir(directory) if f.lower().endswith(SAFE_EXTENSIONS)
        ]
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
                print(
                    f"[SECURITY SHIELD] Discarded fake, renamed, or corrupted image file: {filename}"
                )

        # 3. Viewport Dispatch
        if self.image_files:
            self.current_index = 0
            self.load_image_to_viewport()
        else:
            self.lbl_status.setText("No valid, readable images found in directory.")

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
        file_path = os.path.join(
            self.image_folder, self.image_files[self.current_index]
        )
        self.lbl_status.setText(
            f"[{self.current_index + 1}/{len(self.image_files)}] - {self.image_files[self.current_index]}"
        )

        # Load through Pillow memory pipelines safely
        self.current_pil_image = Image.open(file_path)
        self.refresh_display_canvas()

        # -----------------------------------------------------------------
        # RE-SYNC WORKSPACE SELECTION LAYER PRESERVATION
        # -----------------------------------------------------------------
        if self.chk_preserve.isChecked() and self.last_crop_geometry:
            # 1. Grab the fresh file extension properties
            _, file_ext = os.path.splitext(self.image_files[self.current_index].lower())
            is_jpeg = file_ext in (".jpg", ".jpeg")
            is_lossless = (
                (self.combo_engine.currentText() == "Lossless")
                and LOSSLESS_AVAILABLE
                and is_jpeg
            )

            if is_lossless:
                current_geom = self.last_crop_geometry

                #  OPTIMIZATION CHECK: Only calculate if the box is NOT already aligned
                is_already_snapped = (
                    (current_geom.x() % 16 == 0)
                    and (current_geom.y() % 16 == 0)
                    and (current_geom.width() % 16 == 0)
                    and (current_geom.height() % 16 == 0)
                )

                if not is_already_snapped:
                    # Snap the shunted selection box coordinates onto 16x16 grid markers
                    snap_x = round(current_geom.x() / 16) * 16
                    snap_y = round(current_geom.y() / 16) * 16
                    snap_w = round(current_geom.width() / 16) * 16
                    snap_h = round(current_geom.height() / 16) * 16

                    ratio_type = self.combo_ratio.currentText()
                    if ratio_type != "Freeform":
                        aspect_ratio = (
                            16.0 / 9.0
                            if ratio_type == "16:9 Widescreen"
                            else (4.0 / 3.0 if ratio_type == "4:3 Standard" else 1.0)
                        )
                        snap_h = round((snap_w / aspect_ratio) / 16) * 16

                    # Update our tracking memory with the safe, snapped grid block values
                    self.last_crop_geometry = QRect(snap_x, snap_y, snap_w, snap_h)
                    print("Snapping selection box")
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
        self.update_zoom_hud_payload()

    def refresh_display_canvas(self):
        if not self.current_pil_image:
            return

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
        ratio_type = self.combo_ratio.currentText()

        # FIX: Extract extension from tuple correctly using index [1]
        _, file_ext = os.path.splitext(self.image_files[self.current_index].lower())
        file_ext = file_ext.lower()
        is_jpeg = file_ext in (".jpg", ".jpeg")
        is_lossless = (
            (self.combo_engine.currentText() == "Lossless")
            and LOSSLESS_AVAILABLE
            and is_jpeg
        )

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
        is_lossless = (self.combo_engine.currentText() == "Lossless") and (
            ext in (".jpg", ".jpeg")
        )

        if is_lossless:
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
        file_ext = (
            file_ext.lower()
        )  # ✅ Normalizes .JPG / .JPEG down to lowercase strings
        is_jpeg = file_ext in (".jpg", ".jpeg")

        # Verify the actual internal file signature structure for JPEG
        is_true_jpeg = False
        if is_jpeg:
            try:
                with open(current_filepath, "rb") as f:
                    is_true_jpeg = f.read(3) == b"\xff\xd8\xff"
            except Exception:
                is_true_jpeg = False

        use_lossless = (
            (self.combo_engine.currentText() == "Lossless")
            and LOSSLESS_AVAILABLE
            and is_true_jpeg
        )

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

            current_dir = os.path.dirname(os.path.abspath(__file__))
            if os.name == "nt":
                bin_name = "jpegtran.exe"
            elif platform.system() == "Darwin":
                bin_name = "jpegtran_mac"
            else:
                bin_name = "jpegtran_linux"
            binary_path = os.path.join(current_dir, "binaries", bin_name)

            crop_argument = f"{crop_width}x{crop_height}+{crop_left}+{crop_top}"
            command = [
                binary_path,
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
            if not is_jpeg:
                print(
                    f" 📝 Format Notice : Non-JPEG format ({file_ext.upper()}) dynamically routed to Pillow engine."
                )
            elif not LOSSLESS_AVAILABLE:
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
                _, file_ext = os.path.splitext(
                    self.image_files[self.current_index].lower()
                )
                is_jpeg = file_ext in (".jpg", ".jpeg")
                is_lossless = (
                    (self.combo_engine.currentText() == "Lossless")
                    and LOSSLESS_AVAILABLE
                    and is_jpeg
                )

                if is_lossless:
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
        self.refresh_display_canvas()
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

    def closeEvent(self, event):
        """Standard PyQt window intercept routine executing right before closing down."""
        self.save_application_state()

        if hasattr(self, "zoom_hud") and self.zoom_hud:
            # This forces the borderless satellite HUD to cleanly terminate right alongside the main app
            self.zoom_hud.close()

        event.accept()

    def save_application_state(self):
        """Saves current tool states and path preferences into OS settings registries."""
        settings = QSettings("LossLessCropTeam", "LossLessCrop")

        # Always store the current folder directory no matter what

        if self.image_folder:
            settings.setValue("last_used_folder", self.image_folder)

        # ALWAYS write the master preference toggle first!
        master_remember = self.cfg_remember_settings.isChecked()
        settings.setValue("remember_settings", master_remember)
        # ALWAYS save geometry profiles, but we only restore them if 'Remember
        settings.setValue("main_window_geometry_blob", self.saveGeometry())

        if hasattr(self, "zoom_hud"):
            settings.setValue("hud_win_x", self.zoom_hud.x())
            settings.setValue("hud_win_y", self.zoom_hud.y())
            settings.setValue("hud_win_w", self.zoom_hud.width())
            settings.setValue("hud_win_h", self.zoom_hud.height())
            settings.setValue("show_preview_hud", self.cfg_show_preview.isChecked())

        # Write state variables if 'Remember settings' checkbox rule is active
        if master_remember:
            settings.setValue("persist_main_win", self.cfg_persist_main_win.isChecked())
            settings.setValue("persist_hud_win", self.cfg_persist_hud_win.isChecked())
            settings.setValue("auto_open_folder", self.cfg_auto_folder.isChecked())
            settings.setValue("show_shortcuts", self.cfg_show_shortcuts.isChecked())
            settings.setValue("show_toasts", self.cfg_show_toasts.isChecked())
            settings.setValue("show_infobar", self.cfg_show_infobar.isChecked())
            settings.setValue("show_filename", self.cfg_show_filename.isChecked())
            settings.setValue("show_imgsize", self.cfg_show_imgsize.isChecked())
            settings.setValue("conserve_selection", self.chk_preserve.isChecked())
            settings.setValue("overwrite_files", self.chk_overwrite.isChecked())
            settings.setValue("ratio_preference", self.combo_ratio.currentText())
            settings.setValue("engine_preference", self.combo_engine.currentText())
            settings.setValue("show_preview_hud", self.cfg_show_preview.isChecked())

    def load_application_state(self):
        """Restores previous session user state conditions on startup safely handling OS registries."""
        settings = QSettings("LossLessCropTeam", "LossLessCrop")

        # Helper function to safely translate OS string registries ("true"/"false") into Python booleans

        def safe_bool(val, default):
            if val is None:
                return default
            if isinstance(val, bool):
                return val
            if isinstance(val, int):
                return bool(val)
            return str(val).lower() in ("true", "1", "yes")

        # 1. Parse the master memory rule
        raw_remember = settings.value("remember_settings", True)
        remember = safe_bool(raw_remember, True)
        self.cfg_remember_settings.setChecked(remember)

        if remember:
            self.cfg_persist_main_win.setChecked(
                safe_bool(settings.value("persist_main_win"), True)
            )
            self.cfg_persist_hud_win.setChecked(
                safe_bool(settings.value("persist_hud_win"), True)
            )

            if self.cfg_persist_main_win.isChecked():
                main_geom_blob = settings.value("main_window_geometry_blob")
                if main_geom_blob:
                    self.restoreGeometry(main_geom_blob)

            if hasattr(self, "zoom_hud") and self.cfg_persist_hud_win.isChecked():
                hx = settings.value("hud_win_x")
                hy = settings.value("hud_win_y")
                hw = settings.value("hud_win_w")
                hh = settings.value("hud_win_h")
                if (
                    hx is not None
                    and hy is not None
                    and hw is not None
                    and hh is not None
                ):
                    self.zoom_hud.setGeometry(int(hx), int(hy), int(hw), int(hh))

            # 2. Extract and translate all Boolean states safely using EXACT matching keys
            self.cfg_auto_folder.setChecked(
                safe_bool(settings.value("auto_open_folder"), False)
            )
            self.cfg_show_shortcuts.setChecked(
                safe_bool(settings.value("show_shortcuts"), True)
            )
            self.cfg_show_toasts.setChecked(
                safe_bool(settings.value("show_toasts"), True)
            )
            self.cfg_show_infobar.setChecked(
                safe_bool(settings.value("show_infobar"), True)
            )
            self.cfg_show_filename.setChecked(
                safe_bool(settings.value("show_filename"), True)
            )
            self.cfg_show_imgsize.setChecked(
                safe_bool(settings.value("show_imgsize"), True)
            )
            self.chk_preserve.setChecked(
                safe_bool(settings.value("conserve_selection"), True)
            )
            self.chk_overwrite.setChecked(
                safe_bool(settings.value("overwrite_files"), False)
            )
            self.cfg_show_preview.setChecked(
                safe_bool(settings.value("show_preview_hud"), False)
            )

            show_hud = safe_bool(settings.value("show_preview_hud"), False)
            self.cfg_show_preview.setChecked(show_hud)
            if show_hud:
                self.toggle_zoom_hud_window_visibility()

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
        if (
            last_folder
            and isinstance(last_folder, str)
            and os.path.exists(last_folder)
            and remember
            and self.cfg_auto_folder.isChecked()
        ):
            self.image_folder = last_folder
            folder_name = os.path.basename(os.path.normpath(last_folder))
            self.lbl_folder_name.setText(f"📁 {folder_name}")

            SAFE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
            self.image_files = [
                f
                for f in os.listdir(last_folder)
                if f.lower().endswith(SAFE_EXTENSIONS)
            ]
            self.image_files.sort()

            if self.image_files:
                self.current_index = 0
                self.load_image_to_viewport()
        else:
            # 🌟 Startup is completely empty! Reveal our floating typographic guidelines HUD layout card 🌟
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

        # 4. Engine Validation Check: Is Lossless Active?
        _, file_ext = os.path.splitext(self.image_files[self.current_index].lower())
        is_lossless = (self.combo_engine.currentText() == "Lossless") and (
            file_ext in (".jpg", ".jpeg")
        )

        # Calculate what the grid mapped rectangle represents
        if is_lossless:
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
            if is_lossless:
                self.ghost_selector.setGeometry(snapped_rect)
                self.ghost_selector.show()
                self.ghost_selector.raise_()
            else:
                self.ghost_selector.hide()

        # 6. Source-Pixel Mapping for Spinbox Synchronization
        src_w, src_h = self.current_pil_image.size
        scale_x = src_w / pix_w
        scale_y = src_h / pix_h

        if is_lossless:
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

        _, file_ext = os.path.splitext(self.image_files[self.current_index].lower())
        is_lossless = (self.combo_engine.currentText() == "Lossless") and (
            file_ext in (".jpg", ".jpeg")
        )

        # 4. Enforce Math Transformations Directly in True Image Space
        if is_lossless:
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
            self.lbl_crop_metrics.setText("Crop Size: 0 x 0")
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
        offset_x, offset_y = (lbl_w - pix_w) // 2, (lbl_h - pix_h) // 2

        # 2. Map back to true source image pixel dimensions
        src_w, src_h = self.current_pil_image.size
        scale_x = src_w / pix_w
        scale_y = src_h / pix_h

        img_w = geom.width() * scale_x
        img_h = geom.height() * scale_y

        # 3. CRITICAL ASPECT RATIO UI CORRECTION
        ratio_type = self.combo_ratio.currentText()
        _, file_ext = os.path.splitext(self.image_files[self.current_index].lower())
        is_lossless = (self.combo_engine.currentText() == "Lossless") and (
            file_ext in (".jpg", ".jpeg")
        )

        if is_lossless:
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

        # 5. Synchronize the status bar HUD text labels
        self.lbl_crop_metrics.setText(f"Crop Size: {final_w} x {final_h}")

    def toggle_zoom_hud_window_visibility(self):
        """Displays or shuts down the floating zoom view based on checkbox rules."""
        if self.cfg_show_preview.isChecked():
            settings = QSettings("LossLessCropTeam", "LossLessCrop")

            # 1. Force the window into existence first so the OS layout initializes
            self.zoom_hud.show()
            self.zoom_hud.raise_()

            # 2. Immediately look up our explicit layout coordinates
            hx = settings.value("hud_win_x")
            hy = settings.value("hud_win_y")
            hw = settings.value("hud_win_w")
            hh = settings.value("hud_win_h")

            # 🌟 FIXED: If explicit dimensions exist, enforce them AFTER the window is shown!
            if hx is not None and hy is not None and hw is not None and hh is not None:
                self.zoom_hud.setGeometry(int(hx), int(hy), int(hw), int(hh))
            else:
                # Helpfully place it to the right of the main window ONLY if it's the first run ever
                main_geom = self.geometry()
                self.zoom_hud.setGeometry(
                    main_geom.right() + 10, main_geom.top() + 50, 250, 250
                )

            self.update_zoom_hud_payload()
        else:
            self.zoom_hud.hide()

    def update_zoom_hud_payload(self):
        """Calculates coordinates, slices memory, and passes the payload to the HUD."""
        # Abort if the HUD window is hidden or no image selection is active
        if not self.cfg_show_preview.isChecked() or self.crop_box_selector.isHidden():
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
                    file_path = os.path.join(
                        self.image_folder, self.image_files[self.current_index]
                    )
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

    def dropEvent(self, event):
        """Fires the exact millisecond the user lets go of their mouse drop cargo."""
        urls = event.mimeData().urls()
        if not urls:
            return

        # Extract the absolute local filesystem path from the very first dropped item
        dropped_path = urls[0].toLocalFile()
        if not dropped_path:
            return

        target_folder = ""
        target_starting_file = None

        # -------------------------------------------------------------
        # 🌟 INDEPENDENT PATH PARSING ENGINE AUTOMATION 🌟
        # -------------------------------------------------------------
        if os.path.isdir(dropped_path):
            # PIPELINE A: The asset dropped is a folder container raw
            target_folder = dropped_path

        elif os.path.isfile(dropped_path):
            # PIPELINE B: The asset dropped is an individual image file path
            # Isolate its parent folder directory, and capture the specific filename string
            target_folder = os.path.dirname(dropped_path)
            target_starting_file = os.path.basename(dropped_path)
        # -------------------------------------------------------------

        # Parse the folder queue matching our calculated target directory profiles
        if target_folder and os.path.exists(target_folder):
            self.image_folder = target_folder
            folder_name = os.path.basename(os.path.normpath(target_folder))
            self.lbl_folder_name.setText(f"📁 {folder_name}")

            # Enforce strict defensive extension format parsing whitelists
            SAFE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
            raw_files = [
                f
                for f in os.listdir(target_folder)
                if f.lower().endswith(SAFE_EXTENSIONS)
            ]
            raw_files.sort()

            # Run image header validation check passes to discard bad assets early
            self.image_files = []
            for filename in raw_files:
                test_path = os.path.join(self.image_folder, filename)
                try:
                    with Image.open(test_path) as img:
                        img.verify()
                    self.image_files.append(filename)
                except Exception:
                    pass

            # Workspace Viewport Integration Dispatchers
            if self.image_files:
                # If a single file was dropped, search the array index map to find its position
                if target_starting_file and (target_starting_file in self.image_files):
                    self.current_index = self.image_files.index(target_starting_file)
                else:
                    self.current_index = 0

                    # Force view refresh
                self.load_image_to_viewport()

                # Resync QSettings registry so the folder browser stays matched
                QSettings("LossLessCropTeam", "LossLessCrop").setValue(
                    "last_used_folder", self.image_folder
                )
            else:
                self.lbl_status.setText(
                    "No valid, readable images found in dropped payload."
                )

    def select_individual_image_file(self):
        """Manually picks a specific image file via shortcut, cacing up the surrounding directory."""
        settings = QSettings("LossLessCropTeam", "LossLessCrop")

        # Pull down our saved path registry memory fallback
        fallback_path = settings.value("last_used_folder", "", type=str)

        if not fallback_path or not os.path.exists(fallback_path):
            fallback_path = ""

        # Open individual file-centric prompt target filter dialog bounds
        file_filter = "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        selected_file_path, _ = QFileDialog.getOpenFileName(
            self, "Target Starting Image File", fallback_path, file_filter
        )

        if not selected_file_path:
            return  # User closed the prompt browser window smoothly

        # Deconstruct absolute parent folder string paths and target file properties
        target_folder = os.path.dirname(selected_file_path)
        target_filename = os.path.basename(selected_file_path)

        # Update application workspace states
        self.image_folder = target_folder
        folder_name = os.path.basename(os.path.normpath(target_folder))
        self.lbl_folder_name.setText(f"📁 {folder_name}")

        # Parse the surrounding container assets using strict whitelists shields
        SAFE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
        raw_files = [
            f for f in os.listdir(target_folder) if f.lower().endswith(SAFE_EXTENSIONS)
        ]
        raw_files.sort()

        # Execute header validation checking passes
        self.image_files = []
        for filename in raw_files:
            test_path = os.path.join(self.image_folder, filename)
            try:
                with Image.open(test_path) as img:
                    img.verify()
                self.image_files.append(filename)
            except Exception:
                pass

        # 🚀 WORKSPACE VIEWPORT LAYOUT DISPATCHERS
        if self.image_files:
            # INDEX LOOKUP LOOP: Find exactly where our selected photo sits in the queue array!
            if target_filename in self.image_files:
                self.current_index = self.image_files.index(target_filename)
            else:
                self.current_index = 0

            # Render the targeted image onto your canvas view layout channels
            self.load_image_to_viewport()

            # Resync persistent folder memory boundaries
            settings.setValue("last_used_folder", self.image_folder)
        else:
            self.lbl_status.setText(
                "No valid, readable images found in target folder directory."
            )

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
        _, ext = os.path.splitext(self.image_files[self.current_index].lower())

        # Lossless snapping
        if (self.combo_engine.currentText() == "Lossless") and (
            ext in (".jpg", ".jpeg")
        ):
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
