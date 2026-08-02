from PyQt6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

# Import your unified substitution engine from your theme manager file
from managers.theme_manager import substitute_tokens


class UserManualDialog(QDialog):
    def __init__(self, parent_window, file_manager):
        """
        parent_window: The main application window reference.
        file_manager: Your application file manager instance to read assets.
        """
        super().__init__(parent_window)
        self.main_win = parent_window
        self.file_mgr = file_manager

        # 1. Structural window configurations
        self.setWindowTitle("User Manual")
        self.resize(750, 550)

        # Anchors layout cleanly inside the center of your main viewport
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 2. Instantiate a modern read-only text scrolling pane
        self.viewer = QTextBrowser(self)

        # Essential: Allows clicking links (like GitHub profile items) to launch your browser
        self.viewer.setOpenExternalLinks(True)

        layout.addWidget(self.viewer)
        self.load_and_theme_manual()

    def load_and_theme_manual(self):
        """Loads your repository README, strips noise, themes tokens, and renders it."""
        # 3. Pull your GitHub README file asset directly using your existing file manager
        # (Change FOLDER or FILENAME labels below to match your asset configurations)
        raw_markdown = self.file_mgr.load_readme()

        if not raw_markdown:
            # Fallback if the path target drops out during packaging builds
            self.viewer.setPlainText("Error: README.md documentation asset missing.")
            return

        # 4. Run through your unified sanitation and color substitution loop!
        themed_markdown = substitute_tokens(raw_markdown)

        # 5. Tell the widget engine to natively compute the markup strings into visible elements
        self.viewer.setMarkdown(themed_markdown)
