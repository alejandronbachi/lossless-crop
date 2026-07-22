import dataclasses
from pathlib import Path

from PyQt6.QtCore import QSettings  # Or PyQt5 / PySide6

from models.app_settings import AppSettings


class SettingsManager:
    def __init__(self, organization="LossLessCropTeam", application="LossLessCrop"):
        self.org = organization
        self.app = application
        self.current_settings = AppSettings()

    def save(self, settings_model: AppSettings):
        """Serializes the data model fields out to OS native registries."""

        # Use our tracked instance if no explicit model is passed in
        model_to_save = (
            settings_model if settings_model is not None else self.current_settings
        )
        q_settings = QSettings(self.org, self.app)

        # Iterates through dataclass fields and pushes them cleanly into QSettings
        for key, value in dataclasses.asdict(model_to_save).items():
            q_settings.setValue(key, value)

    def load(self) -> AppSettings:
        """Reads registry records, populates, and returns the AppSettings object."""
        q_settings = QSettings(self.org, self.app)
        model = AppSettings()

        for field in dataclasses.fields(AppSettings):
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
        return self.current_settings

    def _safe_bool(self, val, default) -> bool:
        """Helper to translate raw registry values safely into Python booleans."""
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        if isinstance(val, int):
            return bool(val)
        return str(val).lower() in ("true", "1", "yes")

    def save_last_used_folder(self, folder_path: str | Path):
        """Updates the folder target on our data model instantly."""
        self.current_settings.last_used_folder = str(folder_path)

    def get_fallback_path_str(self) -> str:
        """Helper for QFileDialog which reads straight from the active data model."""
        path_str = self.current_settings.last_used_folder
        if path_str and Path(path_str).exists():
            return path_str
        return ""
