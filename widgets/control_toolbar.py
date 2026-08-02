from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QSpinBox,
    QToolButton,
)

from config import ui_constants
from widgets.sliding_switch import SlidingSwitch


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
        # 1 Toolbar Icons
        # Open folder
        self.main_app.btn_open_folder = QToolButton(self)
        self.main_app.btn_open_folder.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.btn_open_folder.setToolTip(ui_constants.TOOLTIP_SETTINGS)
        self.main_app.btn_open_folder.setFixedSize(38, 38)
        icon_path = self.file_manager.getSVGPathString("open_folder.svg")
        self.main_app.btn_open_folder.setIcon(QIcon(icon_path))
        self.main_app.btn_open_folder.setIconSize(QSize(32, 32))
        self.main_app.btn_open_folder.clicked.connect(self.main_app.select_directory)
        self.layout.addWidget(self.main_app.btn_open_folder)

        # Open Image
        self.main_app.btn_open_image = QToolButton(self)
        self.main_app.btn_open_image.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.btn_open_image.setToolTip(ui_constants.TOOLTIP_SETTINGS)
        self.main_app.btn_open_image.setFixedSize(38, 38)
        icon_path = self.file_manager.getSVGPathString("open_image.svg")
        self.main_app.btn_open_image.setIcon(QIcon(icon_path))
        self.main_app.btn_open_image.setIconSize(QSize(32, 32))
        self.main_app.btn_open_image.clicked.connect(
            self.main_app.select_individual_image_file
        )
        self.layout.addWidget(self.main_app.btn_open_image)
        # Crop
        self.main_app.btn_crop = QToolButton(self)
        self.main_app.btn_crop.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.btn_crop.setToolTip(ui_constants.TOOLTIP_SETTINGS)
        self.main_app.btn_crop.setFixedSize(38, 38)
        icon_path = self.file_manager.getSVGPathString("crop.svg")
        self.main_app.btn_crop.setIcon(QIcon(icon_path))
        self.main_app.btn_crop.setIconSize(QSize(32, 32))
        self.main_app.btn_crop.clicked.connect(self.main_app.process_and_execute_crop)
        self.layout.addWidget(self.main_app.btn_crop)

        # Crop and next
        self.main_app.btn_crop_next = QToolButton(self)
        self.main_app.btn_crop_next.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.btn_crop_next.setToolTip(ui_constants.TOOLTIP_SETTINGS)
        self.main_app.btn_crop_next.setFixedSize(38, 38)
        icon_path = self.file_manager.getSVGPathString("crop_next.svg")
        self.main_app.btn_crop_next.setIcon(QIcon(icon_path))
        self.main_app.btn_crop_next.setIconSize(QSize(32, 32))
        self.main_app.btn_crop_next.clicked.connect(self.main_app.crop_and_next)
        self.layout.addWidget(self.main_app.btn_crop_next)

        # Rotate
        self.main_app.btn_rotate = QToolButton(self)
        self.main_app.btn_rotate.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.btn_rotate.setToolTip(ui_constants.TOOLTIP_SETTINGS)
        self.main_app.btn_rotate.setFixedSize(38, 38)
        icon_path = self.file_manager.getSVGPathString("rotate.svg")
        self.main_app.btn_rotate.setIcon(QIcon(icon_path))
        self.main_app.btn_rotate.setIconSize(QSize(32, 32))
        self.main_app.btn_rotate.clicked.connect(self.main_app.rotate_current_image)
        self.layout.addWidget(self.main_app.btn_rotate)

        self.layout.addStretch()
        self.layout.addWidget(create_toolbar_divider(self))
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
        self.main_app.spin_container.setObjectName("spinContainer")
        spin_layout = QHBoxLayout(self.main_app.spin_container)
        spin_layout.setContentsMargins(5, 0, 5, 0)
        spin_layout.setSpacing(6)

        # Width Numeric Field
        self.main_app.spin_width = QSpinBox()
        self.main_app.spin_width.setRange(10, 10000)
        self.main_app.spin_width.setValue(0)
        self.main_app.spin_width.setPrefix(ui_constants.SPIN_WIDTH_PREFIX)
        self.main_app.spin_width.setSuffix(ui_constants.SPIN_WIDTH_SUFFIX)
        self.main_app.spin_width.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
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
        self.main_app.spin_height.editingFinished.connect(
            self.main_app.on_spin_height_changed
        )
        spin_layout.addWidget(self.main_app.spin_height)

        self.layout.addWidget(self.main_app.spin_container)

        self.layout.addStretch()
        self.layout.addWidget(create_toolbar_divider(self))
        self.layout.addStretch()

        # 6. Toolbar Checkboxes
        self.main_app.chk_preserve = SlidingSwitch(
            ui_constants.CHECKBOX_KEEP_SELECTION_TEXT
        )
        self.main_app.chk_preserve.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.chk_preserve.setToolTip(ui_constants.TOOLTIP_PRESERVE)
        self.main_app.chk_preserve.setChecked(True)
        self.layout.addWidget(self.main_app.chk_preserve)

        self.main_app.chk_overwrite = SlidingSwitch(
            ui_constants.CHECKBOX_OVERWRITE_TEXT
        )
        self.main_app.chk_overwrite.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.chk_overwrite.setToolTip(ui_constants.TOOLTIP_OVERWRITE)
        self.main_app.chk_overwrite.setChecked(False)
        self.layout.addWidget(self.main_app.chk_overwrite)

        self.layout.addStretch()
        self.layout.addWidget(create_toolbar_divider(self))
        self.layout.addStretch()

        # 7. Configuration Gear Toggle Button
        self.main_app.btn_settings = QToolButton(self)
        self.main_app.btn_settings.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.main_app.btn_settings.setToolTip(ui_constants.TOOLTIP_SETTINGS)
        self.main_app.btn_settings.setFixedSize(38, 38)
        icon_path = self.file_manager.getSVGPathString("gear.svg")
        self.main_app.btn_settings.setIcon(QIcon(icon_path))
        self.main_app.btn_settings.setIconSize(QSize(30, 30))
        self.main_app.btn_settings.clicked.connect(self.main_app.toggle_settings_drawer)
        self.layout.addWidget(self.main_app.btn_settings)


def create_toolbar_divider(parent_widget=None):
    """
    Generates a clean, pixel-perfect vertical divider line
    pre-mapped to the application layout's token color schema.
    """
    divider = QFrame(parent_widget)

    # 1. Force the frame to render as a standalone vertical separator line
    divider.setFrameShape(QFrame.Shape.VLine)
    divider.setFrameShadow(QFrame.Shadow.Plain)

    # 2. Prevent the vertical line from squishing out into 0 pixels
    divider.setLineWidth(1)

    # 3. Explicitly style the color to match your custom theme manager variables
    # This styles the VLine structure cleanly across dark frame sheets
    divider.setObjectName("divider")

    return divider
