import logging

from PyQt6.QtWidgets import QApplication, QWidget

from config.ui_constants import (
    BASE_STYLE_TEMPLATE,
    FOLDER_STYLES,
    FOLDER_TEMPLATES,
    TEMPLATE_SPLASH,
)

logger = logging.getLogger(__name__)
THEME_DARK = "dark"
THEME_LIGHT = "light"

# 1. Global State Variables (Module Scope)
current_theme = THEME_DARK
current_palette = {}
_file_manager = None  # Holds the saved reference to your file manager

# 2. Design Token Dictionary Mapping
# --- Unified Dual-Theme Palettes for LossLess Crop ---
THEME_PALETTES = {
    "dark": {
        # --- main windows ---
        "@WINDOW_BG": "#121212",  # Sleek dark window background color
        # --- QPainter Grid Canvas ---
        "@CANVAS_GRID": "#777777",
        # --- Global Layout Colors ---
        "@PRIMARY_ACCENT": "#007acc",
        "@PRIMARY_TEXT": "#ffffff",
        "@DIVIDER_COLOR": "rgba(255, 255, 255, 0.1)",
        "@CANVAS_BG": "#000000",
        "@CANVAS_BORDER": "#4a6fa5",
        # --- General Text Elements ---
        "@LBL_FOLDER_TEXT": "#aaaaaa",
        "@LBL_STATUS_TEXT": "#bbbbbb",
        "@LBL_METRICS_TEXT": "#888888",
        "@SECTION_HEAD_TEXT": "#888888",
        # --- Settings Button (btn_settings.qss) ---
        "@BTN_SETTINGS_COLOR": "#F5EFEB",
        "@BTN_SETTINGS_HOVER_BG": "rgba(26, 115, 232, 0.15)",
        "@BTN_SETTINGS_HOVER_COLOR": "#ffffff",
        "@BTN_SETTINGS_PRESSED_BG": "rgba(26, 115, 232, 0.25)",
        "@BTN_SETTINGS_FOCUS_BG": "rgba(26, 115, 232, 0.15)",
        "@BTN_SETTINGS_FOCUS_COLOR": "#ffffff",
        # --- Commands Overlay (commands_overlay.qss) ---
        "@COMMANDS_TEXT": "#ffffff",
        "@COMMANDS_BG": "rgba(10, 10, 10, 0.55)",
        "@COMMANDS_BORDER": "rgba(255, 255, 255, 0.05)",
        # --- Settings Drawer & Toolbars (drawer.qss) ---
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
        "@TELEMETRY_BG": "rgba(10, 10, 10, 0.45)",
        "@TELEMETRY_BORDER": "rgba(255, 255, 255, 0.1)",
        # --- Splash HUD (splash_hud.qss) ---
        "@SPLASH_TEXT": "#ffffff",
        "@SPLASH_BG": "rgba(15, 15, 15, 0.45)",
        "@SPLASH_BORDER": "rgba(255, 255, 255, 0.08)",
        # --- Spinboxes & Comboboxes (spinboxes.qss) ---
        "@SPIN_BG": "#1e1e1e",
        "@SPIN_BORDER": "#333333",
        "@SPIN_BORDER_HOVER": "#007acc",
        "@SPIN_TEXT": "#ffffff",
        "@SPIN_BTN_BORDER": "#333333",
        "@SPIN_BTN_BG": "#252525",
        "@SPIN_BTN_HOVER": "#353535",
        "@SPIN_BTN_PRESSED": "#151515",
        "@SPIN_FOCUS_BG": "#202630",
        "@SPIN_UP_ARROW": "url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjE4IDE1IDEyIDkgNiAxNSIvPjwvc3ZnPg==)",
        "@SPIN_DOWN_ARROW": "url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtbGluZWNhcD0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjYgOSAxMiAxNSAxOCA5Ii8+PC9zdmc+)",
        # Splash hud
        "@SPLASH_TEXT_MAIN": "#ffffff",
        "@SPLASH_TEXT_MUTED": "#bbbbbb",
        "@SPLASH_OR_DIVIDER": "#555555",
        "@CHECKBOX_HOVER_BORDER": "#666666",  # Your exact original dark hover border
        "@CHECKBOX_HOVER_BG": "#252525",
        "@CHECKBOX_TEXT_HOVER": "#ffffff",
        # Menu Bar
        "@MENUBAR_BG": "#2b2b2b",
        "@MENU_BORDER": "#3a3a3a",
        "@MENU_SEPARATOR_BG": "#444444",
    },
    "light": {
        # --- QPainter Grid Canvas ---
        "@CANVAS_GRID": "#BCAFA5",  # Muted clay-taupe for the dash-line grid pattern
        # --- Global Layout Colors ---
        "@WINDOW_BG": "#F5EFEB",  # Soft Linen Grey-Beige main workspace background
        "@PRIMARY_ACCENT": "#D97D54",  # Beautiful Muted Terracotta Orange highlight accent color
        "@PRIMARY_TEXT": "#2E2520",
        "@DIVIDER_COLOR": "rgba(46, 37, 32, 0.12)",  # Elegant dark coffee divider line
        "@CANVAS_BG": "#F5EFEB",  # Blends completely with your workspace frame context
        "@CANVAS_BORDER": "#D97D54",  # Terracotta accent framing your central canvas wrapper
        # --- General Text Elements (Dark Roasted Coffee / High Readability) ---
        "@LBL_FOLDER_TEXT": "#5C4A40",
        "@LBL_STATUS_TEXT": "#2E2520",
        "@LBL_METRICS_TEXT": "#5C4A40",
        "@SECTION_HEAD_TEXT": "#7A6559",
        # --- Settings Button (btn_settings.qss) ---
        "@BTN_SETTINGS_COLOR": "#ffffff",
        "@BTN_SETTINGS_HOVER_BG": "rgba(217, 125, 84, 0.14)",  # Soft terracotta hover highlight hue
        "@BTN_SETTINGS_HOVER_COLOR": "#2E2520",
        "@BTN_SETTINGS_PRESSED_BG": "rgba(217, 125, 84, 0.08)",
        "@BTN_SETTINGS_FOCUS_BG": "rgba(217, 125, 84, 0.14)",
        "@BTN_SETTINGS_FOCUS_COLOR": "#2E2520",
        # --- Commands Overlay (commands_overlay.qss) ---
        "@COMMANDS_TEXT": "#2E2520",
        "@COMMANDS_BG": "rgba(240, 232, 226, 0.45)",  # Warm Latte Clay base structure
        "@COMMANDS_BORDER": "rgba(46, 37, 32, 0.15)",
        # --- Settings Drawer & Toolbars (drawer.qss / toolbars) ---
        "@DRAWER_BG": "rgba(240, 232, 226, 0.95)",  # Perfectly blended translucent side drawer
        "@DRAWER_BORDER": "rgba(46, 37, 32, 0.15)",
        "@DRAWER_CHECKBOX_TEXT": "#2E2520",
        "@DRAWER_LABEL_TEXT": "#2E2520",
        "@DRAWER_LABEL_BORDER": "rgba(46, 37, 32, 0.12)",
        # --- Notifications (notification.qss) ---
        "@NOTIF_TEXT": "#2E2520",
        "@NOTIF_BG": "rgba(230, 220, 212, 0.60)",
        "@NOTIF_BORDER": "#D97D54",  # Crisp terracotta boundary alert box
        # --- Telemetry HUD (telemetry_hud.qss) ---
        "@TELEMETRY_TEXT": "#2E2520",
        "@TELEMETRY_BG": "rgba(230, 220, 212, 0.45)",
        "@TELEMETRY_BORDER": "rgba(46, 37, 32, 0.08)",
        # --- Splash HUD (splash_hud.qss) ---
        "@SPLASH_TEXT": "#2E2520",
        "@SPLASH_BG": "rgba(230, 220, 212, 0.55)",
        "@SPLASH_BORDER": "rgba(46, 37, 32, 0.12)",
        # --- Spinboxes & Comboboxes (spinboxes.qss / combos) ---
        "@SPIN_BG": "#FAF6F3",  # Pale clean cream container background pop
        "@SPIN_BORDER": "#DDD1C7",  # Soft linen boundary frame lines
        "@SPIN_BORDER_HOVER": "#D97D54",  # Accent hover glow
        "@SPIN_TEXT": "#2E2520",
        "@SPIN_BTN_BORDER": "#DDD1C7",
        "@SPIN_BTN_BG": "#F5EFEB",  # Subtle shading for control buttons
        "@SPIN_BTN_HOVER": "#EBE1DA",
        "@SPIN_BTN_PRESSED": "#DDD1C7",
        "@SPIN_FOCUS_BG": "#FAF6F3",
        # Custom Base64 micro-arrows updated with stroke="#2E2520" (Dark Roasted Coffee) for strong contrast
        "@SPIN_UP_ARROW": "url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjMkUyNTIwIiBzdHJva2Utd2lkdGg9IjQiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMTggMTUgMTIgOSYgMTUiLz48L3N2Zz4=)",
        "@SPIN_DOWN_ARROW": "url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjMkUyNTIwIiBzdHJva2Utd2lkdGg9IjQiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iNiA5IDEyIDE1IDE4IDkiLz48L3N2Zz4=)",
        # splash hud
        "@SPLASH_TEXT_MAIN": "#2E2520",
        "@SPLASH_TEXT_MUTED": "#5C4A40",
        "@SPLASH_OR_DIVIDER": "#9C8A7F",
        "@CHECKBOX_HOVER_BORDER": "#BCAFA5",  # Richer clay-taupe to create a sharp visible border
        "@CHECKBOX_HOVER_BG": "#EADED5",
        "@CHECKBOX_TEXT_HOVER": "#000000",
        # Menu Bar
        "@MENUBAR_BG": "#ffffff",
        "@MENU_BORDER": "#DDD1C7",
        "@MENU_SEPARATOR_BG": "#5C4A40",
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


def substitute_tokens(raw_payload: str) -> str:
    """
    Universal String Compiler. Sanitizes formatting noise and injects
    theme colors into any text type (QSS, HTML, or Markdown) using the
    global module scope variables.
    """
    if not raw_payload:
        return ""

    # 1. Universal Sanitation (Now safely protects HTML and MD files)
    clean_buffer = raw_payload.replace("\r\n", "\n").replace("\ufeff", "").strip()

    # 2. Extract palette map using global variable state
    global current_palette
    sorted_tokens = sorted(
        current_palette.items(), key=lambda item: len(item[0]), reverse=True
    )

    # 3. Core Replacement Loop
    for token, hex_color in sorted_tokens:
        clean_buffer = clean_buffer.replace(token, hex_color)

    return clean_buffer


def apply_theme(theme_mode: str):
    """Loads blueprint template assets, swaps variables, and pushes straight to Qt."""
    global current_theme, current_palette, _file_manager

    if not _file_manager:
        logger.error(
            "Theme Engine Error: init_theme() must be called before apply_theme()."
        )
        return

    current_theme = theme_mode
    current_palette = THEME_PALETTES[theme_mode]
    qss_buffer = _file_manager.load_asset(
        filename=BASE_STYLE_TEMPLATE, folder_name=FOLDER_STYLES
    )
    if not qss_buffer:
        return

    qss_buffer = substitute_tokens(qss_buffer)

    app_instance = QApplication.instance()
    if app_instance:
        app_instance.setStyleSheet(qss_buffer)

        # --- 2. DYNAMICALLY RE-COMPILE AND SET SPLASH HUD TEXT DIRECTLY ---
        # Look through active windows to find the custom SplashHUD object ID string name
        for window in app_instance.topLevelWidgets():
            if hasattr(window, "findChild"):
                splash_hud = window.findChild(QWidget, "SplashHUD")
                if splash_hud and hasattr(splash_hud, "setText"):
                    # If found, load the splash asset, swap tokens, and set it directly!
                    raw_html = _file_manager.load_asset(
                        filename=TEMPLATE_SPLASH, folder_name=FOLDER_TEMPLATES
                    )
                    if raw_html:
                        raw_html = substitute_tokens(raw_html)
                        # Direct call on the widget instance inside the theme manager loop
                        splash_hud.setText(raw_html)
    else:
        logger.warning("Application runtime loop missed.")


def get_color(token_name: str) -> str:
    """Helper method used by your custom Canvas loops to pull color hex strings."""
    return current_palette.get(token_name, "#FFFFFF")


def toggle_theme():
    """Toggles the application between dark and light themes automatically."""
    global current_theme
    # Calculate the opposite layout state based on the active runtime value
    next_theme = "light" if current_theme == "dark" else "dark"
    apply_theme(next_theme)
