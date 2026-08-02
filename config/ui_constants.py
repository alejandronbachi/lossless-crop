import sys

# --- Front End Assets Directory Names ---
FOLDER_ASSETS = "assets"
FOLDER_STYLES = "styles"
FOLDER_TEMPLATES = "templates"
FOLDER_ICONS = "icons"
# --- Stylesheet File Names ---
BASE_STYLE_TEMPLATE = "base_template.qss"

# --- HTML Template File Names ---
TEMPLATE_SPLASH = "splash_hud.html"
TEMPLATE_COMMANDS = "commands_overlay.html"
TEMPLATE_ABOUT = "about.html"

# --- ICON File Name ---
if sys.platform == "win32":
    ICON_FILENAME = "icon.ico"
elif sys.platform == "darwin":
    ICON_FILENAME = "icon.icns"
else:
    ICON_FILENAME = "icon.png"


# --- App Window & Views Titles ---
WINDOW_TITLE = "LossLess Crop"

# --- View Control / Object Names ---
WIDGET_ZOOM_HUD = "zoom_hud"
WIDGET_SETTINGS_DRAWER = "settings_drawer"
WIDGET_CONTROL_TOOLBAR = "control_toolbar"
WIDGET_INFO_BAR = "info_bar_widget"
WIDGET_SPLASH_HUD = "SplashHUD"
WIDGET_TELEMETRY_HUD = "TelemetryHUD"

# --- Text Messages & Notifications ---
TEXT_NO_DIRECTORY = "No directory loaded"
TEXT_READY_STATUS = "Ready. Open a folder to start cropping."
TEXT_LOSSLESS_CROP = "Lossless Crop"
TEXT_LOSSY_CROP = "Lossy Crop"
TEXT_CROP_FAILED = "Crop Failed"
TEXT_NO_VALID_IMAGES = "No valid images found in target folder."
TEXT_NO_VALID_IMAGES_DIR = "No valid, readable images found in directory."
TEXT_NO_VALID_IMAGES_DROP = "No valid, readable images found in dropped payload."

# --- Spinbox Prefixes & Suffixes ---
SPIN_WIDTH_PREFIX = "W: "
SPIN_WIDTH_SUFFIX = " px"
SPIN_HEIGHT_PREFIX = "H: "
SPIN_HEIGHT_SUFFIX = " px"

# --- File Filters ---
IMAGE_FILE_FILTER = "Images (*.png *.jpg *.jpeg *.webp *.bmp)"

# --- Settings Drawer & Toolbar UI Texts & Tooltips ---
LABEL_GENERAL_SECTION = "General"
LABEL_SHOW_SECTION = "Show / Display"
LABEL_LAYOUT_SECTION = "Layout Memory"

CHECKBOX_SAVE_SETTINGS_TEXT = "Save settings"
CHECKBOX_AUTO_OPEN_FOLDER_TEXT = "Auto-open last folder"
CHECKBOX_SHORTCUTS_GUIDE_TEXT = "Shortcuts Guide"
CHECKBOX_NOTIFICATIONS_TEXT = "Notifications"
CHECKBOX_BOTTOM_INFOBAR_TEXT = "Bottom Info Bar"
CHECKBOX_IMAGE_FILENAME_TEXT = "Image Filename"
CHECKBOX_IMAGE_RESOLUTION_TEXT = "Image Resolution"
CHECKBOX_PREVIEW_TEXT = "Preview"
CHECKBOX_FIT_PREVIEW_TEXT = "Fit Preview"
CHECKBOX_MAIN_WINDOW_TEXT = "Main Window"
CHECKBOX_PREVIEW_HUD_TEXT = "Preview HUD"
CHECKBOX_KEEP_SELECTION_TEXT = "Keep selection"
CHECKBOX_OVERWRITE_TEXT = "Overwrite"
CHECKBOX_DARK_THEME = "Dark Theme"

TOOLTIP_PREVIEW = "Display Zoom Preview HUD"
TOOLTIP_ENGINE = "Choose processing engine mode for saving operations."
TOOLTIP_RATIO = (
    "Force the cropping rectangle selection box to lock onto specific aspect ratios."
)
TOOLTIP_SNAP = "Select layout feedback mode for Left-Click mouse drawing."
TOOLTIP_PRESERVE = (
    "Conserve current selection box size and position coordinates across images."
)
TOOLTIP_OVERWRITE = "Directly overwrite original source image files instead of nesting copies in a subfolder."
TOOLTIP_SETTINGS = "Toggle configuration choices"

RATIO_FREEFORM = "Freeform"
RATIO_SQUARE = "1:1 Square"
RATIO_WIDESCREEN = "16:9 Widescreen"
RATIO_STANDARD = "4:3 Standard"
RATIO_SOURCE = "Source Ratio"
RATIO_ITEMS = [
    RATIO_FREEFORM,
    RATIO_SQUARE,
    RATIO_WIDESCREEN,
    RATIO_STANDARD,
    RATIO_SOURCE,
]
SNAP_REAL_TIME = "Real-time snap"
SNAP_POST_RELEASE = "Post-release snap"
SNAP_GHOSTING = "Ghosting"
SNAP_ITEMS = [SNAP_REAL_TIME, SNAP_POST_RELEASE, SNAP_GHOSTING]
ENGINE_LOSSLESS = "Lossless"
ENGINE_PIXEL_PERFECT = "Pixel-Perfect"
ENGINE_ACTIVATION_LOSSLESS = "LOSSLESS MODE (jpegtran)"
ENGINE_ACTIVATION_PIXEL_PERFECT = "PIXEL-PERFECT MODE (Pillow)"
