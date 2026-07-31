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
        self.setObjectName("NotificationOverlay")

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


class CommandsOverlay(QLabel):
    def __init__(self, parent_container, file_manager, ui_constants):
        super().__init__(parent_container)
        self.hide()

        self.setObjectName("CommandsOverlay")
        self.setText(
            file_manager.load_asset(
                ui_constants.TEMPLATE_COMMANDS, ui_constants.FOLDER_TEMPLATES
            )
        )

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(4)
        shadow.setColor(QColor("#000000"))
        shadow.setOffset(1, 1)
        self.setGraphicsEffect(shadow)


class SplashHUD(QLabel):
    def __init__(self, parent_container, file_manager, ui_constants):
        super().__init__(parent_container)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()  # Maintained hidden by default until evaluated on launch
        self.setObjectName("SplashHUD")
        splash_text = file_manager.load_asset(
            ui_constants.TEMPLATE_SPLASH, ui_constants.FOLDER_TEMPLATES
        )
        self.setText(splash_text)


class TelemetryHUD(QLabel):
    def __init__(self, parent_container, file_manager, ui_constants):
        # 🚀 Pass the canvas/central container directly
        super().__init__(parent_container)
        self.setObjectName(ui_constants.WIDGET_TELEMETRY_HUD)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.hide()  # Hidden by default until bar collapses
        # 3. Restore your exact asset-loaded styling rule variable
        self.setObjectName("TelemetryHUD")
        # 4. Restore your exact soft drop-shadow graphic layer effects
        telemetry_shadow = QGraphicsDropShadowEffect(self)
        telemetry_shadow.setBlurRadius(3)
        telemetry_shadow.setColor(QColor("#000000"))
        telemetry_shadow.setOffset(1, 1)
        self.setGraphicsEffect(telemetry_shadow)
