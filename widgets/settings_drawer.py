from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QFrame, QLabel, QVBoxLayout, QWidget

from config import ui_constants


class SettingsDrawer(
    QFrame
):  # 🚀 Modernized: Switched to QFrame to handle background QSS natively
    def __init__(self, parent, file_manager):
        # We explicitly pass the central widget as the parent to keep the floating canvas layout intact
        super().__init__(parent.central_widget)
        self.main_app = parent
        self.drawer_width = 240
        self.setObjectName("SettingsDrawer")

        # Style the drawer with semi-transparent obsidian glass aesthetics
        self.setStyleSheet(
            file_manager.load_asset(
                ui_constants.STYLE_DRAWER, ui_constants.FOLDER_STYLES
            )
        )

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
        lbl_auto_section = QLabel(ui_constants.LABEL_GENERAL_SECTION)
        lbl_auto_section.setStyleSheet(
            "color: #888888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; border: none; margin-top: 15px; padding-bottom: 2px;"
        )
        self.layout.addWidget(lbl_auto_section)
        self.layout.addWidget(self._create_divider())

        # Expose references back onto the main app window so its state checking code doesn't break
        self.main_app.cfg_remember_settings = QCheckBox(
            ui_constants.CHECKBOX_SAVE_SETTINGS_TEXT
        )
        self.main_app.cfg_remember_settings.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_remember_settings.setChecked(True)
        self.layout.addWidget(self.main_app.cfg_remember_settings)

        self.main_app.cfg_auto_folder = QCheckBox(
            ui_constants.CHECKBOX_AUTO_OPEN_FOLDER_TEXT
        )
        self.main_app.cfg_auto_folder.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_auto_folder.setChecked(False)
        self.layout.addWidget(self.main_app.cfg_auto_folder)

        # --- CATEGORY 2: SHOW / DISPLAY OPTIONS ---
        lbl_show_section = QLabel(ui_constants.LABEL_SHOW_SECTION)
        lbl_show_section.setStyleSheet(
            "color: #888888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; border: none; margin-top: 10px; padding-bottom: 2px;"
        )
        self.layout.addWidget(lbl_show_section)
        self.layout.addWidget(self._create_divider())

        self.main_app.cfg_show_shortcuts = QCheckBox(
            ui_constants.CHECKBOX_SHORTCUTS_GUIDE_TEXT
        )
        self.main_app.cfg_show_shortcuts.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_shortcuts.setChecked(True)
        self.main_app.cfg_show_shortcuts.stateChanged.connect(
            self.main_app.status_manager.sync_drawer_visibility_rules
        )
        self.layout.addWidget(self.main_app.cfg_show_shortcuts)

        self.main_app.cfg_show_toasts = QCheckBox(
            ui_constants.CHECKBOX_NOTIFICATIONS_TEXT
        )
        self.main_app.cfg_show_toasts.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_toasts.setChecked(True)
        self.layout.addWidget(self.main_app.cfg_show_toasts)

        self.main_app.cfg_show_infobar = QCheckBox(
            ui_constants.CHECKBOX_BOTTOM_INFOBAR_TEXT
        )
        self.main_app.cfg_show_infobar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_infobar.setChecked(True)
        self.main_app.cfg_show_infobar.stateChanged.connect(
            self.main_app.status_manager.sync_drawer_visibility_rules
        )
        self.layout.addWidget(self.main_app.cfg_show_infobar)

        self.main_app.cfg_show_filename = QCheckBox(
            ui_constants.CHECKBOX_IMAGE_FILENAME_TEXT
        )
        self.main_app.cfg_show_filename.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_filename.setChecked(True)
        # 🚀 FIX: Point callback away from deleted method straight to your centralized StatusManager engine
        self.main_app.cfg_show_filename.stateChanged.connect(
            self.main_app.status_manager.update_status_and_telemetry
        )
        self.layout.addWidget(self.main_app.cfg_show_filename)

        self.main_app.cfg_show_imgsize = QCheckBox(
            ui_constants.CHECKBOX_IMAGE_RESOLUTION_TEXT
        )
        self.main_app.cfg_show_imgsize.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_imgsize.setChecked(True)
        # 🚀 FIX: Point callback to StatusManager here too
        self.main_app.cfg_show_imgsize.stateChanged.connect(
            self.main_app.status_manager.update_status_and_telemetry
        )
        self.layout.addWidget(self.main_app.cfg_show_imgsize)

        self.main_app.cfg_show_preview = QCheckBox(ui_constants.CHECKBOX_PREVIEW_TEXT)
        self.main_app.cfg_show_preview.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_show_preview.setToolTip(ui_constants.TOOLTIP_PREVIEW)
        self.main_app.cfg_show_preview.setChecked(False)
        # 🚀 FIX: Redirect callback to your unified main window visibility toggle
        self.main_app.cfg_show_preview.stateChanged.connect(
            self.main_app.toggle_zoom_hud_window_visibility
        )
        self.layout.addWidget(self.main_app.cfg_show_preview)

        # --- CATEGORY 3: WINDOW LAYOUT MEMORY PERMANENCE ---
        lbl_layout_section = QLabel(ui_constants.LABEL_LAYOUT_SECTION)
        lbl_layout_section.setStyleSheet(
            "color: #888888; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; border: none; margin-top: 15px; padding-bottom: 2px;"
        )
        self.layout.addWidget(lbl_layout_section)
        self.layout.addWidget(self._create_divider())

        self.main_app.cfg_persist_main_win = QCheckBox(
            ui_constants.CHECKBOX_MAIN_WINDOW_TEXT
        )
        self.main_app.cfg_persist_main_win.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_persist_main_win.setChecked(True)
        self.layout.addWidget(self.main_app.cfg_persist_main_win)

        self.main_app.cfg_persist_hud_win = QCheckBox(
            ui_constants.CHECKBOX_PREVIEW_HUD_TEXT
        )
        self.main_app.cfg_persist_hud_win.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_app.cfg_persist_hud_win.setChecked(True)
        self.layout.addWidget(self.main_app.cfg_persist_hud_win)

        self.layout.addStretch()
