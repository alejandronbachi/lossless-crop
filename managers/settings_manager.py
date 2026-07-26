import dataclasses
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, QSettings, QSignalBlocker
from PyQt6.QtWidgets import QCheckBox, QComboBox, QWidget

from config import app_constants
from models.app_settings import AppSettings


class SettingsBinder(QObject):
    """
    Acts as a binding bridge between PyQt UI controls (QCheckBox, QComboBox)
    and the AppSettings dataclass model. Handles automatic two-way synchronization,
    eliminating manual state mapping boilerplate in the main window.
    """

    def __init__(self, settings_model: AppSettings, parent: QObject = None):
        super().__init__(parent)
        self.model = settings_model
        # List of binding tuples: (widget, attribute_name, widget_type)
        self._bindings: list[tuple[QWidget, str, str]] = []

    def bind_checkbox(self, widget: QCheckBox, attr_name: str) -> None:
        """Binds a QCheckBox to a boolean property on AppSettings with real-time sync."""
        if not hasattr(self.model, attr_name):
            raise AttributeError(f"AppSettings has no attribute '{attr_name}'")

        self._bindings.append((widget, attr_name, "checkbox"))

        # Real-time UI -> Model synchronization callback
        def _on_toggled(checked: bool):
            setattr(self.model, attr_name, checked)

        widget.toggled.connect(_on_toggled)

    def bind_combobox(self, widget: QComboBox, attr_name: str) -> None:
        """Binds a QComboBox to a string property on AppSettings with real-time sync."""
        if not hasattr(self.model, attr_name):
            raise AttributeError(f"AppSettings has no attribute '{attr_name}'")

        self._bindings.append((widget, attr_name, "combobox"))

        # Real-time UI -> Model synchronization callback
        def _on_text_changed(text: str):
            setattr(self.model, attr_name, text)

        widget.currentTextChanged.connect(_on_text_changed)

    def apply_to_ui(self) -> None:
        """Populates all bound UI widgets with current values from AppSettings model."""
        for widget, attr_name, widget_type in self._bindings:
            value = getattr(self.model, attr_name)
            blocker = QSignalBlocker(
                widget
            )  # Prevent feedback loop during populating UI
            try:
                if widget_type == "checkbox" and isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif widget_type == "combobox" and isinstance(widget, QComboBox):
                    index = widget.findText(str(value))
                    if index != -1:
                        widget.setCurrentIndex(index)
            finally:
                del blocker

    def update_model_from_ui(self) -> None:
        """Reads all bound UI widgets and writes values back to AppSettings model."""
        for widget, attr_name, widget_type in self._bindings:
            if widget_type == "checkbox" and isinstance(widget, QCheckBox):
                setattr(self.model, attr_name, widget.isChecked())
            elif widget_type == "combobox" and isinstance(widget, QComboBox):
                setattr(self.model, attr_name, widget.currentText())


class SettingsManager:
    """
    Manages persistence to OS registry via QSettings and coordinates
    SettingsBinder for UI model binding.
    """

    ALWAYS_PERSISTED_FIELDS = {
        app_constants.SETTING_REMEMBER_SETTINGS,
        app_constants.SETTING_REMEMBER_WINDOW,
        app_constants.SETTING_REMEMBER_PREVIEW,
        app_constants.SETTING_LAST_USED_FOLDER,
        app_constants.SETTING_MAIN_WINDOW_GEOMETRY_BLOB,
        app_constants.SETTING_HUD_WIN_X,
        app_constants.SETTING_HUD_WIN_Y,
        app_constants.SETTING_HUD_WIN_W,
        app_constants.SETTING_HUD_WIN_H,
        app_constants.SETTING_SHOW_PREVIEW_HUD,
        app_constants.SETTING_PERSIST_MAIN_WIN,
        app_constants.SETTING_PERSIST_HUD_WIN,
    }

    def __init__(
        self, organization: str = "LossLessCropTeam", application: str = "LossLessCrop"
    ):
        self.org = organization
        self.app = application
        self.current_settings = AppSettings()
        self.binder = SettingsBinder(self.current_settings)

    def bind_ui(self, main_window) -> None:
        """Registers all main window UI controls with SettingsBinder."""
        binder = self.binder

        # Category 1: General & Automation
        binder.bind_checkbox(
            main_window.cfg_remember_settings, app_constants.SETTING_REMEMBER_SETTINGS
        )
        binder.bind_checkbox(
            main_window.cfg_auto_folder, app_constants.SETTING_AUTO_OPEN_FOLDER
        )

        # Category 2: Display Toggles
        binder.bind_checkbox(
            main_window.cfg_show_shortcuts, app_constants.SETTING_SHOW_SHORTCUTS
        )
        binder.bind_checkbox(
            main_window.cfg_show_toasts, app_constants.SETTING_SHOW_TOASTS
        )
        binder.bind_checkbox(
            main_window.cfg_show_infobar, app_constants.SETTING_SHOW_INFOBAR
        )
        binder.bind_checkbox(
            main_window.cfg_show_filename, app_constants.SETTING_SHOW_FILENAME
        )
        binder.bind_checkbox(
            main_window.cfg_show_imgsize, app_constants.SETTING_SHOW_IMGSIZE
        )
        binder.bind_checkbox(
            main_window.cfg_show_preview, app_constants.SETTING_SHOW_PREVIEW_HUD
        )

        # Category 3: Window Persistence
        binder.bind_checkbox(
            main_window.cfg_persist_main_win, app_constants.SETTING_PERSIST_MAIN_WIN
        )
        binder.bind_checkbox(
            main_window.cfg_persist_hud_win, app_constants.SETTING_PERSIST_HUD_WIN
        )

        # Category 4: Toolbar Controls
        binder.bind_checkbox(
            main_window.chk_preserve, app_constants.SETTING_CONSERVE_SELECTION
        )
        binder.bind_checkbox(
            main_window.chk_overwrite, app_constants.SETTING_OVERWRITE_FILES
        )

        # Category 5: Dropdowns
        binder.bind_combobox(
            main_window.combo_ratio, app_constants.SETTING_RATIO_PREFERENCE
        )
        binder.bind_combobox(
            main_window.combo_engine, app_constants.SETTING_ENGINE_PREFERENCE
        )
        binder.bind_combobox(
            main_window.combo_snap, app_constants.SETTING_SNAP_PREFERENCE
        )

    def save(self, settings_model: AppSettings = None) -> None:
        """Serializes the data model fields out to OS native registries."""
        model_to_save = (
            settings_model if settings_model is not None else self.current_settings
        )
        q_settings = QSettings(self.org, self.app)

        as_dict = dataclasses.asdict(model_to_save)
        for key, value in as_dict.items():
            if (
                not model_to_save.remember_settings
                and key not in self.ALWAYS_PERSISTED_FIELDS
            ):
                continue
            q_settings.setValue(key, value)

    def load(self) -> AppSettings:
        """Reads registry records, populates, and returns the AppSettings object."""
        q_settings = QSettings(self.org, self.app)
        model = AppSettings()

        remember_settings_val = model.remember_settings
        if q_settings.contains("remember_settings"):
            remember_settings_val = self._safe_bool(
                q_settings.value("remember_settings"), model.remember_settings
            )

        for field in dataclasses.fields(AppSettings):
            if (
                not remember_settings_val
                and field.name not in self.ALWAYS_PERSISTED_FIELDS
            ):
                continue

            if q_settings.contains(field.name):
                raw_value = q_settings.value(field.name)

                if field.type is bool:
                    setattr(
                        model, field.name, self._safe_bool(raw_value, field.default)
                    )
                elif field.type is int and raw_value is not None:
                    setattr(model, field.name, int(raw_value))
                else:
                    setattr(model, field.name, raw_value)

        self.current_settings = model
        self.binder.model = model  # Re-link binder to newly loaded instance
        return self.current_settings

    def capture_window_geometry(self, main_window, hud_window=None) -> None:
        """Captures window and HUD geometry states directly into current AppSettings model."""
        self.current_settings.main_window_geometry_blob = main_window.saveGeometry()

        if hud_window is not None:
            self.current_settings.hud_win_x = hud_window.x()
            self.current_settings.hud_win_y = hud_window.y()
            self.current_settings.hud_win_w = hud_window.width()
            self.current_settings.hud_win_h = hud_window.height()

    def restore_window_geometry(self, main_window, hud_window=None) -> None:
        """Restores window and HUD geometry states from current AppSettings model."""
        if (
            self.current_settings.persist_main_win
            and self.current_settings.main_window_geometry_blob
        ):
            main_window.restoreGeometry(self.current_settings.main_window_geometry_blob)

        if hud_window is not None:
            if self.current_settings.persist_hud_win:
                hud_window.setGeometry(
                    self.current_settings.hud_win_x,
                    self.current_settings.hud_win_y,
                    self.current_settings.hud_win_w,
                    self.current_settings.hud_win_h,
                )
            else:
                main_geom = main_window.geometry()
                hud_window.setGeometry(
                    main_geom.right() + 10, main_geom.top() + 50, 250, 250
                )

    def _safe_bool(self, val: Any, default: bool) -> bool:
        """Helper to translate raw registry values safely into Python booleans."""
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        if isinstance(val, int):
            return bool(val)
        return str(val).lower() in ("true", "1", "yes")

    def save_last_used_folder(self, folder_path: str | Path) -> None:
        """Updates the folder target on our data model instantly."""
        self.current_settings.last_used_folder = str(folder_path)

    def get_fallback_path_str(self) -> str:
        """Helper for QFileDialog which reads straight from the active data model."""
        path_str = self.current_settings.last_used_folder
        if path_str and Path(path_str).exists():
            return path_str
        return ""
