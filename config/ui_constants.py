import sys

from PyQt6.QtCore import QCoreApplication


# --- Internationalization Helpers ---
def QT_TRANSLATE_NOOP(context: str, text: str) -> str:
    return text


def translate_constant(text: str) -> str:
    app = QCoreApplication.instance()

    # Verify if an application context exists and checks our persistent tracking property
    if not app or not hasattr(app, "translator"):
        return text

    # Perform the dictionary lookup
    result = QCoreApplication.translate("UIConstants", text)

    # Optional debugging for foreign languages (e.g., Spanish)
    if result == text:
        print(f"[MISSING TRANSLATION] Context: UIConstants | String: '{text}'")

    return result


SUPPORTED_LANGUAGES = ["en", "es"]

# --- Front End Assets Directory Names ---
FOLDER_ASSETS = "assets"
FOLDER_STYLES = "styles"
FOLDER_TEMPLATES = "templates"
FOLDER_ICONS = "icons"
FOLDER_SVGS = "svgs"
# --- Stylesheet File Names ---
BASE_STYLE_TEMPLATE = "base_template.qss"

# --- HTML Template File Names ---
TEMPLATE_SPLASH = "splash_hud"
TEMPLATE_COMMANDS = "commands_overlay"
TEMPLATE_ABOUT = "about"
TEMPLATE_USER_MANUAL = "user_manual_format"

# --- ICON File Name ---
if sys.platform == "win32":
    ICON_FILENAME = "icon.ico"
elif sys.platform == "darwin":
    ICON_FILENAME = "icon.icns"
else:
    ICON_FILENAME = "icon.png"


# --- App Window & Views Titles ---
WINDOW_TITLE = QT_TRANSLATE_NOOP("UIConstants", "LossLess Crop")

# --- View Control / Object Names ---
WIDGET_ZOOM_HUD = "zoom_hud"
WIDGET_SETTINGS_DRAWER = "settings_drawer"
WIDGET_CONTROL_TOOLBAR = "control_toolbar"
WIDGET_INFO_BAR = "info_bar_widget"
WIDGET_SPLASH_HUD = "SplashHUD"
WIDGET_TELEMETRY_HUD = "TelemetryHUD"

# --- Text Messages & Notifications ---
TEXT_NO_DIRECTORY = QT_TRANSLATE_NOOP("UIConstants", "No directory loaded")
TEXT_READY_STATUS = QT_TRANSLATE_NOOP(
    "UIConstants", "Ready. Open a folder to start cropping."
)
TEXT_LOSSLESS_CROP = QT_TRANSLATE_NOOP("UIConstants", "Lossless Crop")
TEXT_LOSSY_CROP = QT_TRANSLATE_NOOP("UIConstants", "Lossy Crop")
TEXT_CROP_FAILED = QT_TRANSLATE_NOOP("UIConstants", "Crop Failed")
TEXT_NO_VALID_IMAGES = QT_TRANSLATE_NOOP(
    "UIConstants", "No valid images found in target folder."
)
TEXT_NO_VALID_IMAGES_DIR = QT_TRANSLATE_NOOP(
    "UIConstants", "No valid, readable images found in directory."
)
TEXT_NO_VALID_IMAGES_DROP = QT_TRANSLATE_NOOP(
    "UIConstants", "No valid, readable images found in dropped payload."
)

# --- Spinbox Prefixes & Suffixes ---
SPIN_WIDTH_PREFIX = QT_TRANSLATE_NOOP("UIConstants", "W: ")
SPIN_WIDTH_SUFFIX = QT_TRANSLATE_NOOP("UIConstants", " px")
SPIN_HEIGHT_PREFIX = QT_TRANSLATE_NOOP("UIConstants", "H: ")
SPIN_HEIGHT_SUFFIX = QT_TRANSLATE_NOOP("UIConstants", " px")

# --- File Filters ---
IMAGE_FILE_FILTER = QT_TRANSLATE_NOOP(
    "UIConstants", "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
)

# --- Settings Drawer & Toolbar UI Texts & Tooltips ---
LABEL_GENERAL_SECTION = QT_TRANSLATE_NOOP("UIConstants", "General")
LABEL_SHOW_SECTION = QT_TRANSLATE_NOOP("UIConstants", "Show / Display")
LABEL_LAYOUT_SECTION = QT_TRANSLATE_NOOP("UIConstants", "Layout Memory")

CHECKBOX_SAVE_SETTINGS_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Save settings")
CHECKBOX_AUTO_OPEN_FOLDER_TEXT = QT_TRANSLATE_NOOP(
    "UIConstants", "Auto-open last folder"
)
CHECKBOX_SHORTCUTS_GUIDE_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Shortcuts Guide")
CHECKBOX_NOTIFICATIONS_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Notifications")
CHECKBOX_BOTTOM_INFOBAR_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Bottom Info Bar")
CHECKBOX_IMAGE_DIRECTORY_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Directory Name")
CHECKBOX_IMAGE_FILENAME_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Image Filename")
CHECKBOX_IMAGE_RESOLUTION_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Image Resolution")
CHECKBOX_PREVIEW_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Preview")
CHECKBOX_FIT_PREVIEW_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Fit Preview")
CHECKBOX_MAIN_WINDOW_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Main Window")
CHECKBOX_PREVIEW_HUD_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Preview HUD")
CHECKBOX_KEEP_SELECTION_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Keep selection")
CHECKBOX_OVERWRITE_TEXT = QT_TRANSLATE_NOOP("UIConstants", "Overwrite")
CHECKBOX_DARK_THEME = QT_TRANSLATE_NOOP("UIConstants", "Dark Theme")

TOOLTIP_PREVIEW = QT_TRANSLATE_NOOP("UIConstants", "Display Zoom Preview HUD")
TOOLTIP_ENGINE = QT_TRANSLATE_NOOP(
    "UIConstants", "Choose processing engine mode for saving operations."
)
TOOLTIP_RATIO = QT_TRANSLATE_NOOP(
    "UIConstants",
    "Force the cropping rectangle selection box to lock onto specific aspect ratios.",
)
TOOLTIP_SNAP = QT_TRANSLATE_NOOP(
    "UIConstants", "Select layout feedback mode for Left-Click mouse drawing."
)
TOOLTIP_PRESERVE = QT_TRANSLATE_NOOP(
    "UIConstants",
    "Conserve current selection box size and position coordinates across images.",
)
TOOLTIP_OVERWRITE = QT_TRANSLATE_NOOP(
    "UIConstants",
    "Directly overwrite original source image files instead of nesting copies in a subfolder.",
)
TOOLTIP_SETTINGS = QT_TRANSLATE_NOOP("UIConstants", "Toggle configuration choices")

RATIO_FREEFORM = QT_TRANSLATE_NOOP("UIConstants", "Freeform")
RATIO_SQUARE = QT_TRANSLATE_NOOP("UIConstants", "1:1 Square")
RATIO_WIDESCREEN = QT_TRANSLATE_NOOP("UIConstants", "16:9 Widescreen")
RATIO_STANDARD = QT_TRANSLATE_NOOP("UIConstants", "4:3 Standard")
RATIO_SOURCE = QT_TRANSLATE_NOOP("UIConstants", "Source Ratio")
RATIO_ITEMS = [
    RATIO_FREEFORM,
    RATIO_SQUARE,
    RATIO_WIDESCREEN,
    RATIO_STANDARD,
    RATIO_SOURCE,
]
SNAP_REAL_TIME = QT_TRANSLATE_NOOP("UIConstants", "Real-time snap")
SNAP_POST_RELEASE = QT_TRANSLATE_NOOP("UIConstants", "Post-release snap")
SNAP_GHOSTING = QT_TRANSLATE_NOOP("UIConstants", "Ghosting")
SNAP_ITEMS = [SNAP_REAL_TIME, SNAP_POST_RELEASE, SNAP_GHOSTING]
ENGINE_LOSSLESS = QT_TRANSLATE_NOOP("UIConstants", "Lossless")
ENGINE_PIXEL_PERFECT = QT_TRANSLATE_NOOP("UIConstants", "Pixel-Perfect")
ENGINE_ACTIVATION_LOSSLESS = QT_TRANSLATE_NOOP(
    "UIConstants", "LOSSLESS MODE (jpegtran)"
)
ENGINE_ACTIVATION_PIXEL_PERFECT = QT_TRANSLATE_NOOP(
    "UIConstants", "PIXEL-PERFECT MODE (Pillow)"
)

# --- Email Feedback Dialog Constants ---
FEEDBACK_BTN_SUBMIT = QT_TRANSLATE_NOOP("UIConstants", "Submit")
FEEDBACK_BTN_TRANSMITTING = QT_TRANSLATE_NOOP("UIConstants", "Transmitting...")
FEEDBACK_ANONYMOUS_USER = QT_TRANSLATE_NOOP("UIConstants", "Anonymous User")
FEEDBACK_CAPTCHA_FALSE = "false"
FEEDBACK_SUBJECT_TEMPLATE = QT_TRANSLATE_NOOP(
    "UIConstants", "📥 New {} from lossless-crop"
)
FEEDBACK_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
FEEDBACK_ACCEPT = "application/json"
FEEDBACK_CONTENT_TYPE = "application/json"
FEEDBACK_ORIGIN = "https://github.com"
FEEDBACK_REFERER = "https://github.com/alejandronbachi/lossless-crop"
FEEDBACK_ENDPOINT_TEMPLATE = "https://formsubmit.co/ajax/{}"
FEEDBACK_TIMEOUT = 12
FEEDBACK_SUCCESS_STR = QT_TRANSLATE_NOOP("UIConstants", "Success")
FEEDBACK_SERVER_ERROR_PREFIX = QT_TRANSLATE_NOOP(
    "UIConstants", "Server responded with status code: "
)

FEEDBACK_WINDOW_TITLE = QT_TRANSLATE_NOOP("UIConstants", "Submit Feedback / Bug Report")
FEEDBACK_MIN_WIDTH = 420
FEEDBACK_MIN_HEIGHT = 380

FEEDBACK_LABEL_EMAIL = QT_TRANSLATE_NOOP(
    "UIConstants", "Your Email (Optional, for follow-up details):"
)
FEEDBACK_PLACEHOLDER_EMAIL = QT_TRANSLATE_NOOP("UIConstants", "developer@example.com")
FEEDBACK_LABEL_CATEGORY = QT_TRANSLATE_NOOP("UIConstants", "Classification Category:")
FEEDBACK_CATEGORIES_ITEMS = [
    QT_TRANSLATE_NOOP("UIConstants", "Bug Report"),
    QT_TRANSLATE_NOOP("UIConstants", "Feature Request "),
    QT_TRANSLATE_NOOP("UIConstants", "General UI Feedback "),
]
FEEDBACK_LABEL_DESCRIPTION = QT_TRANSLATE_NOOP("UIConstants", "Detailed Description:")
FEEDBACK_PLACEHOLDER_DESCRIPTION = QT_TRANSLATE_NOOP(
    "UIConstants",
    "Please specify what steps you took right before encountering the issue...",
)
FEEDBACK_BTN_CANCEL = QT_TRANSLATE_NOOP("UIConstants", "Cancel")

FEEDBACK_VALIDATION_TITLE = QT_TRANSLATE_NOOP("UIConstants", "Validation Error")
FEEDBACK_VALIDATION_MSG = QT_TRANSLATE_NOOP(
    "UIConstants", "Description field cannot be submitted blank."
)

FEEDBACK_THANKYOU_TITLE = QT_TRANSLATE_NOOP("UIConstants", "Thank You")
FEEDBACK_THANKYOU_MSG = QT_TRANSLATE_NOOP(
    "UIConstants",
    "Your feedback was sent successfully and delivered straight to my inbox!",
)

FEEDBACK_FAILURE_TITLE = QT_TRANSLATE_NOOP("UIConstants", "Network Dispatch Failure")
FEEDBACK_FAILURE_TEMPLATE = QT_TRANSLATE_NOOP(
    "UIConstants", "Transmission failed. Check internet access.\n\nError: {}"
)
