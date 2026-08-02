from PyQt6.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

from config.app_constants import APP_ROOT_DIR
from config.ui_constants import FOLDER_TEMPLATES, TEMPLATE_USER_MANUAL

# Import your global scope token replacement helper
from managers.theme_manager import substitute_tokens


class UserManualDialog(QDialog):
    def __init__(self, parent_window, file_manager):
        super().__init__(parent_window)
        self.main_win = parent_window
        self.file_mgr = file_manager

        self.setWindowTitle("User Manual")
        self.resize(750, 550)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.viewer = QTextBrowser(self)
        self.viewer.setOpenExternalLinks(True)

        # Strip out standard borders on the widget container itself
        self.viewer.setStyleSheet(
            "QTextBrowser { border: none; background: transparent; }"
        )

        layout.addWidget(self.viewer)
        self.load_manual()

    def load_manual(self):
        # 1. Fetch your raw GitHub markdown file from your file manager
        raw_markdown = self.file_mgr.load_user_manual()

        if not raw_markdown:
            self.viewer.setPlainText("Error: README.md documentation asset missing.")
            return

        # 2. Fetch the external shell HTML layout template file
        raw_html_template = self.file_mgr.load_asset(
            TEMPLATE_USER_MANUAL, FOLDER_TEMPLATES
        )

        if not raw_html_template:
            self.viewer.setPlainText("Error: HTML theme template asset missing.")
            return

        # 3. PyInstaller Extraction Directory Resolution

        self.viewer.setSearchPaths([str(APP_ROOT_DIR)])

        # 4. Use an isolated hidden QTextBrowser instance to turn Markdown strings into raw HTML content
        parser = QTextBrowser()
        parser.setMarkdown(raw_markdown)
        compiled_body_html = parser.toHtml()

        # Inject the parsed markdown straight into your external template placeholder slot
        complete_document = raw_html_template.format(
            user_manual_content=compiled_body_html
        )

        # 6. Run the whole combined document through your unified token substitution parser
        themed_html = substitute_tokens(complete_document)

        # 7. Render it directly onto your user manual scroll view panel canvas
        self.viewer.setHtml(themed_html)
