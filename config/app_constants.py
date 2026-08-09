import sys
from enum import IntEnum
from pathlib import Path

if getattr(sys, "frozen", False):
    APP_ROOT_DIR = Path(sys._MEIPASS)
else:
    APP_ROOT_DIR = Path(__file__).resolve().parent.parent

JPEG_EXTENSIONS = {".jpg", ".jpeg"}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
ALWAYS_LOSSLESS_IMAGE_EXTENSIONS = {".png", ".bmp"}

BINARY_WINDOWS = "jpegtran.exe"
BINARY_MAC = "jpegtran_mac"
BINARY_LINUX = "jpegtran_linux"

# This placeholder gets overwritten completely during the GitHub Actions build process
FORMSUBMIT_TOKEN = "DEV_PLACEHOLDER_TOKEN"


# Combo options
class EngineMode(IntEnum):
    LOSSLESS = 0
    PIXEL_PERFECT = 1


class SnapMode(IntEnum):
    REAL_TIME = 0
    POST_RELEASE = 1
    GHOSTING = 2


class CropRatioMode(IntEnum):
    FREEFORM = 0
    SQUARE_1_1 = 1
    WIDESCREEN_16_9 = 2
    STANDARD_4_3 = 3
    SOURCE_RATIO = 4


# --- Settings Attribute Names ---
SETTING_REMEMBER_SETTINGS = "remember_settings"
SETTING_LAST_USED_FOLDER = "last_used_folder"
SETTING_MAIN_WINDOW_GEOMETRY_BLOB = "main_window_geometry_blob"
SETTING_HUD_WIN_X = "hud_win_x"
SETTING_HUD_WIN_Y = "hud_win_y"
SETTING_HUD_WIN_W = "hud_win_w"
SETTING_HUD_WIN_H = "hud_win_h"
SETTING_SHOW_PREVIEW_HUD = "show_preview_hud"
SETTING_FIT_PREVIEW = "fit_preview"
SETTING_PERSIST_MAIN_WIN = "persist_main_win"
SETTING_PERSIST_HUD_WIN = "persist_hud_win"
SETTING_AUTO_OPEN_FOLDER = "auto_open_folder"
SETTING_SHOW_SHORTCUTS = "show_shortcuts"
SETTING_SHOW_TOASTS = "show_toasts"
SETTING_SHOW_INFOBAR = "show_infobar"
SETTING_SHOW_DIRECTORY = "show_directory"
SETTING_SHOW_FILENAME = "show_filename"
SETTING_SHOW_IMGSIZE = "show_imgsize"
SETTING_CONSERVE_SELECTION = "conserve_selection"
SETTING_OVERWRITE_FILES = "overwrite_files"
SETTING_RATIO_PREFERENCE = "ratio_preference"
SETTING_ENGINE_PREFERENCE = "engine_preference"
SETTING_SNAP_PREFERENCE = "snap_preference"
SETTING_DARK_THEME = "dark_theme"


# --- DYNAMIC SEMANTIC VERSION ENGINE ---
def get_application_version():
    """
    Dynamically captures the version tag.
    If compiled by GitHub Actions, it reads the embedded metadata.
    If running locally in dev mode, it fallbacks to a local dev string.
    """
    # 1. Look for an external version file generated during cloud packaging
    version_file = APP_ROOT_DIR / "version.txt"
    if version_file.exists():
        try:
            return version_file.read_text().strip()
        except Exception:
            pass

    # 2. Local development fallback identifier
    return "App"


# Global constant ready to be imported by any PyQt window handle
APP_VERSION = get_application_version()
