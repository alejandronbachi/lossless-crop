import logging
from pathlib import Path

from PyQt6.QtCore import QStandardPaths, Qt, QUrl
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtWidgets import QMenuBar, QMessageBox

from config.ui_constants import FOLDER_TEMPLATES, TEMPLATE_ABOUT
from managers import theme_manager
from managers.file_manager import FileManager
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
        file_menu = self.addMenu("File")

        open_folder_act = QAction("Open Directory", self)
        open_image_act = QAction("Open Image", self)

        self.recent_menu = self.addMenu("Recent")
        self.recent_menu.aboutToShow.connect(self.populate_recent_menu)

        see_logs_act = QAction("See Logs", self)
        exit_act = QAction("Exit", self)

        open_folder_act.triggered.connect(self.handle_open_folder)
        open_image_act.triggered.connect(self.handle_open_image)
        see_logs_act.triggered.connect(self.handle_see_logs)
        exit_act.triggered.connect(self.main_win.close)

        file_menu.addAction(open_folder_act)
        file_menu.addAction(open_image_act)

        file_menu.addAction(see_logs_act)
        file_menu.addSeparator()
        file_menu.addAction(exit_act)

        # --- HELP MENU ---
        help_menu = self.addMenu("Help")
        user_manual_act = QAction("User Manual", self)
        about_act = QAction("About", self)

        user_manual_act.triggered.connect(self.handle_user_manual)
        about_act.triggered.connect(self.handle_about)

        help_menu.addAction(user_manual_act)
        help_menu.addAction(about_act)

    def populate_recent_menu(self):
        """Clears the submenu and regenerates text items using the self-healed list."""
        self.recent_menu.clear()

        # Pulls the already verified and pruned path array
        recent_paths = self.settings_mgr.get_recent_paths()

        if not recent_paths:
            empty_act = QAction("No Recent Items", self)
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

    # --- ACTIONS ---
    def handle_open_folder(self):
        self.setVisible(False)
        self.main_win.select_directory()

    def handle_open_image(self):
        self.setVisible(False)
        self.main_win.select_individual_image_file()

    def handle_load_recent(self, path_str):
        self.setVisible(False)
        self.main_win.automate_folder_loading(path_str)

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
                "Permission denied: Cannot access log directory."
            )
            return
        except Exception:
            logger.exception(
                "Unexpected system exception occurred during log folder preparation."
            )
            self.main_win.status_manager.show_center_notification(
                "System error: Unable to prepare logs."
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
                "OS failed to launch file explorer."
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
        msg_box.setWindowTitle("About Lossless Crop")
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
        about_html = self.file_mgr.load_asset(TEMPLATE_ABOUT, FOLDER_TEMPLATES)
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
