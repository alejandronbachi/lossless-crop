from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QSpinBox


class KeyboardController(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        # 1. Track global focus shifts
        QApplication.instance().installEventFilter(self)

    def toggle_preview_state(self):
        """Centralized helper handler for the preview UI state."""
        current_state = self.main_window.cfg_show_preview.isChecked()
        self.main_window.cfg_show_preview.setChecked(not current_state)

    def eventFilter(self, watched_obj, event):
        # Intercept keys originating from inside the toolbar row container
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()

            # Capture global workflow letters before the spinbox text cursor eats them
            if key in (
                Qt.Key.Key_F,
                Qt.Key.Key_D,
                Qt.Key.Key_B,
                Qt.Key.Key_A,
                Qt.Key.Key_P,
                Qt.Key.Key_Q,
                Qt.Key.Key_R,
                Qt.Key.Key_O,
                Qt.Key.Key_I,
                Qt.Key.Key_S,
                Qt.Key.Key_Space,
                Qt.Key.Key_Escape,
                Qt.Key.Key_Alt,
            ):
                if key in (Qt.Key.Key_F, Qt.Key.Key_D):
                    self.trigger_forward_navigation()
                if key in (Qt.Key.Key_B, Qt.Key.Key_A):
                    self.trigger_backward_navigation()
                if key in (Qt.Key.Key_P, Qt.Key.Key_Q):
                    self.toggle_preview_state()
                elif key == Qt.Key.Key_R:
                    self.main_window.rotate_current_image()
                elif key == Qt.Key.Key_O:
                    self.main_window.select_directory()
                elif key == Qt.Key.Key_I:
                    self.main_window.select_individual_image_file()
                elif key == Qt.Key.Key_S:
                    self.main_window.process_and_execute_crop()
                elif key == Qt.Key.Key_Space:
                    self.main_window.process_and_execute_crop()
                    self.trigger_forward_navigation()
                elif key == Qt.Key.Key_Escape:
                    self.main_window.close()
                elif key == Qt.Key.Key_Alt:
                    is_visible = self.main_window.custom_menu.isVisible()
                    self.main_window.custom_menu.setVisible(not is_visible)
                return True  # Intercepted! Do not let the letter type inside the spinbox number box

            # EXCEPTION: Spinboxes keep their default text cursor manipulation
            if key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
                current_focus = self.main_window.focusWidget()
                if not current_focus:
                    return super().eventFilter(watched_obj, event)

                # If focus is inside a spinbox, check if the text cursor is at the edge boundaries
                if isinstance(current_focus, QSpinBox):
                    line_edit = current_focus.lineEdit()
                    cursor_pos = line_edit.cursorPosition()
                    text_content = line_edit.text()

                    # Extract prefix and suffix lengths dynamically from the widget configuration
                    prefix_len = len(current_focus.prefix())  # e.g., len("W: ") -> 3
                    suffix_len = len(current_focus.suffix())  # e.g., len(" px") -> 3

                    # Calculate the exact visual boundary points for the numerical digits
                    num_start_boundary = prefix_len
                    num_end_boundary = len(text_content) - suffix_len

                    # If pressing Right at the end of the number string, Tab out!
                    if key == Qt.Key.Key_Right and cursor_pos == num_end_boundary:
                        tab_event = QKeyEvent(
                            QEvent.Type.KeyPress,
                            Qt.Key.Key_Tab,
                            Qt.KeyboardModifier.NoModifier,
                        )
                        QApplication.postEvent(current_focus, tab_event)
                        return True

                    # If pressing Left at the beginning of the number string, Shift+Tab out!
                    elif key == Qt.Key.Key_Left and cursor_pos == num_start_boundary:
                        shift_tab_event = QKeyEvent(
                            QEvent.Type.KeyPress,
                            Qt.Key.Key_Tab,
                            Qt.KeyboardModifier.ShiftModifier,
                        )
                        QApplication.postEvent(current_focus, shift_tab_event)
                        return True

                    # Otherwise, let them move the cursor normally within the number digits
                    return super().eventFilter(watched_obj, event)

                # TRANSLATION ENGINE: Convert arrows to navigation tabs
                if key == Qt.Key.Key_Right:
                    # Synthesize a standard 'Tab' key press event
                    tab_event = QKeyEvent(
                        QEvent.Type.KeyPress,
                        Qt.Key.Key_Tab,
                        Qt.KeyboardModifier.NoModifier,
                    )
                    QApplication.postEvent(current_focus, tab_event)
                    return True  # Consume the original arrow event completely

                elif key == Qt.Key.Key_Left:
                    # Synthesize a 'Shift + Tab' backward key press event
                    shift_tab_event = QKeyEvent(
                        QEvent.Type.KeyPress,
                        Qt.Key.Key_Tab,
                        Qt.KeyboardModifier.ShiftModifier,
                    )
                    QApplication.postEvent(current_focus, shift_tab_event)
                    return True  # Consume the original arrow event completely

        return super().eventFilter(watched_obj, event)

    # --- Add these two helper methods inside your KeyboardController class ---

    def trigger_forward_navigation(self):
        """Universal handler to advance the image canvas forward."""
        if alert := self.main_window.image_session.next():
            self.main_window.status_manager.show_center_notification(alert)
        else:
            self.main_window.load_image_to_viewport()

    def trigger_backward_navigation(self):
        """Universal handler to move the image canvas backward."""
        if alert := self.main_window.image_session.previous():
            self.main_window.status_manager.show_center_notification(alert)
        else:
            self.main_window.load_image_to_viewport()
