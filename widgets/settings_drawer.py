from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from config.ui_constants import FOLDER_STYLES, STYLE_DRAWER


class SettingsDrawer(QWidget):
    def __init__(self, parent, file_manager):
        # We explicitly pass the central widget as the parent to keep the floating canvas layout intact
        super().__init__(parent.central_widget)
        self.main_app = parent
        self.drawer_width = 240
        self.setObjectName("SettingsDrawer")

        # Style the drawer with semi-transparent obsidian glass aesthetics
        self.setStyleSheet(file_manager.load_asset(STYLE_DRAWER, FOLDER_STYLES))

        # Build the structural menu layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 20, 15, 20)
        self.layout.setSpacing(12)

        self._build_ui()

        # Positions the drawer completely tucked away out of sight behind the left edge
        self.setGeometry(-self.drawer_width, 0, self.drawer_width, 0)

    def _create_divider(self):
        divider = QWidget()
        divider.setMinimumHeight(1)
        divider.setMaximumHeight(1)
        divider.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.1); margin-bottom: 5px;"
        )
        return divider

    def _build_ui(self):
        # --- CATEGORY 1: AUTOMATION & PERSISTENCE OPTIONS ---
        lbl_auto_section = QLabel("General")
        lbl_auto_section.setStyleSheet(
            "color: #888888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; border: none; margin-top: 15px; padding-bottom: 2px;"
        )
        self.layout.addWidget(lbl_auto_section)
        self.layout.addWidget(self._create_divider())

        # Expose references back onto the main app window so its state checking code doesn't break
        self.main_app.cfg_remember_settings = QCheckBox("Save settings")
        self.main_app.cfg_remember_settings.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_remember_settings.setChecked(True)
        self.layout.addWidget(self.main_app.cfg_remember_settings)

        self.main_app.cfg_auto_folder = QCheckBox("Auto-open last folder")
        self.main_app.cfg_auto_folder.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_auto_folder.setChecked(False)
        self.layout.addWidget(self.main_app.cfg_auto_folder)

        # --- CATEGORY 2: SHOW / DISPLAY OPTIONS ---
        lbl_show_section = QLabel("Show / Display")
        lbl_show_section.setStyleSheet(
            "color: #888888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; border: none; margin-top: 10px; padding-bottom: 2px;"
        )
        self.layout.addWidget(lbl_show_section)
        self.layout.addWidget(self._create_divider())

        self.main_app.cfg_show_shortcuts = QCheckBox("Shortcuts Guide")
        self.main_app.cfg_show_shortcuts.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_shortcuts.setChecked(True)
        self.main_app.cfg_show_shortcuts.stateChanged.connect(
            self.main_app.apply_drawer_visibility_rules
        )
        self.layout.addWidget(self.main_app.cfg_show_shortcuts)

        self.main_app.cfg_show_toasts = QCheckBox("Notifications")
        self.main_app.cfg_show_toasts.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_toasts.setChecked(True)
        self.layout.addWidget(self.main_app.cfg_show_toasts)

        self.main_app.cfg_show_infobar = QCheckBox("Bottom Info Bar")
        self.main_app.cfg_show_infobar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_infobar.setChecked(True)
        self.main_app.cfg_show_infobar.stateChanged.connect(
            self.main_app.apply_drawer_visibility_rules
        )
        self.layout.addWidget(self.main_app.cfg_show_infobar)

        self.main_app.cfg_show_filename = QCheckBox("Image Filename")
        self.main_app.cfg_show_filename.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_filename.setChecked(True)
        self.main_app.cfg_show_filename.stateChanged.connect(
            self.main_app.update_telemetry_label
        )
        self.layout.addWidget(self.main_app.cfg_show_filename)

        self.main_app.cfg_show_imgsize = QCheckBox("Image Resolution")
        self.main_app.cfg_show_imgsize.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_imgsize.setChecked(True)
        self.main_app.cfg_show_imgsize.stateChanged.connect(
            self.main_app.update_telemetry_label
        )
        self.layout.addWidget(self.main_app.cfg_show_imgsize)

        self.main_app.cfg_show_preview = QCheckBox("Preview")
        self.main_app.cfg_show_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_preview.setToolTip("Display Zoom Preview HUD")
        self.main_app.cfg_show_preview.setChecked(False)
        self.main_app.cfg_show_preview.stateChanged.connect(
            self.main_app.toggle_zoom_hud_window_visibility
        )
        self.layout.addWidget(self.main_app.cfg_show_preview)

        # --- CATEGORY 3: WINDOW LAYOUT MEMORY PERMANENCE ---
        lbl_layout_section = QLabel("Layout Memory")
        lbl_layout_section.setStyleSheet(
            "color: #888888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; border: none; margin-top: 15px; padding-bottom: 2px;"
        )
        self.layout.addWidget(lbl_layout_section)
        self.layout.addWidget(self._create_divider())

        self.main_app.cfg_persist_main_win = QCheckBox("Main Window")
        self.main_app.cfg_persist_main_win.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_persist_main_win.setChecked(True)
        self.layout.addWidget(self.main_app.cfg_persist_main_win)

        self.main_app.cfg_persist_hud_win = QCheckBox("Preview HUD")
        self.main_app.cfg_persist_hud_win.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_persist_hud_win.setChecked(True)
        self.layout.addWidget(self.main_app.cfg_persist_hud_win)

        self.layout.addStretch()

    def paintEvent(self, event):
        """Forces custom QWidget subclasses to honor stylesheet background rules."""
        from PyQt6.QtGui import QPainter
        from PyQt6.QtWidgets import QStyle, QStyleOption

        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)
