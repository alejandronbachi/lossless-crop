from pathlib import Path

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QMenuBar


class ApplicationMenuBar(QMenuBar):
    def __init__(self, parent_window, settings_manager):
        super().__init__(parent_window)
        self.main_win = parent_window
        self.settings_mgr = settings_manager

        self.init_menus()

    def init_menus(self):
        # --- FILE MENU ---
        file_menu = self.addMenu("File")

        open_folder_act = QAction("Open Folder", self)
        open_image_act = QAction("Open Image", self)

        self.recent_menu = QMenu("Recent...", self)
        self.recent_menu.aboutToShow.connect(self.populate_recent_menu)

        see_logs_act = QAction("See Logs", self)
        exit_act = QAction("Exit", self)

        open_folder_act.triggered.connect(self.handle_open_folder)
        open_image_act.triggered.connect(self.handle_open_image)
        see_logs_act.triggered.connect(self.handle_see_logs)
        exit_act.triggered.connect(self.main_win.close)

        file_menu.addAction(open_folder_act)
        file_menu.addAction(open_image_act)
        file_menu.addMenu(self.recent_menu)
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
        pass

    def handle_user_manual(self):
        pass

    def handle_about(self):
        pass
