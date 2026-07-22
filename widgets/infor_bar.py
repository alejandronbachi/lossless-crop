from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel


class InfoBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("info_bar_widget")

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)

        self._build_ui()

    def _build_ui(self):
        self.layout.addStretch(1)

        # Primary Centered File Status Label
        self.lbl_status = QLabel("Ready. Open a folder to start cropping.")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #bbb; font-size: 15px; font-weight: 500;")
        self.layout.addWidget(self.lbl_status)

        self.layout.addStretch(1)

        # Secondary Right Edge Metrics Tracker
        self.lbl_metrics = QLabel("")
        self.lbl_metrics.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.lbl_metrics.setStyleSheet(
            "color: #888888; font-family: monospace; font-size: 13px; font-weight: bold;"
        )
        self.layout.addWidget(self.lbl_metrics)
