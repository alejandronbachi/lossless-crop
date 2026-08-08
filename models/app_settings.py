from dataclasses import dataclass, field

from config import app_constants


@dataclass
class AppSettings:
    # --- Persistence Booleans ---
    remember_settings: bool = True
    remember_window: bool = True
    remember_preview: bool = True

    # --- Structural Preferences ---
    last_used_folder: str = ""
    main_window_geometry_blob: bytes = b""

    # --- HUD Geometry Dimensions ---
    hud_win_x: int = 100
    hud_win_y: int = 100
    hud_win_w: int = 200
    hud_win_h: int = 200
    show_preview_hud: bool = True
    fit_preview: bool = False

    # --- Persistent Configuration Toggles ---
    persist_main_win: bool = True
    persist_hud_win: bool = True
    auto_open_folder: bool = False
    show_shortcuts: bool = True
    show_toasts: bool = True
    show_infobar: bool = True
    show_directory: bool = True
    show_filename: bool = True
    show_imgsize: bool = True
    conserve_selection: bool = False
    overwrite_files: bool = False
    dark_theme: bool = True

    # --- Dropdown ComboBox States ---
    ratio_preference: int = app_constants.CropRatioMode.FREEFORM
    engine_preference: int = app_constants.EngineMode.LOSSLESS
    snap_preference: int = app_constants.SnapMode.REAL_TIME
    # --- Recent Files History ---
    # 2. This safely creates a unique, empty list for every instance
    recent_items_history: list[str] = field(default_factory=list)
