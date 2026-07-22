import dataclasses

from PyQt6.QtCore import QSettings  # Or PyQt5 / PySide6

from models.app_settings import AppSettings


class SettingsManager:
    def __init__(self, organization="LossLessCropTeam", application="LossLessCrop"):
        self.org = organization
        self.app = application

    def save(self, settings_model: AppSettings):
        """Serializes the data model fields out to OS native registries."""
        q_settings = QSettings(self.org, self.app)

        # Iterates through dataclass fields and pushes them cleanly into QSettings
        for key, value in dataclasses.asdict(settings_model).items():
            q_settings.setValue(key, value)

    def load(self) -> AppSettings:
        """Reads registry records and returns a fully initialized AppSettings object."""
        q_settings = QSettings(self.org, self.app)
        model = AppSettings()

        # Pull defaults from the AppSettings class definition dynamically
        for field in dataclasses.fields(AppSettings):
            if q_settings.contains(field.name):
                raw_value = q_settings.value(field.name)

                # Apply standard type casting rules safely
                if field.type is bool:
                    setattr(
                        model, field.name, self._safe_bool(raw_value, field.default)
                    )
                elif field.type is int and raw_value is not None:
                    setattr(model, field.name, int(raw_value))
                else:
                    setattr(model, field.name, raw_value)

        return model

    def _safe_bool(self, val, default) -> bool:
        """Helper to translate raw registry values safely into Python booleans."""
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        if isinstance(val, int):
            return bool(val)
        return str(val).lower() in ("true", "1", "yes")
