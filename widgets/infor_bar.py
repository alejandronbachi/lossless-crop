from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel

from config import ui_constants


class InfoBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName(ui_constants.WIDGET_INFO_BAR)
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)

        self._build_ui()

    def _build_ui(self):
        # Left directory name label (Column 0)
        self.lbl_directory = QLabel("")
        self.lbl_directory.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.lbl_directory.setObjectName("lblDirectory")
        self.lbl_directory.setVisible(False)
        self.layout.addWidget(self.lbl_directory, 0, 0)

        # Primary Centered File Status Label (Column 1)
        self.lbl_status = QLabel(
            ui_constants.translate_constant(ui_constants.TEXT_READY_STATUS)
        )
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setObjectName("lblStatus")
        self.layout.addWidget(self.lbl_status, 0, 1)

        # Secondary Right Edge Metrics Tracker (Column 2)
        self.lbl_metrics = QLabel("")
        self.lbl_metrics.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.lbl_metrics.setObjectName("lblMetrics")
        self.layout.addWidget(self.lbl_metrics, 0, 2)

        # 2. Force side columns to stretch equally, locking the center in place
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 0)  # Center only takes required space
        self.layout.setColumnStretch(2, 1)
