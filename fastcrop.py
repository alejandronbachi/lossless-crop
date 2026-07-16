import sys
import os
from PIL import Image
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QFileDialog, QPushButton, 
                             QComboBox, QCheckBox, QRubberBand, QSizePolicy, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QPixmap, QImage, QKeyEvent, QColor
from PyQt6.QtCore import Qt, QRect, QSize, QPoint, QTimer

class FastCropApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FastCrop - Desktop Image Editor")
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
        
    def init_ui(self):
        # Master Structural Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # -------------------------------------------------------------
        # TOP SYSTEM TOOLBAR CONTROL PANELS
        # -------------------------------------------------------------
        self.toolbar = QHBoxLayout()
        
        self.btn_open = QPushButton("Open Folder")
        self.btn_open.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_open.clicked.connect(self.select_directory)
        self.toolbar.addWidget(self.btn_open)
        
        # NEW: Shows the folder name directly next to the button
        self.lbl_folder_name = QLabel("No directory loaded.")
        self.lbl_folder_name.setStyleSheet("font-weight: bold; color: #aaa; margin-left: 5px;")
        self.toolbar.addWidget(self.lbl_folder_name)
        
        self.toolbar.addStretch()
        
        # Aspect Ratio Optimization Control Dropdowns
        self.toolbar.addWidget(QLabel("Force Ratio:"))
        self.combo_ratio = QComboBox()
        self.combo_ratio.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_ratio.addItems(["Freeform", "1:1 Square", "16:9 Widescreen", "4:3 Standard"])
        self.combo_ratio.currentIndexChanged.connect(self.on_ratio_changed)
        self.toolbar.addWidget(self.combo_ratio)
        
        # Workspace Retention Checkboxes
        self.chk_preserve = QCheckBox("Conserve selection box position/size")
        self.chk_preserve.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.chk_preserve.setChecked(True)
        self.toolbar.addWidget(self.chk_preserve)
        
        self.chk_overwrite = QCheckBox("Overwrite original files")
        self.chk_overwrite.setFocusPolicy(Qt.FocusPolicy.NoFocus) 
        self.chk_overwrite.setChecked(False)
        self.toolbar.addWidget(self.chk_overwrite)
        
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
        self.notification_timer.setInterval(2000)
        self.notification_timer.setSingleShot(True)
        self.notification_timer.timeout.connect(self.lbl_notification.hide)
        # Bottom info bar
        self.info_bar = QHBoxLayout()
        self.lbl_status = QLabel("Ready. Open a folder to start cropping.")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #bbb; font-size: 15px; font-weight: 500; padding: 5px 0px;")
        self.info_bar.addWidget(self.lbl_status)
        self.main_layout.addLayout(self.info_bar)


    # -----------------------------------------------------------------
    # FILE PIPELINE AND RENDERING LOGIC
    # -----------------------------------------------------------------
    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if not directory:
            return
            
        self.image_folder = directory
        
        # Extract just the last folder name from the absolute path
        folder_name = os.path.basename(os.path.normpath(directory))
        self.lbl_folder_name.setText(f"📁 {folder_name}")
        
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
        self.image_files = [f for f in os.listdir(directory) if f.lower().endswith(valid_extensions)]
        self.image_files.sort()
        
        if self.image_files:
            self.current_index = 0
            self.load_image_to_viewport()
        else:
            self.lbl_status.setText("No compatible images found in chosen directory.")


    def load_image_to_viewport(self):
        if not (0 <= self.current_index < len(self.image_files)):
            return
            
        file_path = os.path.join(self.image_folder, self.image_files[self.current_index])
        self.lbl_status.setText(f"[{self.current_index + 1}/{len(self.image_files)}] - {self.image_files[self.current_index]}")
        
        # Load through Pillow memory pipelines safely
        self.current_pil_image = Image.open(file_path)
        self.refresh_display_canvas()
        
        # Handle persistent selection boundaries box rules
        if self.chk_preserve.isChecked() and self.last_crop_geometry:
            self.crop_box_selector.setGeometry(self.last_crop_geometry)
            self.crop_box_selector.show()
            self.crop_box_selector.raise_() 
        else:
            self.crop_box_selector.hide()
            self.last_crop_geometry = None
        
        self.position_commands_overlay()
        self.lbl_commands_overlay.show()
        self.lbl_commands_overlay.raise_()

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
        if not self.image_display_container.pixmap():
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
            else:
                self.is_moving_box = False

    def on_mouse_move(self, event):
        if self.drag_start_origin.isNull():
            return
            
        current_point = event.position().toPoint()

        if self.is_moving_box:
            # Right Click Logic: Move the selection box without resizing it
            delta = current_point - self.drag_start_origin
            current_geometry = self.crop_box_selector.geometry()
            
            # Calculate new position coordinates
            new_x = current_geometry.x() + delta.x()
            new_y = current_geometry.y() + delta.y()
            
            # Constrain to prevent moving completely outside the display canvas boundaries
            new_x = max(0, min(new_x, self.image_display_container.width() - current_geometry.width()))
            new_y = max(0, min(new_y, self.image_display_container.height() - current_geometry.height()))
            
            # Apply layout movement update
            self.crop_box_selector.move(new_x, new_y)
            self.last_crop_geometry = self.crop_box_selector.geometry()
            self.drag_start_origin = current_point  # Update base point for smooth tracking delta
            
        else:
            # Left Click Logic: Handle original box drawing/resizing
            current_rect = QRect(self.drag_start_origin, current_point).normalized()
            ratio_type = self.combo_ratio.currentText()
            
            if ratio_type == "Freeform":
                self.crop_box_selector.setGeometry(current_rect)
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
                self.crop_box_selector.setGeometry(new_rect)

    def on_mouse_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.is_moving_box:
            if self.crop_box_selector.width() > 5 and self.crop_box_selector.height() > 5:
                self.last_crop_geometry = self.crop_box_selector.geometry()
            self.drag_start_origin = QPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            self.is_moving_box = False
            self.drag_start_origin = QPoint()
        self.lbl_commands_overlay.show()
        self.lbl_commands_overlay.raise_()

    def position_commands_overlay(self):
        """Positions the command overlay in the top right corner of the container."""
        self.lbl_commands_overlay.adjustSize()
        padding = 15
        x = self.image_display_container.width() - self.lbl_commands_overlay.width() - padding
        y = padding
        self.lbl_commands_overlay.move(max(0, x), y)

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
        # Process structural image matrix slicing via pillow arrays
        cropped_image = self.current_pil_image.crop((crop_left, crop_top, crop_right, crop_bottom))
        
        # Original asset fallback defaults
        original_name = self.image_files[self.current_index]
        
        # SAVE PATH REDIRECTION LOGIC
        if self.chk_overwrite.isChecked():
            # If overwrite is active, save directly over the source file
            output_filepath = os.path.join(self.image_folder, original_name)
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
        
        # Write asset back to filesystem
        cropped_image.save(output_filepath)
        
        # Reload the newly saved file back into memory so navigation doesn't throw errors
        self.current_pil_image = Image.open(output_filepath)
        
        if self.chk_overwrite.isChecked():
            # Force the UI to instantly display the newly cropped version of the image
            self.refresh_display_canvas()
            # Clear the old box selection so it doesn't float over the newly resized canvas
            self.crop_box_selector.hide()
            self.last_crop_geometry = None
        return True



    def rotate_current_image(self):
        if self.current_pil_image:
            self.current_pil_image = self.current_pil_image.rotate(-90, expand=True)
            self.refresh_display_canvas()

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
        if self.lbl_notification.isVisible():
            parent_w = self.image_display_container.width()
            parent_h = self.image_display_container.height()
            x = (parent_w - self.lbl_notification.width()) // 2
            y = (parent_h - self.lbl_notification.height()) // 2
            self.lbl_notification.move(x, y)        

    def show_center_notification(self, text):
        """Displays a cinematic floating alert in the exact middle of the image area."""
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
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FastCropApp()
    window.show()
    sys.exit(app.exec())
  
