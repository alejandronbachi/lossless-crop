from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from config import ui_constants
from managers import theme_manager
from widgets.sliding_switch import SlidingSwitch


class SettingsDrawer(
    QFrame
):  # 🚀 Modernized: Switched to QFrame to handle background QSS natively
    def __init__(self, parent, file_manager):
        # We explicitly pass the central widget as the parent to keep the floating canvas layout intact
        super().__init__(parent.central_widget)
        self.main_app = parent
        self.drawer_width = 240
        self.setObjectName("SettingsDrawer")

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
        divider.setObjectName("divider")
        return divider

    def _build_ui(self):
        # --- CATEGORY 1: AUTOMATION & PERSISTENCE OPTIONS ---
        lbl_auto_section = QLabel(ui_constants.LABEL_GENERAL_SECTION)
        lbl_auto_section.setProperty("class", "sectionHeading")
        lbl_auto_section.setObjectName("lblAutoSection")
        self.layout.addWidget(lbl_auto_section)
        self.layout.addWidget(self._create_divider())

        # Expose references back onto the main app window so its state checking code doesn't break
        self.main_app.cfg_remember_settings = SlidingSwitch(
            ui_constants.CHECKBOX_SAVE_SETTINGS_TEXT
        )
        self.main_app.cfg_remember_settings.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_remember_settings.setChecked(True)
        self.layout.addWidget(self.main_app.cfg_remember_settings)

        self.main_app.cfg_auto_folder = SlidingSwitch(
            ui_constants.CHECKBOX_AUTO_OPEN_FOLDER_TEXT
        )
        self.main_app.cfg_auto_folder.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_auto_folder.setChecked(False)
        self.layout.addWidget(self.main_app.cfg_auto_folder)

        self.main_app.cfg_fit_preview = SlidingSwitch(
            ui_constants.CHECKBOX_FIT_PREVIEW_TEXT
        )
        self.main_app.cfg_fit_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_fit_preview.setChecked(False)
        self.main_app.cfg_fit_preview.toggled.connect(
            self.main_app.status_manager.invalidate_ui_state
        )
        self.layout.addWidget(self.main_app.cfg_fit_preview)

        self.main_app.cfg_dark_theme = SlidingSwitch(ui_constants.CHECKBOX_DARK_THEME)
        self.main_app.cfg_dark_theme.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_dark_theme.setChecked(False)
        self.main_app.cfg_dark_theme.toggled.connect(theme_manager.toggle_theme)
        self.layout.addWidget(self.main_app.cfg_dark_theme)

        # --- CATEGORY 2: SHOW / DISPLAY OPTIONS ---
        lbl_show_section = QLabel(ui_constants.LABEL_SHOW_SECTION)
        lbl_show_section.setProperty("class", "sectionHeading")
        lbl_show_section.setObjectName("lblShowSection")
        self.layout.addWidget(lbl_show_section)
        self.layout.addWidget(self._create_divider())

        self.main_app.cfg_show_shortcuts = SlidingSwitch(
            ui_constants.CHECKBOX_SHORTCUTS_GUIDE_TEXT
        )
        self.main_app.cfg_show_shortcuts.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_shortcuts.setChecked(True)
        self.main_app.cfg_show_shortcuts.toggled.connect(
            self.main_app.status_manager.sync_drawer_visibility_rules
        )
        self.layout.addWidget(self.main_app.cfg_show_shortcuts)

        self.main_app.cfg_show_toasts = SlidingSwitch(
            ui_constants.CHECKBOX_NOTIFICATIONS_TEXT
        )
        self.main_app.cfg_show_toasts.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_toasts.setChecked(True)
        self.layout.addWidget(self.main_app.cfg_show_toasts)

        self.main_app.cfg_show_infobar = SlidingSwitch(
            ui_constants.CHECKBOX_BOTTOM_INFOBAR_TEXT
        )
        self.main_app.cfg_show_infobar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_infobar.setChecked(True)
        self.main_app.cfg_show_infobar.toggled.connect(
            self.main_app.status_manager.sync_drawer_visibility_rules
        )
        self.layout.addWidget(self.main_app.cfg_show_infobar)

        self.main_app.cfg_show_directory = SlidingSwitch(
            ui_constants.CHECKBOX_IMAGE_DIRECTORY_TEXT
        )
        self.main_app.cfg_show_directory.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_directory.setChecked(True)
        self.main_app.cfg_show_directory.toggled.connect(
            self.main_app.status_manager.sync_drawer_visibility_rules
        )
        self.layout.addWidget(self.main_app.cfg_show_directory)

        self.main_app.cfg_show_filename = SlidingSwitch(
            ui_constants.CHECKBOX_IMAGE_FILENAME_TEXT
        )
        self.main_app.cfg_show_filename.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_filename.setChecked(True)
        self.main_app.cfg_show_filename.toggled.connect(
            self.main_app.status_manager.sync_drawer_visibility_rules
        )
        self.layout.addWidget(self.main_app.cfg_show_filename)

        self.main_app.cfg_show_imgsize = SlidingSwitch(
            ui_constants.CHECKBOX_IMAGE_RESOLUTION_TEXT
        )
        self.main_app.cfg_show_imgsize.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_imgsize.setChecked(True)
        self.main_app.cfg_show_imgsize.toggled.connect(
            self.main_app.status_manager.sync_drawer_visibility_rules
        )
        self.layout.addWidget(self.main_app.cfg_show_imgsize)

        self.main_app.cfg_show_preview = SlidingSwitch(
            ui_constants.CHECKBOX_PREVIEW_TEXT
        )
        self.main_app.cfg_show_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_preview.setToolTip(ui_constants.TOOLTIP_PREVIEW)
        self.main_app.cfg_show_preview.setChecked(False)
        self.main_app.cfg_show_preview.toggled.connect(
            self.main_app.toggle_zoom_hud_window_visibility
        )
        self.layout.addWidget(self.main_app.cfg_show_preview)

        # --- CATEGORY 3: WINDOW LAYOUT MEMORY PERMANENCE ---
        lbl_layout_section = QLabel(ui_constants.LABEL_LAYOUT_SECTION)
        lbl_layout_section.setProperty("class", "sectionHeading")
        lbl_layout_section.setObjectName("lblLayoutSection")
        self.layout.addWidget(lbl_layout_section)
        self.layout.addWidget(self._create_divider())

        self.main_app.cfg_persist_main_win = SlidingSwitch(
            ui_constants.CHECKBOX_MAIN_WINDOW_TEXT
        )
        self.main_app.cfg_persist_main_win.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_persist_main_win.setChecked(True)
        self.layout.addWidget(self.main_app.cfg_persist_main_win)

        self.main_app.cfg_persist_hud_win = SlidingSwitch(
            ui_constants.CHECKBOX_PREVIEW_HUD_TEXT
        )
        self.main_app.cfg_persist_hud_win.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_persist_hud_win.setChecked(True)
        self.layout.addWidget(self.main_app.cfg_persist_hud_win)

        self.layout.addStretch()
