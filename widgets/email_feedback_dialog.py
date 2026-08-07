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

from config import ui_constants
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
        self.user_email = (
            user_email if user_email else ui_constants.FEEDBACK_ANONYMOUS_USER
        )
        self.category = category
        self.message = message

    def run(self):
        payload = {
            "Email": self.user_email,
            "Category": self.category,
            "Message": self.message,
            "_captcha": ui_constants.FEEDBACK_CAPTCHA_FALSE,
            "_subject": ui_constants.FEEDBACK_SUBJECT_TEMPLATE.format(self.category),
        }

        headers = {
            "User-Agent": ui_constants.FEEDBACK_USER_AGENT,
            "Accept": ui_constants.FEEDBACK_ACCEPT,
            "Content-Type": ui_constants.FEEDBACK_CONTENT_TYPE,
            "Origin": ui_constants.FEEDBACK_ORIGIN,
            "Referer": ui_constants.FEEDBACK_REFERER,
        }

        try:
            # FIXED SYNTAX: Added the explicit forward slash separator right before the variable
            endpoint_url = ui_constants.FEEDBACK_ENDPOINT_TEMPLATE.format(
                self.target_email
            )

            response = requests.post(
                endpoint_url,
                json=payload,
                headers=headers,
                timeout=ui_constants.FEEDBACK_TIMEOUT,
            )

            if response.status_code == 200:
                self.finished.emit(True, ui_constants.FEEDBACK_SUCCESS_STR)
            else:
                self.finished.emit(
                    False,
                    f"{ui_constants.FEEDBACK_SERVER_ERROR_PREFIX}{response.status_code}",
                )
        except Exception as error_msg:
            self.finished.emit(False, str(error_msg))


# =========================================================================
# 2. COMPLETE USER INTERFACE DIALOG WINDOW
# =========================================================================
class EmailFeedbackDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(ui_constants.FEEDBACK_WINDOW_TITLE)
        self.setMinimumSize(
            ui_constants.FEEDBACK_MIN_WIDTH, ui_constants.FEEDBACK_MIN_HEIGHT
        )

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
        layout.addWidget(QLabel(ui_constants.FEEDBACK_LABEL_EMAIL))
        self.email_field = QLineEdit()
        self.email_field.setPlaceholderText(ui_constants.FEEDBACK_PLACEHOLDER_EMAIL)
        layout.addWidget(self.email_field)

        # Context Category Classification
        layout.addWidget(QLabel(ui_constants.FEEDBACK_LABEL_CATEGORY))
        self.category_select = QComboBox()
        self.category_select.addItems(ui_constants.FEEDBACK_CATEGORIES_ITEMS)
        layout.addWidget(self.category_select)

        # Text Body Payload Description
        layout.addWidget(QLabel(ui_constants.FEEDBACK_LABEL_DESCRIPTION))
        self.body_field = QTextEdit()
        self.body_field.setPlaceholderText(
            ui_constants.FEEDBACK_PLACEHOLDER_DESCRIPTION
        )
        layout.addWidget(self.body_field)

        # User Submission Controls Block
        actions_bar = QHBoxLayout()
        self.btn_cancel = QPushButton(ui_constants.FEEDBACK_BTN_CANCEL)
        self.btn_submit = QPushButton(ui_constants.FEEDBACK_BTN_SUBMIT)
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
                self,
                ui_constants.FEEDBACK_VALIDATION_TITLE,
                ui_constants.FEEDBACK_VALIDATION_MSG,
            )
            return

        # Interface lockout to ensure double clicks do not trigger duplicate transmissions
        self.btn_submit.setEnabled(False)
        self.btn_submit.setText(ui_constants.FEEDBACK_BTN_TRANSMITTING)

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
        self.btn_submit.setText(ui_constants.FEEDBACK_BTN_SUBMIT)

        if is_successful:
            QMessageBox.information(
                self,
                ui_constants.FEEDBACK_THANKYOU_TITLE,
                ui_constants.FEEDBACK_THANKYOU_MSG,
            )
            self.accept()  # Close window cleanly
        else:
            QMessageBox.critical(
                self,
                ui_constants.FEEDBACK_FAILURE_TITLE,
                ui_constants.FEEDBACK_FAILURE_TEMPLATE.format(system_msg),
            )
