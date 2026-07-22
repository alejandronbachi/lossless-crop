from PyQt6.QtCore import QObject, QTimer


class NotificationManager(QObject):
    def __init__(self, main_app, notification_widget):
        super().__init__()
        self.main_app = main_app
        self.lbl_notification = notification_widget

        # 1-second clean single-shot auto-dismiss countdown clock
        self.notification_timer = QTimer()
        self.notification_timer.setInterval(1000)
        self.notification_timer.setSingleShot(True)
        self.notification_timer.timeout.connect(self.lbl_notification.hide)

    def show_center_notification(self, text: str):
        """Displays a cinematic floating alert in the exact middle of the image area."""
        # 🚀 Architectural Upgrade: Uses your active memory settings model!
        if (
            hasattr(self.main_app, "settings")
            and not self.main_app.settings.show_toasts
        ):
            return

        # Load message details and resize widget bounding box metrics
        self.lbl_notification.display_message(text)

        # Recalculate and center the layout position boundaries
        self.reposition_notification()

        # Reveal it over the canvas and start the single-shot countdown
        self.lbl_notification.show()
        self.lbl_notification.raise_()
        self.notification_timer.start()

    def reposition_notification(self):
        """Computes coordinate shifts to lock the widget dead center over the parent container."""
        parent = self.lbl_notification.parentWidget()
        if not parent:
            return

        parent_w = parent.width()
        parent_h = parent.height()
        box_w = self.lbl_notification.width()
        box_h = self.lbl_notification.height()

        x = (parent_w - box_w) // 2
        y = (parent_h - box_h) // 2

        self.lbl_notification.move(x, y)
