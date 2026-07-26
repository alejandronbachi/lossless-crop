from pathlib import Path

APP_ROOT_DIR = Path(__file__).resolve().parent.parent
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

# --- Settings Attribute Names ---
SETTING_REMEMBER_SETTINGS = "remember_settings"
SETTING_REMEMBER_WINDOW = "remember_window"
SETTING_REMEMBER_PREVIEW = "remember_preview"
SETTING_LAST_USED_FOLDER = "last_used_folder"
SETTING_MAIN_WINDOW_GEOMETRY_BLOB = "main_window_geometry_blob"
SETTING_HUD_WIN_X = "hud_win_x"
SETTING_HUD_WIN_Y = "hud_win_y"
SETTING_HUD_WIN_W = "hud_win_w"
SETTING_HUD_WIN_H = "hud_win_h"
SETTING_SHOW_PREVIEW_HUD = "show_preview_hud"
SETTING_PERSIST_MAIN_WIN = "persist_main_win"
SETTING_PERSIST_HUD_WIN = "persist_hud_win"
SETTING_AUTO_OPEN_FOLDER = "auto_open_folder"
SETTING_SHOW_SHORTCUTS = "show_shortcuts"
SETTING_SHOW_TOASTS = "show_toasts"
SETTING_SHOW_INFOBAR = "show_infobar"
SETTING_SHOW_FILENAME = "show_filename"
SETTING_SHOW_IMGSIZE = "show_imgsize"
SETTING_CONSERVE_SELECTION = "conserve_selection"
SETTING_OVERWRITE_FILES = "overwrite_files"
SETTING_RATIO_PREFERENCE = "ratio_preference"
SETTING_ENGINE_PREFERENCE = "engine_preference"
SETTING_SNAP_PREFERENCE = "snap_preference"
