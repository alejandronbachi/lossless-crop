from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel

from config import ui_constants


class InfoBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName(ui_constants.WIDGET_INFO_BAR)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)

        self._build_ui()

    def _build_ui(self):
        self.layout.addStretch(1)

        # Primary Centered File Status Label
        self.lbl_status = QLabel(ui_constants.TEXT_READY_STATUS)
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setObjectName("lblStatus")
        self.layout.addWidget(self.lbl_status)

        self.layout.addStretch(1)

        # Secondary Right Edge Metrics Tracker
        self.lbl_metrics = QLabel("")
        self.lbl_metrics.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.lbl_metrics.setObjectName("lblMetrics")
        self.layout.addWidget(self.lbl_metrics)
