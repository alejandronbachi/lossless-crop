import logging

from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


# 1. Global State Variables (Module Scope)
current_theme = "dark"
current_palette = {}
_file_manager = None  # Holds the saved reference to your file manager

# 2. Design Token Dictionary Mapping
# --- Unified Dual-Theme Palettes for LossLess Crop ---
THEME_PALETTES = {
    "dark": {
        # --- QPainter Grid Canvas ---
        "@CANVAS_GRID": "#777777",
        # --- Global Layout Colors ---
        "@PRIMARY_ACCENT": "#007acc",
        "@DIVIDER_COLOR": "rgba(255, 255, 255, 0.1)",
        "@CANVAS_BG": "#000000",
        "@CANVAS_BORDER": "#4a6fa5",
        # --- General Text Elements ---
        "@LBL_FOLDER_TEXT": "#aaaaaa",
        "@LBL_STATUS_TEXT": "#bbbbbb",
        "@LBL_METRICS_TEXT": "#888888",
        "@SECTION_HEAD_TEXT": "#888888",
        # --- Settings Button (btn_settings.qss) ---
        "@BTN_SETTINGS_COLOR": "#888888",
        "@BTN_SETTINGS_HOVER_BG": "rgba(255, 255, 255, 0.08)",
        "@BTN_SETTINGS_HOVER_COLOR": "#ffffff",
        "@BTN_SETTINGS_PRESSED_BG": "rgba(255, 255, 255, 0.04)",
        "@BTN_SETTINGS_FOCUS_BG": "rgba(255, 255, 255, 0.08)",
        "@BTN_SETTINGS_FOCUS_COLOR": "#ffffff",
        # --- Commands Overlay (commands_overlay.qss) ---
        "@COMMANDS_TEXT": "#ffffff",
        "@COMMANDS_BG": "rgba(10, 10, 10, 0.55)",
        "@COMMANDS_BORDER": "rgba(255, 255, 255, 0.05)",
        # --- Settings Drawer (drawer.qss) ---
        "@DRAWER_BG": "rgba(20, 20, 20, 0.94)",
        "@DRAWER_BORDER": "rgba(255, 255, 255, 0.15)",
        "@DRAWER_CHECKBOX_TEXT": "#e0e0e0",
        "@DRAWER_LABEL_TEXT": "#ffffff",
        "@DRAWER_LABEL_BORDER": "rgba(255, 255, 255, 0.1)",
        # --- Notifications (notification.qss) ---
        "@NOTIF_TEXT": "#ffffff",
        "@NOTIF_BG": "rgba(0, 0, 0, 0.75)",
        "@NOTIF_BORDER": "rgba(255, 255, 255, 0.4)",
        # --- Telemetry HUD (telemetry_hud.qss) ---
        "@TELEMETRY_TEXT": "#888888",
        "@TELEMETRY_BG": "rgba(10, 10, 10, 0.75)",
        "@TELEMETRY_BORDER": "rgba(255, 255, 255, 0.1)",
        # --- Splash HUD (splash_hud.qss) ---
        "@SPLASH_TEXT": "#ffffff",
        "@SPLASH_BG": "rgba(15, 15, 15, 0.85)",
        "@SPLASH_BORDER": "rgba(255, 255, 255, 0.08)",
        # --- Spinboxes (spinboxes.qss) ---
        "@SPIN_BG": "#1e1e1e",
        "@SPIN_BORDER": "#333333",
        "@SPIN_BORDER_HOVER": "#444444",
        "@SPIN_TEXT": "#ffffff",
        "@SPIN_BTN_BORDER": "#333333",
        "@SPIN_BTN_BG": "#252525",
        "@SPIN_BTN_HOVER": "#353535",
        "@SPIN_BTN_PRESSED": "#151515",
        "@SPIN_FOCUS_BG": "#202630",
        "@SPIN_UP_ARROW": "url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjE4IDE1IDEyIDkgNiAxNSIvPjwvc3ZnPg==)",
        "@SPIN_DOWN_ARROW": "url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjYgOSAxMiAxNSAxOCA5Ii8+PC9zdmc+)",
    },
    "light": {
        # --- QPainter Grid Canvas ---
        "@CANVAS_GRID": "#b0b0b0",
        # --- Global Layout Colors ---
        "@PRIMARY_ACCENT": "#007acc",
        "@DIVIDER_COLOR": "rgba(0, 0, 0, 0.1)",
        "@CANVAS_BG": "#ffffff",
        "@CANVAS_BORDER": "#a0b0d0",
        # --- General Text Elements ---
        "@LBL_FOLDER_TEXT": "#444444",
        "@LBL_STATUS_TEXT": "#333333",
        "@LBL_METRICS_TEXT": "#555555",
        "@SECTION_HEAD_TEXT": "#666666",
        # --- Settings Button (btn_settings.qss) ---
        "@BTN_SETTINGS_COLOR": "#555555",
        "@BTN_SETTINGS_HOVER_BG": "rgba(0, 0, 0, 0.05)",
        "@BTN_SETTINGS_HOVER_COLOR": "#000000",
        "@BTN_SETTINGS_PRESSED_BG": "rgba(0, 0, 0, 0.08)",
        "@BTN_SETTINGS_FOCUS_BG": "rgba(0, 0, 0, 0.05)",
        "@BTN_SETTINGS_FOCUS_COLOR": "#000000",
        # --- Commands Overlay (commands_overlay.qss) ---
        "@COMMANDS_TEXT": "#111111",
        "@COMMANDS_BG": "rgba(245, 245, 245, 0.90)",
        "@COMMANDS_BORDER": "rgba(0, 0, 0, 0.1)",
        # --- Settings Drawer (drawer.qss) ---
        "@DRAWER_BG": "rgba(240, 240, 240, 0.96)",
        "@DRAWER_BORDER": "rgba(0, 0, 0, 0.15)",
        "@DRAWER_CHECKBOX_TEXT": "#222222",
        "@DRAWER_LABEL_TEXT": "#000000",
        "@DRAWER_LABEL_BORDER": "rgba(0, 0, 0, 0.1)",
        # --- Notifications (notification.qss) ---
        "@NOTIF_TEXT": "#000000",
        "@NOTIF_BG": "rgba(255, 255, 255, 0.90)",
        "@NOTIF_BORDER": "rgba(0, 0, 0, 0.2)",
        # --- Telemetry HUD (telemetry_hud.qss) ---
        "@TELEMETRY_TEXT": "#444444",
        "@TELEMETRY_BG": "rgba(245, 245, 245, 0.85)",
        "@TELEMETRY_BORDER": "rgba(0, 0, 0, 0.1)",
        # --- Splash HUD (splash_hud.qss) ---
        "@SPLASH_TEXT": "#111111",
        "@SPLASH_BG": "rgba(250, 250, 250, 0.95)",
        "@SPLASH_BORDER": "rgba(0, 0, 0, 0.1)",
        # --- Spinboxes (spinboxes.qss) ---
        "@SPIN_BG": "#ffffff",
        "@SPIN_BORDER": "#cccccc",
        "@SPIN_BORDER_HOVER": "#aaaaaa",
        "@SPIN_TEXT": "#000000",
        "@SPIN_BTN_BORDER": "#cccccc",
        "@SPIN_BTN_BG": "#f0f0f0",
        "@SPIN_BTN_HOVER": "#e0e0e0",
        "@SPIN_BTN_PRESSED": "#d0d0d0",
        "@SPIN_FOCUS_BG": "#eef4fc",
        # SVGs updated from stroke="white" to stroke="black" via Base64 encoding
        "@SPIN_UP_ARROW": "url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjE4IDE1IDEyIDkgNiAxNSIvPjwvc3ZnPg==)",
        "@SPIN_DOWN_ARROW": "url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJibGFjayIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjYgOSAxMiAxNSAxOCA5Ii8+PC9zdmc+)",
    },
}


def init_theme(file_manager_instance, default_mode: str = "dark"):
    """Saves the file manager reference once and applies the initial theme."""
    global _file_manager, current_theme, current_palette
    _file_manager = file_manager_instance

    if default_mode in THEME_PALETTES:
        current_theme = default_mode
        current_palette = THEME_PALETTES[default_mode]

    # Notice we don't need to pass the instance anymore!
    apply_theme(current_theme)


def apply_theme(theme_mode: str):
    """Loads the template using the saved file manager and applies it to Qt."""
    global current_theme, current_palette, _file_manager

    if not _file_manager:
        logger.error(
            "Theme Engine Error: init_theme() must be called before apply_theme()."
        )
        return

    if theme_mode not in THEME_PALETTES:
        logger.error("Theme '%s' not recognized.", theme_mode)
        return

    current_theme = theme_mode
    current_palette = THEME_PALETTES[theme_mode]

    # Uses the stored global reference automatically
    qss_buffer = _file_manager.load_asset(
        filename="base_template.qss", folder_name="styles"
    )
    sorted_tokens = sorted(
        current_palette.items(), key=lambda item: len(item[0]), reverse=True
    )

    # Replace variables on the fly using the correct string-length priority order
    for token, hex_color in sorted_tokens:
        qss_buffer = qss_buffer.replace(token, hex_color)

    app_instance = QApplication.instance()
    if app_instance:
        app_instance.setStyleSheet(qss_buffer)
        for widget in app_instance.allWidgets():
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
    else:
        logger.warning("QApplication core instance loop not found.")


def get_color(token_name: str) -> str:
    """Helper method used by your custom Canvas loops to pull color hex strings."""
    return current_palette.get(token_name, "#FFFFFF")
