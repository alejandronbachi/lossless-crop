import requests
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from config.app_constants import FORMSUBMIT_TOKEN


# =========================================================================
# 1. ASYNCHRONOUS BACKGROUND NETWORK WORKER
# =========================================================================
class FormSubmitWorker(QObject):
    """Pipes form data directly into the FormSubmit API gateway using AJAX-JSON format."""

    finished = pyqtSignal(bool, str)  # Emits (success_status, message)

    def __init__(self, target_email, user_email, category, message):
        super().__init__()
        # FormSubmit's AJAX endpoint syntax layout
        self.target_email = target_email
        self.user_email = user_email if user_email else "Anonymous User"
        self.category = category
        self.message = message

    def run(self):
        payload = {
            "Email": self.user_email,
            "Category": self.category,
            "Message": self.message,
            "_captcha": "false",
            "_subject": f"📥 New {self.category} from lossless-crop",
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://github.com",
            "Referer": "https://github.com/alejandronbachi/lossless-crop",
        }

        try:
            # FIXED SYNTAX: Added the explicit forward slash separator right before the variable
            endpoint_url = f"https://formsubmit.co/ajax/{self.target_email}"

            response = requests.post(
                endpoint_url, json=payload, headers=headers, timeout=12
            )

            if response.status_code == 200:
                self.finished.emit(True, "Success")
            else:
                self.finished.emit(
                    False, f"Server responded with status code: {response.status_code}"
                )
        except Exception as error_msg:
            self.finished.emit(False, str(error_msg))


# =========================================================================
# 2. COMPLETE USER INTERFACE DIALOG WINDOW
# =========================================================================
class EmailFeedbackDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Submit Feedback / Bug Report")
        self.setMinimumSize(420, 380)

        # Safe production-ready build variable
        self.TARGET_EMAIL = FORMSUBMIT_TOKEN

        # Prevent garbage collection issues by initializing reference tracking
        self.runtime_thread = None
        self.network_worker = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Contact Identification
        layout.addWidget(QLabel("Your Email (Optional, for follow-up details):"))
        self.email_field = QLineEdit()
        self.email_field.setPlaceholderText("developer@example.com")
        layout.addWidget(self.email_field)

        # Context Category Classification
        layout.addWidget(QLabel("Classification Category:"))
        self.category_select = QComboBox()
        self.category_select.addItems(
            ["Bug Report", "Feature Request ", "General UI Feedback "]
        )
        layout.addWidget(self.category_select)

        # Text Body Payload Description
        layout.addWidget(QLabel("Detailed Description:"))
        self.body_field = QTextEdit()
        self.body_field.setPlaceholderText(
            "Please specify what steps you took right before encountering the issue..."
        )
        layout.addWidget(self.body_field)

        # User Submission Controls Block
        actions_bar = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_submit = QPushButton("Submit")
        self.btn_submit.setDefault(True)  # Triggers when hitting 'Enter' key

        actions_bar.addWidget(self.btn_cancel)
        actions_bar.addWidget(self.btn_submit)
        layout.addLayout(actions_bar)

        # Wiring Event Signals
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_submit.clicked.connect(self.process_submission)

    def process_submission(self):
        feedback_text = self.body_field.toPlainText().strip()
        if not feedback_text:
            QMessageBox.warning(
                self, "Validation Error", "Description field cannot be submitted blank."
            )
            return

        # Interface lockout to ensure double clicks do not trigger duplicate transmissions
        self.btn_submit.setEnabled(False)
        self.btn_submit.setText("Transmitting...")

        # Construct safe multi-threaded runtime lifecycle
        self.runtime_thread = QThread()
        self.network_worker = FormSubmitWorker(
            self.TARGET_EMAIL,
            self.email_field.text().strip(),
            self.category_select.currentText(),
            feedback_text,
        )
        self.network_worker.moveToThread(self.runtime_thread)

        # Link functional dependencies across execution scope
        self.runtime_thread.started.connect(self.network_worker.run)
        self.network_worker.finished.connect(self.handle_callback_ui)
        self.network_worker.finished.connect(self.runtime_thread.quit)
        self.network_worker.finished.connect(self.network_worker.deleteLater)
        self.runtime_thread.finished.connect(self.runtime_thread.deleteLater)

        self.runtime_thread.start()

    def handle_callback_ui(self, is_successful, system_msg):
        # Restore button control state
        self.btn_submit.setEnabled(True)
        self.btn_submit.setText("Submit")

        if is_successful:
            QMessageBox.information(
                self,
                "Thank You",
                "Your feedback was sent successfully and delivered straight to my inbox!",
            )
            self.accept()  # Close window cleanly
        else:
            QMessageBox.critical(
                self,
                "Network Dispatch Failure",
                f"Transmission failed. Check internet access.\n\nError: {system_msg}",
            )
