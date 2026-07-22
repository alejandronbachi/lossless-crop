from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QLabel


class CenterNotification(QLabel):
    def __init__(self, parent_canvas, file_manager, ui_constants):
        # Bind it directly as a floating layer over your image display container
        super().__init__(parent_canvas)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.hide()

        # Load your custom cinematic alert styles
        self.setStyleSheet(
            file_manager.load_asset(
                ui_constants.STYLE_NOTIFICATIONS, ui_constants.FOLDER_STYLES
            )
        )

        # Apply your exact soft ambient shadow configuration
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def display_message(self, text: str):
        """Updates text payload data and forces layout size recalculation."""
        self.setText(text)
        self.adjustSize()
