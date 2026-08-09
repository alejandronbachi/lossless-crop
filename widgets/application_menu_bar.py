import logging
import sys
from pathlib import Path

from PyQt6.QtCore import QStandardPaths, Qt, QUrl
from PyQt6.QtGui import QAction, QActionGroup, QDesktopServices
from PyQt6.QtWidgets import QApplication, QMenuBar, QMessageBox

from config import ui_constants
from config.app_constants import APP_VERSION
from managers import theme_manager
from managers.file_manager import FileManager
from widgets.email_feedback_dialog import EmailFeedbackDialog
from widgets.user_manual_dialog import UserManualDialog

logger = logging.getLogger(__name__)


class ApplicationMenuBar(QMenuBar):
    def __init__(self, parent_window, settings_manager, file_manager: FileManager):
        super().__init__(parent_window)
        self.main_win = parent_window
        self.settings_mgr = settings_manager
        self.file_mgr = file_manager
        self.setObjectName("CustomAppMenuBar")
        self.init_menus()

    def init_menus(self):
        # --- FILE MENU ---
        file_menu = self.addMenu(
            ui_constants.translate_constant(ui_constants.MENU_FILE)
        )

        open_folder_act = QAction(
            ui_constants.translate_constant(ui_constants.ACTION_OPEN_DIRECTORY), self
        )
        open_image_act = QAction(
            ui_constants.translate_constant(ui_constants.ACTION_OPEN_IMAGE), self
        )

        see_logs_act = QAction(
            ui_constants.translate_constant(ui_constants.ACTION_SEE_LOGS), self
        )

        exit_act = QAction(
            ui_constants.translate_constant(ui_constants.ACTION_EXIT), self
        )

        open_folder_act.triggered.connect(self.handle_open_folder)
        open_image_act.triggered.connect(self.handle_open_image)

        see_logs_act.triggered.connect(self.handle_see_logs)
        exit_act.triggered.connect(self.main_win.close)

        file_menu.addAction(open_folder_act)
        file_menu.addAction(open_image_act)
        file_menu.addSeparator()
        if sys.platform == "win32":
            create_shortcut = QAction(
                ui_constants.translate_constant(
                    ui_constants.ACTION_CREATE_DESKTOP_SHORTCUT
                ),
                self,
            )
            create_shortcut.triggered.connect(self.handle_desktop_shortcut)
            file_menu.addAction(create_shortcut)
        file_menu.addAction(see_logs_act)
        file_menu.addSeparator()
        file_menu.addAction(exit_act)

        # Recen menu
        self.recent_menu = self.addMenu(
            ui_constants.translate_constant(ui_constants.MENU_RECENT)
        )
        self.recent_menu.aboutToShow.connect(self.populate_recent_menu)

        # Language menu
        self.setup_language_menu()

        # --- HELP MENU ---
        help_menu = self.addMenu(
            ui_constants.translate_constant(ui_constants.MENU_HELP)
        )
        user_manual_act = QAction(
            ui_constants.translate_constant(ui_constants.ACTION_USER_MANUAL), self
        )
        about_act = QAction(
            ui_constants.translate_constant(ui_constants.ACTION_ABOUT), self
        )
        feedback_act = QAction(
            ui_constants.translate_constant(ui_constants.ACTION_SEND_FEEDBACK), self
        )

        user_manual_act.triggered.connect(self.handle_user_manual)
        about_act.triggered.connect(self.handle_about)
        feedback_act.triggered.connect(self.handle_feedback)

        help_menu.addAction(user_manual_act)
        help_menu.addAction(feedback_act)
        help_menu.addAction(about_act)

    def populate_recent_menu(self):
        """Clears the submenu and regenerates text items using the self-healed list."""
        self.recent_menu.clear()

        # Pulls the already verified and pruned path array
        recent_paths = self.settings_mgr.get_recent_paths()

        if not recent_paths:
            empty_act = QAction(
                ui_constants.translate_constant(ui_constants.ACTION_NO_RECENT_ITEMS),
                self,
            )
            empty_act.setEnabled(False)
            self.recent_menu.addAction(empty_act)
            return

        # Render active working items only
        for path_str in recent_paths:
            p = Path(path_str)
            display_name = f"{p.name} ({p.parent.name})" if p.is_file() else p.name

            action = QAction(display_name, self)
            action.setStatusTip(path_str)

            action.triggered.connect(
                lambda checked, target=path_str: self.handle_load_recent(target)
            )
            self.recent_menu.addAction(action)

    def setup_language_menu(self):
        # --- LANGUAGE MENU ---
        lang_menu = self.addMenu(
            ui_constants.translate_constant(ui_constants.MENU_LANGUAGE_TITLE)
        )

        # Group actions to behave like exclusive radio selections
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)

        app_instance = QApplication.instance()
        current_lang = getattr(app_instance, "base_lang", "en")

        for lang_code in ui_constants.SUPPORTED_LANGUAGES:
            # Directly extract the native string literal payload
            native_label = ui_constants.LANGUAGE_DISPLAY_NAMES.get(lang_code, lang_code)

            # Build checkable action properties using the clean native string directly
            action = QAction(native_label, self, checkable=True)
            action.setData(lang_code)

            if lang_code == current_lang:
                action.setChecked(True)

            action.triggered.connect(self.handle_language_change)
            lang_group.addAction(action)
            lang_menu.addAction(action)

    # --- ACTIONS ---
    def handle_open_folder(self):
        self.setVisible(False)
        self.main_win.select_directory()

    def handle_open_image(self):
        self.setVisible(False)
        self.main_win.select_individual_image_file()

    def handle_load_recent(self, path_str):
        self.setVisible(False)
        self.main_win.open_recent_dir(path_str)

    def handle_see_logs(self):
        """
        Locates the application's local log directory and opens it natively.
        Logs system failures silently to file and triggers visual toast notifications.
        """
        self.setVisible(False)
        raw_data_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppLocalDataLocation
        )
        log_dir = Path(raw_data_dir)
        # --- FILESYSTEM CHECK ---
        try:
            if not log_dir.exists():
                log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # 1. Log the full traceback information to your background log file
            logger.exception(
                "Failed to open log folder due to missing directory permissions."
            )
            # 2. Inform the user gracefully on screen using your status manager
            self.main_win.status_manager.show_center_notification(
                ui_constants.translate_constant(
                    ui_constants.NOTIFICATION_LOG_PERMISSION_DENIED
                )
            )
            return
        except Exception:
            logger.exception(
                "Unexpected system exception occurred during log folder preparation."
            )
            self.main_win.status_manager.show_center_notification(
                ui_constants.translate_constant(
                    ui_constants.NOTIFICATION_LOG_SYSTEM_ERROR
                )
            )
            return

        # --- OPERATING SYSTEM LAUNCHER CHECK ---
        folder_url = QUrl.fromLocalFile(str(log_dir))
        success = QDesktopServices.openUrl(folder_url)

        if not success:
            # Log the platform launch failure error
            logger.error(
                f"OS Shell failed to trigger default file manager for path: {log_dir}"
            )
            # Notify the user smoothly
            self.main_win.status_manager.show_center_notification(
                ui_constants.translate_constant(
                    ui_constants.NOTIFICATION_OS_LAUNCH_FAILED
                )
            )

    def handle_about(self):
        """
        Displays an advanced HTML About dialog where users can natively
        highlight, select, and copy text values with their mouse.
        """
        self.setVisible(False)
        # 1. Instantiate an explicit instance instead of using the static shortcut wrapper
        msg_box = QMessageBox(self.main_win)

        # 2. Assign properties cleanly using native methods
        msg_box.setWindowTitle(
            ui_constants.translate_constant(ui_constants.DIALOG_TITLE_ABOUT)
        )
        if self.main_win.windowIcon() and not self.main_win.windowIcon().isNull():
            # Grabs your app icon and scales it to a standard crisp crisp 48x48 layout
            app_pixmap = self.main_win.windowIcon().pixmap(48, 48)
            msg_box.setIconPixmap(app_pixmap)
        else:
            # Fallback if no window icon is loaded yet in your main app lifecycle
            msg_box.setIcon(QMessageBox.Icon.NoIcon)
        # 3. CRUCIAL: Tell the underlying text renderer engine to allow selection highlights
        msg_box.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )

        # 4. Your polished HTML block layout
        about_html = self.file_mgr.load_localized_template(ui_constants.TEMPLATE_ABOUT)
        about_html = about_html.replace("@APP_VERSION", APP_VERSION)
        about_html = theme_manager.substitute_tokens(about_html)

        # 5. Populate and execute the modal popup event loop
        msg_box.setText(about_html)
        msg_box.exec()

    def handle_user_manual(self):
        """Launches the non-blocking compiled markdown README viewer dialog window."""
        self.setVisible(False)
        # Instantiated as non-modal (using show()) so users can keep this instruction window
        # open on a second monitor while actively cropping items in the main window
        self.manual_win = UserManualDialog(self.main_win, self.file_mgr)
        self.manual_win.show()

    def handle_feedback(self):
        self.setVisible(False)
        emailFeedback = EmailFeedbackDialog(self.main_win)
        emailFeedback.exec()

    def handle_desktop_shortcut(self):
        success = self.create_desktop_shortcut()
        if success:
            self.main_win.status_manager.show_center_notification(
                ui_constants.translate_constant(
                    ui_constants.NOTIFICATION_SHORTCUT_CREATED
                )
            )
        else:
            self.main_win.status_manager.show_center_notification(
                ui_constants.translate_constant(
                    ui_constants.NOTIFICATION_SHORTCUT_FAILED
                )
            )

    def create_desktop_shortcut(self):
        if sys.platform == "win32":
            try:
                import winshell
                from win32com.client import Dispatch

                desktop = Path(winshell.desktop())
                shortcut_path = desktop / "Lossless Crop.lnk"

                # Cast the executable string path to a clean Path object
                exe_path = Path(sys.executable)

                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(shortcut_path))

                shortcut.Targetpath = str(exe_path)
                shortcut.WorkingDirectory = str(exe_path.parent)
                shortcut.IconLocation = str(exe_path)
                shortcut.save()
                return True  # Let the UI know it succeeded
            except Exception:
                logger.exception("Failed to create desktop shortcut.")
                return False  # Let the UI know it failed (e.g. permissions issue)

    def handle_language_change(self) -> None:
        """Extracts the underlying language token string and signals the main window to prompt a restart."""
        action = self.sender()
        if not isinstance(action, QAction):
            return

        target_lang = action.data()
        app_instance = QApplication.instance()
        current_lang = getattr(app_instance, "base_lang", "en")

        # Guard Clause: Do nothing if the user clicks the language that is already active
        if target_lang == current_lang:
            return

        logger.info(
            "Language switch requested via menu bar sequence: '%s' -> '%s'",
            current_lang,
            target_lang,
        )

        # Forward the instruction smoothly to your main window interface layer
        if hasattr(self.main_win, "prompt_language_restart"):
            self.main_win.prompt_language_restart(target_lang)
