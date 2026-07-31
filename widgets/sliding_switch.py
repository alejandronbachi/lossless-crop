# 🔥🚀 [START OF MODIFICATION: Animated Sliding Switch Subclass] 🚀🔥
from PyQt6.QtCore import QEasingCurve, QPointF, QRectF, QSize, Qt, QVariantAnimation
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QAbstractButton

from managers import theme_manager


class SlidingSwitch(QAbstractButton):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setText(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setMouseTracking(True)
        self._is_hovered = False
        self._is_focused = False

        self.track_width = 38
        self.track_height = 20
        self.thumb_radius = 6
        self._thumb_x = self.thumb_radius + 4

        self.animation = QVariantAnimation(self)
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.valueChanged.connect(self._animate_thumb)
        self.setMinimumHeight(self.track_height + 8)

    def enterEvent(self, event):
        self._is_hovered = True
        self.update()  # Request immediate repaint pass
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self.update()  # Request immediate repaint pass
        super().leaveEvent(event)

    def sizeHint(self):
        """Informs parent layouts of the exact pixel boundaries required for this element."""
        # Add font metrics width to the track width so the text label isn't chopped
        font_width = (
            self.fontMetrics().horizontalAdvance(self.text()) if self.text() else 0
        )
        return QSize(self.track_width + 16 + font_width, self.track_height + 8)

    def _animate_thumb(self, value):
        """Callback that repaints the button frame-by-frame during the slide."""
        self._thumb_x = value
        self.update()

    def nextCheckState(self):
        """Intercepts clicks to trigger the sliding timeline direction."""
        super().nextCheckState()
        start = self._thumb_x
        # Calculate target endpoint boundaries based on the toggle state
        end = (
            (self.track_width - self.thumb_radius - 4)
            if self.isChecked()
            else (self.thumb_radius + 4)
        )

        self.animation.stop()
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.start()

    def setChecked(self, checked: bool):
        """Intercepts setting states from code to force the knob to snap to the correct side."""
        super().setChecked(checked)

        if checked:
            target_x = self.track_width - self.thumb_radius - 4
        else:
            target_x = self.thumb_radius + 4

        # If an interpolation timeline loop is running, stop it to prevent coordinate jumps
        if (
            hasattr(self, "animation")
            and self.animation.state() == QVariantAnimation.State.Running
        ):
            self.animation.stop()

        # Direct snap updates for the drawing layout matrix view coordinates
        self._thumb_x = target_x
        self.update()

    def paintEvent(self, event):
        """Vector paints the switch surfaces cleanly using your active theme manager palette colors."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_active_interaction = self._is_hovered or self._is_focused
        if self.isChecked():
            bg_color = QColor(theme_manager.get_color("@PRIMARY_ACCENT"))
            border_color = QColor(
                "#FFFFFF"
                if is_active_interaction
                else theme_manager.get_color("@PRIMARY_ACCENT")
            )
            thumb_color = QColor("#FFFFFF")
        else:
            # If the mouse glides over an unchecked switch, use your hover tokens instead of resting styles!
            bg_color = QColor(
                theme_manager.get_color(
                    "@SPIN_BTN_HOVER" if is_active_interaction else "@SPIN_BG"
                )
            )
            border_color = QColor(
                theme_manager.get_color(
                    "@SPIN_BORDER_HOVER" if self._is_hovered else "@SPIN_BORDER"
                )
            )
            thumb_color = QColor("#FFFFFF" if self._is_hovered else "#8B8B8B")

        text_token = (
            "@CHECKBOX_TEXT_HOVER" if self._is_hovered else "@DRAWER_CHECKBOX_TEXT"
        )
        text_color = QColor(theme_manager.get_color(text_token))

        # 1. Paint the outer rounded pill track layer
        painter.setPen(border_color)
        painter.setBrush(bg_color)
        track_rect = QRectF(
            2,
            (self.height() - self.track_height) / 2,
            self.track_width,
            self.track_height,
        )
        painter.drawRoundedRect(
            track_rect, self.track_height / 2, self.track_height / 2
        )

        # 2. Paint the circular sliding knob thumb node (Fixed Y center coordinate offset math)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(thumb_color)
        center_y = self.height() / 2
        painter.drawEllipse(
            QPointF(self._thumb_x, center_y), self.thumb_radius, self.thumb_radius
        )
        # 3. Paint your descriptive setting option label text on the right
        if self.text():
            painter.setPen(text_color)
            # Fetch the widget's current default typography font layout profile
            switch_font = self.font()
            switch_font.setItalic(is_active_interaction)
            painter.setFont(switch_font)
            text_x = self.track_width + 12
            painter.drawText(
                text_x,
                0,
                self.width() - text_x,
                self.height(),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                self.text(),
            )

    def focusInEvent(self, event):
        self._is_focused = True
        self.update()  # Request immediate repaint pass
        super().focusInEvent(event)

    #  Capture when the widget loses keyboard tab focus highlight
    def focusOutEvent(self, event):
        self._is_focused = False
        self.update()  # Request immediate repaint pass
        super().focusOutEvent(event)

    #  Intercept Enter/Return keyboard strikes to dynamically toggle the slider switch
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Programmatically trigger a click to initiate the sliding timeline animation pass
            self.click()
            event.accept()
        else:
            super().keyPressEvent(event)
