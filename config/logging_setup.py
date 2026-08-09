import logging.config
import sys
from pathlib import Path

from PyQt6.QtCore import QCoreApplication, QStandardPaths


def initialize_logging():
    """Configures global self-cleaning rolling loggers for the application."""
    # 1. Standardize company branding for the directory path
    QCoreApplication.setOrganizationName("losslesscropteam")
    QCoreApplication.setApplicationName("LossLessCropApp")

    # 1. Retrieve the local app data root string from Qt
    raw_data_dir = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppLocalDataLocation
    )

    # 2. Convert to a pathlib Path object and create the directory safely
    app_data_dir = Path(raw_data_dir)
    app_data_dir.mkdir(parents=True, exist_ok=True)

    # 3. Establish the clean log file path using the / slash operator
    log_file_path = app_data_dir / "lossless_crop.log"

    # 3. Define the configuration profile schema
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": log_file_path,
                "encoding": "utf-8",
                "maxBytes": 5242880,  # 5 MB
                "backupCount": 3,
            },
        },
        "root": {"handlers": ["console", "file"], "level": "DEBUG"},
    }

    # 4. Inject settings into Python's logging core engine
    logging.config.dictConfig(LOGGING_CONFIG)
