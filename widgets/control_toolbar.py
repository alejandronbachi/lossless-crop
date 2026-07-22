from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
)


class ControlToolbar(QFrame):
    def __init__(
        self, parent, image_manager, file_manager, ui_constants, pillow_available
    ):
        super().__init__(parent)
        self.main_app = parent
        self.image_manager = image_manager
        self.file_manager = file_manager
        self.ui_constants = ui_constants

        # Build the horizontal structural engine row
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self._build_ui(pillow_available)

    def _build_ui(self, pillow_available):
        # 1. Directory Loader Button
        self.main_app.lbl_folder_name = QPushButton("No directory loaded")
        self.main_app.lbl_folder_name.setStyleSheet(
            "font-weight: bold; color: #aaa; margin-left: 5px; min-width: 140px; text-align: left;"
        )
        self.main_app.lbl_folder_name.clicked.connect(self.main_app.select_directory)
        self.layout.addWidget(self.main_app.lbl_folder_name)

        self.layout.addStretch()

        # Shared Font Profile Configuration
        native_font = QFont("Segoe UI", 10)

        # 2. Engine Options Dropdown
        self.main_app.combo_engine = QComboBox()
        self.main_app.combo_engine.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.combo_engine.setToolTip(
            "Choose processing engine mode for saving operations."
        )
        self.main_app.combo_engine.setFont(native_font)
        self.main_app.combo_engine.view().setFont(native_font)

        if self.image_manager.is_lossless_available:
            self.main_app.combo_engine.addItem("Lossless")
        if pillow_available:
            self.main_app.combo_engine.addItem("Pixel-Perfect")
        if not self.image_manager.is_lossless_available and pillow_available:
            self.main_app.combo_engine.setCurrentText("Pixel-Perfect")
        self.layout.addWidget(self.main_app.combo_engine)

        # 3. Aspect Ratio Dropdown
        self.main_app.combo_ratio = QComboBox()
        self.main_app.combo_ratio.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.combo_ratio.setToolTip(
            "Force the cropping rectangle selection box to lock onto specific aspect ratios."
        )
        self.main_app.combo_ratio.setFont(native_font)
        self.main_app.combo_ratio.view().setFont(native_font)
        self.main_app.combo_ratio.addItems(
            ["Freeform", "1:1 Square", "16:9 Widescreen", "4:3 Standard"]
        )
        self.main_app.combo_ratio.currentIndexChanged.connect(
            self.main_app.on_ratio_changed
        )
        self.layout.addWidget(self.main_app.combo_ratio)

        # 4. Snap Feedback Dropdown
        self.main_app.combo_snap = QComboBox()
        self.main_app.combo_snap.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.combo_snap.setToolTip(
            "Select layout feedback mode for Left-Click mouse drawing."
        )
        self.main_app.combo_snap.setFont(native_font)
        self.main_app.combo_snap.view().setFont(native_font)
        self.main_app.combo_snap.addItems(
            ["No snap feedback", "Post-release snap", "Ghosting"]
        )
        self.layout.addWidget(self.main_app.combo_snap)

        # 5. Precision Manual Crop Spinboxes Component Layout
        self.main_app._updating_spinboxes = False

        self.main_app.spin_container = QFrame()
        self.main_app.spin_container.setStyleSheet(
            "background-color: transparent; border: none; margin: 0; padding: 0;"
        )
        spin_layout = QHBoxLayout(self.main_app.spin_container)
        spin_layout.setContentsMargins(5, 0, 5, 0)
        spin_layout.setSpacing(6)

        spin_box_stylesheet = self.file_manager.load_asset(
            self.ui_constants.STYLE_SPINBOXES, self.ui_constants.FOLDER_STYLES
        )

        # Width Numeric Field
        self.main_app.spin_width = QSpinBox()
        self.main_app.spin_width.setRange(10, 10000)
        self.main_app.spin_width.setValue(0)
        self.main_app.spin_width.setPrefix("W: ")
        self.main_app.spin_width.setSuffix(" px")
        self.main_app.spin_width.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.main_app.spin_width.setStyleSheet(spin_box_stylesheet)
        self.main_app.spin_width.valueChanged.connect(
            self.main_app.on_spin_width_changed
        )
        spin_layout.addWidget(self.main_app.spin_width)

        # Height Numeric Field
        self.main_app.spin_height = QSpinBox()
        self.main_app.spin_height.setRange(10, 10000)
        self.main_app.spin_height.setValue(0)
        self.main_app.spin_height.setPrefix("H: ")
        self.main_app.spin_height.setSuffix(" px")
        self.main_app.spin_height.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.main_app.spin_height.setStyleSheet(spin_box_stylesheet)
        self.main_app.spin_height.valueChanged.connect(
            self.main_app.on_spin_height_changed
        )
        spin_layout.addWidget(self.main_app.spin_height)

        self.layout.addWidget(self.main_app.spin_container)

        # 6. Toolbar Checkboxes
        self.main_app.chk_preserve = QCheckBox("Keep selection")
        self.main_app.chk_preserve.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.chk_preserve.setToolTip(
            "Conserve current selection box size and position coordinates across images."
        )
        self.main_app.chk_preserve.setChecked(True)
        self.layout.addWidget(self.main_app.chk_preserve)

        self.main_app.chk_overwrite = QCheckBox("Overwrite")
        self.main_app.chk_overwrite.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.chk_overwrite.setToolTip(
            "Directly overwrite original source image files instead of nesting copies in a subfolder."
        )
        self.main_app.chk_overwrite.setChecked(False)
        self.layout.addWidget(self.main_app.chk_overwrite)

        # 7. Configuration Gear Toggle Button
        self.main_app.btn_settings = QPushButton("⚙️")
        self.main_app.btn_settings.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.btn_settings.setToolTip("Toggle configuration choices")
        self.main_app.btn_settings.setFixedSize(38, 38)
        self.main_app.btn_settings.setStyleSheet(
            self.file_manager.load_asset(
                self.ui_constants.STYLE_BTN_SETTINGS, self.ui_constants.FOLDER_STYLES
            )
        )
        self.main_app.btn_settings.clicked.connect(self.main_app.toggle_settings_drawer)
        self.layout.addWidget(self.main_app.btn_settings)
