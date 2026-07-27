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

from config import ui_constants


class ControlToolbar(QFrame):
    def __init__(
        self, parent, image_manager, file_manager, ui_constants_obj, pillow_available
    ):
        super().__init__(parent)
        self.main_app = parent
        self.image_manager = image_manager
        self.file_manager = file_manager
        self.ui_constants = ui_constants_obj

        # Build the horizontal structural engine row
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self._build_ui(pillow_available)

    def _build_ui(self, pillow_available):
        # 1. Directory Loader Button
        self.main_app.lbl_folder_name = QPushButton(ui_constants.TEXT_NO_DIRECTORY)
        self.main_app.lbl_folder_name.setFocusPolicy(Qt.FocusPolicy.NoFocus)
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
        self.main_app.combo_engine.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.combo_engine.setToolTip(ui_constants.TOOLTIP_ENGINE)
        self.main_app.combo_engine.setFont(native_font)
        self.main_app.combo_engine.view().setFont(native_font)

        if self.image_manager.is_lossless_available:
            self.main_app.combo_engine.addItem(ui_constants.ENGINE_LOSSLESS)
        if pillow_available:
            self.main_app.combo_engine.addItem(ui_constants.ENGINE_PIXEL_PERFECT)
        if not self.image_manager.is_lossless_available and pillow_available:
            self.main_app.combo_engine.setCurrentText(ui_constants.ENGINE_PIXEL_PERFECT)
        self.main_app.combo_engine.currentIndexChanged.connect(
            self.main_app.on_engine_changed
        )
        self.layout.addWidget(self.main_app.combo_engine)

        # 3. Aspect Ratio Dropdown
        self.main_app.combo_ratio = QComboBox()
        self.main_app.combo_ratio.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.combo_ratio.setToolTip(ui_constants.TOOLTIP_RATIO)
        self.main_app.combo_ratio.setFont(native_font)
        self.main_app.combo_ratio.view().setFont(native_font)
        self.main_app.combo_ratio.addItems(ui_constants.RATIO_ITEMS)
        self.main_app.combo_ratio.currentIndexChanged.connect(
            self.main_app.on_ratio_changed
        )
        self.layout.addWidget(self.main_app.combo_ratio)

        # 4. Snap Feedback Dropdown
        self.main_app.combo_snap = QComboBox()
        self.main_app.combo_snap.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.combo_snap.setToolTip(ui_constants.TOOLTIP_SNAP)
        self.main_app.combo_snap.setFont(native_font)
        self.main_app.combo_snap.view().setFont(native_font)
        self.main_app.combo_snap.addItems(ui_constants.SNAP_ITEMS)
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
        self.main_app.spin_width.setPrefix(ui_constants.SPIN_WIDTH_PREFIX)
        self.main_app.spin_width.setSuffix(ui_constants.SPIN_WIDTH_SUFFIX)
        self.main_app.spin_width.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.spin_width.setStyleSheet(spin_box_stylesheet)
        self.main_app.spin_width.editingFinished.connect(
            self.main_app.on_spin_width_changed
        )
        spin_layout.addWidget(self.main_app.spin_width)

        # Height Numeric Field
        self.main_app.spin_height = QSpinBox()
        self.main_app.spin_height.setRange(10, 10000)
        self.main_app.spin_height.setValue(0)
        self.main_app.spin_height.setPrefix(ui_constants.SPIN_HEIGHT_PREFIX)
        self.main_app.spin_height.setSuffix(ui_constants.SPIN_HEIGHT_SUFFIX)
        self.main_app.spin_height.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.spin_height.setStyleSheet(spin_box_stylesheet)
        self.main_app.spin_height.editingFinished.connect(
            self.main_app.on_spin_height_changed
        )
        spin_layout.addWidget(self.main_app.spin_height)

        self.layout.addWidget(self.main_app.spin_container)

        # 6. Toolbar Checkboxes
        self.main_app.chk_preserve = QCheckBox(
            ui_constants.CHECKBOX_KEEP_SELECTION_TEXT
        )
        self.main_app.chk_preserve.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.chk_preserve.setToolTip(ui_constants.TOOLTIP_PRESERVE)
        self.main_app.chk_preserve.setChecked(True)
        self.layout.addWidget(self.main_app.chk_preserve)

        self.main_app.chk_overwrite = QCheckBox(ui_constants.CHECKBOX_OVERWRITE_TEXT)
        self.main_app.chk_overwrite.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.chk_overwrite.setToolTip(ui_constants.TOOLTIP_OVERWRITE)
        self.main_app.chk_overwrite.setChecked(False)
        self.layout.addWidget(self.main_app.chk_overwrite)

        # 7. Configuration Gear Toggle Button
        self.main_app.btn_settings = QPushButton("⚙️")
        self.main_app.btn_settings.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.btn_settings.setToolTip(ui_constants.TOOLTIP_SETTINGS)
        self.main_app.btn_settings.setFixedSize(38, 38)
        self.main_app.btn_settings.setStyleSheet(
            self.file_manager.load_asset(
                self.ui_constants.STYLE_BTN_SETTINGS, self.ui_constants.FOLDER_STYLES
            )
        )
        self.main_app.btn_settings.clicked.connect(self.main_app.toggle_settings_drawer)
        self.layout.addWidget(self.main_app.btn_settings)
