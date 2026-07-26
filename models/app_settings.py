from dataclasses import dataclass


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

    # --- Persistent Configuration Toggles ---
    persist_main_win: bool = True
    persist_hud_win: bool = True
    auto_open_folder: bool = False
    show_shortcuts: bool = True
    show_toasts: bool = True
    show_infobar: bool = True
    show_filename: bool = True
    show_imgsize: bool = True
    conserve_selection: bool = False
    overwrite_files: bool = False

    # --- Dropdown ComboBox States ---
    ratio_preference: str = "Free"
    engine_preference: str = "Lossless"
    snap_preference: str = "Real-time snap"
