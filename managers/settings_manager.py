import dataclasses
from collections.abc import Callable
from pathlib import Path
from typing import Any, get_origin

from PyQt6.QtCore import QObject, QSettings, QSignalBlocker
from PyQt6.QtWidgets import QAbstractButton, QComboBox, QWidget

from config import app_constants, ui_constants
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

    def bind_checkbox(self, widget: QAbstractButton, attr_name: str) -> None:
        """Binds a QAbstractButton (QCheckBox/SlidingSwitch) to a boolean property on AppSettings with real-time sync."""
        if not hasattr(self.model, attr_name):
            raise AttributeError(f"AppSettings has no attribute '{attr_name}'")

        self._bindings.append((widget, attr_name, "checkbox"))

        # Real-time UI -> Model synchronization callback
        def _on_toggled(checked: bool):
            setattr(self.model, attr_name, checked)

        widget.toggled.connect(_on_toggled)

    def bind_combobox(self, widget: QComboBox, attr_name: str) -> None:
        """Binds a QComboBox using its hidden item data property payload to AppSettings with real-time sync."""
        if not hasattr(self.model, attr_name):
            raise AttributeError(f"AppSettings has no attribute '{attr_name}'")

        self._bindings.append((widget, attr_name, "combobox"))

        # Real-time UI -> Model synchronization callback via internal Data payload
        def _on_data_changed(index: int):
            # Extract the raw integer enum bound to the row instead of translated text characters
            enum_value = widget.itemData(index)
            if enum_value is not None:
                setattr(self.model, attr_name, enum_value)

        widget.currentIndexChanged.connect(_on_data_changed)

    def apply_to_ui(self) -> None:
        """Populates all bound UI widgets with language-agnostic data values from AppSettings model."""
        for widget, attr_name, widget_type in self._bindings:
            value = getattr(self.model, attr_name)
            blocker = QSignalBlocker(
                widget
            )  # Prevent feedback loop during populating UI
            try:
                if widget_type == "checkbox" and isinstance(widget, QAbstractButton):
                    widget.setChecked(bool(value))
                elif widget_type == "combobox" and isinstance(widget, QComboBox):
                    # 1. Handle unexpected dictionaries (extract data if possible, or fall back)
                    if isinstance(value, dict):
                        # Extract the inner value if it matches your new system's structure
                        # e.g., value.get("current_selection") or value.get("value")
                        value = value.get("current_selection", None)

                    # 2. Guard against invalid, unhashable, or missing data types
                    if value is None or isinstance(value, (list, set)):
                        index = 0  # Default to first item
                    else:
                        try:
                            index = widget.findData(value)
                        except TypeError:
                            index = 0  # Catch-all for incompatible custom types

                    # 3. Apply index, defaulting to safety if the value wasn't found in choices
                    if index != -1:
                        widget.setCurrentIndex(index)
                    else:
                        widget.setCurrentIndex(0)
            finally:
                del blocker

    def update_model_from_ui(self) -> None:
        """Reads all bound UI widgets and writes underlying Enum integers back to AppSettings model."""
        for widget, attr_name, widget_type in self._bindings:
            if widget_type == "checkbox" and isinstance(widget, QAbstractButton):
                setattr(self.model, attr_name, widget.isChecked())
            elif widget_type == "combobox" and isinstance(widget, QComboBox):
                # Clean write pass mapping the language-agnostic property to storage configurations
                setattr(self.model, attr_name, widget.currentData())


class SettingsManager:
    """
    Manages persistence to OS registry via QSettings and coordinates
    SettingsBinder for UI model binding.
    """

    ALWAYS_PERSISTED_FIELDS = {
        app_constants.SETTING_REMEMBER_SETTINGS,
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
        self.max_recent_items = 10  # Strict ceiling constraint
        self.current_settings = AppSettings()
        self.binder = SettingsBinder(self.current_settings)
        # 1. Type-Mapping Registry Strategy
        # Maps Python types to safe, standalone normalizing parsers
        self._type_parsers: dict[Any, Callable[[Any, Any], Any]] = {
            bool: lambda raw, default: self._safe_bool(raw, default),
            int: lambda raw, default: self._safe_int(raw, default),
            str: lambda raw, default: self._safe_str(raw, default),
            bytes: lambda raw, default: self._safe_bytes(raw, default),
            list: self._parse_list_type,
        }

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
            main_window.cfg_show_directory, app_constants.SETTING_SHOW_DIRECTORY
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
        binder.bind_checkbox(
            main_window.cfg_fit_preview, app_constants.SETTING_FIT_PREVIEW
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
        binder.bind_checkbox(
            main_window.cfg_dark_theme, app_constants.SETTING_DARK_THEME
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

    def _safe_int(self, val: Any, default: int) -> int:
        """Helper to translate raw registry values safely into Python integers."""
        if val is None:
            return default
        if isinstance(val, int) and not isinstance(val, bool):
            return val
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def _safe_str(self, val: Any, default: str) -> str:
        """Helper to translate raw registry values safely into Python strings."""
        if val is None:
            return default
        if isinstance(val, str):
            return val
        try:
            return str(val)
        except (ValueError, TypeError):
            return default

    def _safe_bytes(self, val: Any, default: bytes) -> bytes:
        """Helper to translate raw registry values safely into Python bytes."""
        if val is None:
            return default
        if isinstance(val, bytes):
            return val
        if hasattr(val, "data") and callable(val.data):
            try:
                return bytes(val.data())
            except Exception:
                pass
        if isinstance(val, bytearray):
            return bytes(val)
        if isinstance(val, str):
            try:
                return val.encode("utf-8")
            except Exception:
                pass
        return default

    def save_last_used_folder(self, folder_path: str | Path) -> None:
        """Updates the folder target on our data model instantly."""
        self.current_settings.last_used_folder = str(folder_path)

    def get_fallback_path_str(self) -> str:
        """Helper for QFileDialog which reads straight from the active data model."""
        path_str = self.current_settings.last_used_folder
        if path_str and Path(path_str).exists():
            return path_str
        return ""

    def add_to_recent(self, raw_path: str):
        """Updates the in-memory dataclass history queue."""
        if not raw_path:
            return

        target_path = Path(raw_path).resolve()
        if not target_path.exists():
            return

        path_str = str(target_path)
        current_list = self.get_recent_paths()  # Gets the live filtered list

        # Deduplicate
        if path_str in current_list:
            current_list.remove(path_str)

        # Slide item to the top
        current_list.insert(0, path_str)
        current_list = current_list[: self.max_recent_items]

        # Update the memory state
        self.current_settings.recent_items_history = current_list

    def get_recent_paths(self) -> list[str]:
        """Retrieves and self-heals the list in memory."""
        raw_list = self.current_settings.recent_items_history

        # Filter ghost files using pathlib
        valid_paths = [p for p in raw_list if Path(p).exists()]

        # Self-healing: If ghost files were found, update the memory state immediately
        if len(valid_paths) != len(raw_list):
            self.current_settings.recent_items_history = valid_paths

        return valid_paths

    def load(self) -> AppSettings:
        """Reads registry records, populates, and returns the AppSettings object."""
        q_settings = QSettings(self.org, self.app)
        model = AppSettings()

        # 2. Guard against missing initial remember rule state safely
        remember_settings_val = model.remember_settings
        if q_settings.contains(app_constants.SETTING_REMEMBER_SETTINGS):
            remember_settings_val = self._safe_bool(
                q_settings.value(app_constants.SETTING_REMEMBER_SETTINGS),
                model.remember_settings,
            )

        for field in dataclasses.fields(AppSettings):
            # 3. Guard Clause: Skip field parsing evaluation immediately if retention limits apply
            if (
                not remember_settings_val
                and field.name not in self.ALWAYS_PERSISTED_FIELDS
            ):
                continue

            if not q_settings.contains(field.name):
                continue

            raw_value = q_settings.value(field.name)
            field_base_type = get_origin(field.type) or field.type
            field_default = (
                field.default
                if field.default is not dataclasses.MISSING
                else (
                    field.default_factory()
                    if field.default_factory is not dataclasses.MISSING
                    else None
                )
            )

            # 4. Route type extraction dynamically through the strategic parser map or field name
            if field.name == app_constants.SETTING_RATIO_PREFERENCE:
                parsed_value = self._parse_ratio_preference(raw_value, field_default)
            elif field.name == app_constants.SETTING_ENGINE_PREFERENCE:
                parsed_value = self._parse_engine_preference(raw_value, field_default)
            elif field.name == app_constants.SETTING_SNAP_PREFERENCE:
                parsed_value = self._parse_snap_preference(raw_value, field_default)
            else:
                parser = self._type_parsers.get(field_base_type)
                if parser:
                    parsed_value = parser(raw_value, field_default)
                else:
                    if raw_value is not None and isinstance(raw_value, field_base_type):
                        parsed_value = raw_value
                    else:
                        parsed_value = field_default

            # 5. Final type verification safeguard to prevent type mismatches (e.g. string vs enum/data)
            if parsed_value is not None and not isinstance(
                parsed_value, field_base_type
            ):
                try:
                    if field_base_type == int:
                        parsed_value = int(parsed_value)
                    elif field_base_type == bool:
                        parsed_value = bool(parsed_value)
                    elif field_base_type == str:
                        parsed_value = str(parsed_value)
                    else:
                        parsed_value = field_default
                except Exception:
                    parsed_value = field_default

            setattr(model, field.name, parsed_value)

        self.current_settings = model
        self.binder.model = model  # Re-link binder to newly loaded instance
        return self.current_settings

    # --- Extracted Specialized Normalizing Helpers ---

    def _parse_ratio_preference(self, raw: Any, default: Any) -> int:
        """Parses ratio preference handling both IntEnum/int and legacy string literals."""
        if isinstance(raw, int) and not isinstance(raw, bool):
            try:
                return app_constants.CropRatioMode(raw)
            except ValueError:
                return default
        if isinstance(raw, str):
            mapping = {
                ui_constants.RATIO_FREEFORM: app_constants.CropRatioMode.FREEFORM,
                ui_constants.RATIO_SQUARE: app_constants.CropRatioMode.SQUARE_1_1,
                ui_constants.RATIO_WIDESCREEN: app_constants.CropRatioMode.WIDESCREEN_16_9,
                ui_constants.RATIO_STANDARD: app_constants.CropRatioMode.STANDARD_4_3,
                ui_constants.RATIO_SOURCE: app_constants.CropRatioMode.SOURCE_RATIO,
                "Freeform": app_constants.CropRatioMode.FREEFORM,
                "1:1 Square": app_constants.CropRatioMode.SQUARE_1_1,
                "16:9 Widescreen": app_constants.CropRatioMode.WIDESCREEN_16_9,
                "4:3 Standard": app_constants.CropRatioMode.STANDARD_4_3,
                "Source Ratio": app_constants.CropRatioMode.SOURCE_RATIO,
            }
            return mapping.get(raw, default)
        return default

    def _parse_engine_preference(self, raw: Any, default: Any) -> int:
        """Parses engine preference handling both IntEnum/int and legacy string literals."""
        if isinstance(raw, int) and not isinstance(raw, bool):
            try:
                return app_constants.EngineMode(raw)
            except ValueError:
                return default
        if isinstance(raw, str):
            mapping = {
                ui_constants.ENGINE_LOSSLESS: app_constants.EngineMode.LOSSLESS,
                ui_constants.ENGINE_PIXEL_PERFECT: app_constants.EngineMode.PIXEL_PERFECT,
                "Lossless": app_constants.EngineMode.LOSSLESS,
                "Pixel-Perfect": app_constants.EngineMode.PIXEL_PERFECT,
            }
            return mapping.get(raw, default)
        return default

    def _parse_snap_preference(self, raw: Any, default: Any) -> int:
        """Parses snap preference handling both IntEnum/int and legacy string literals."""
        if isinstance(raw, int) and not isinstance(raw, bool):
            try:
                return app_constants.SnapMode(raw)
            except ValueError:
                return default
        if isinstance(raw, str):
            mapping = {
                ui_constants.SNAP_REAL_TIME: app_constants.SnapMode.REAL_TIME,
                ui_constants.SNAP_POST_RELEASE: app_constants.SnapMode.POST_RELEASE,
                ui_constants.SNAP_GHOSTING: app_constants.SnapMode.GHOSTING,
                "Real-time snap": app_constants.SnapMode.REAL_TIME,
                "Post-release snap": app_constants.SnapMode.POST_RELEASE,
                "Ghosting": app_constants.SnapMode.GHOSTING,
            }
            return mapping.get(raw, default)
        return default

    def _parse_list_type(self, raw_value: Any, _: Any) -> list:
        """Forces normalization because QSettings can return string arrays or strings."""
        if isinstance(raw_value, list):
            return raw_value
        if isinstance(raw_value, str) and raw_value:
            return [raw_value]
        return []
