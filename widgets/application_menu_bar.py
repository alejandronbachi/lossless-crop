from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog, QMenuBar, QMessageBox


class ApplicationMenuBar(QMenuBar):
    def __init__(self, parent_window):
        """
        parent_window: The existing QMainWindow instance where this menu will live.
        """
        super().__init__(parent_window)
        self.main_win = parent_window
        self.init_menus()

    def init_menus(self):
        # --- FILE MENU ---
        file_menu = self.addMenu("File")

        # Create actions
        open_folder_act = QAction("Open Folder", self)
        open_image_act = QAction("Open Image", self)
        recent_folders_act = QAction("Recent Folders", self)
        see_logs_act = QAction("See Logs", self)
        exit_act = QAction("Exit", self)

        # Connect actions to local class methods
        open_folder_act.triggered.connect(self.handle_open_folder)
        open_image_act.triggered.connect(self.handle_open_image)
        recent_folders_act.triggered.connect(self.handle_recent_folders)
        see_logs_act.triggered.connect(self.handle_see_logs)
        exit_act.triggered.connect(self.main_win.close)  # Directly closes the main app

        # Build File menu
        file_menu.addAction(open_folder_act)
        file_menu.addAction(open_image_act)
        file_menu.addAction(recent_folders_act)
        file_menu.addAction(see_logs_act)
        file_menu.addSeparator()
        file_menu.addAction(exit_act)

        # --- HELP MENU ---
        help_menu = self.addMenu("Help")

        # Create actions
        user_manual_act = QAction("User Manual", self)
        about_act = QAction("About", self)

        # Connect actions to local class methods
        user_manual_act.triggered.connect(self.handle_user_manual)
        about_act.triggered.connect(self.handle_about)

        # Build Help menu
        help_menu.addAction(user_manual_act)
        help_menu.addAction(about_act)

    # --- INDEPENDENT LOGIC METHODS ---
    def handle_open_folder(self):
        # Uses self.main_win as parent to center the native file dialog correctly
        folder_path = QFileDialog.getExistingDirectory(self.main_win, "Select Folder")
        if folder_path:
            print(f"Selected folder: {folder_path}")
            # You can call a method on your main app here if needed:
            # self.main_win.process_folder(folder_path)

    def handle_open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_win, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            print(f"Selected image: {file_path}")

    def handle_recent_folders(self):
        print("Displaying recent folders list...")

    def handle_see_logs(self):
        print("Opening system log viewer...")

    def handle_user_manual(self):
        print("Displaying user guide...")

    def handle_about(self):
        QMessageBox.about(
            self.main_win,
            "About Application",
            "Your Application Name\nVersion 1.0.0\nAll rights reserved.",
        )
