from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QSpinBox


class KeyboardController(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        QApplication.instance().installEventFilter(self)
        # --- FLAT HOTKEY MAP (Grade A Mapping) ---
        # Single actions, multi-step actions, and lambdas are mapped flatly.
        self.hotkeys = {
            Qt.Key.Key_F: self.trigger_forward_navigation,
            Qt.Key.Key_D: self.trigger_forward_navigation,
            Qt.Key.Key_B: self.trigger_backward_navigation,
            Qt.Key.Key_A: self.trigger_backward_navigation,
            Qt.Key.Key_P: self.toggle_preview_state,
            Qt.Key.Key_Q: self.toggle_preview_state,
            Qt.Key.Key_R: self.main_window.rotate_current_image,
            Qt.Key.Key_O: self.main_window.select_directory,
            Qt.Key.Key_I: self.main_window.select_individual_image_file,
            Qt.Key.Key_S: self.main_window.process_and_execute_crop,
            Qt.Key.Key_Escape: self.main_window.close,
            Qt.Key.Key_Space: self.main_window.crop_and_next,
            Qt.Key.Key_Alt: self._toggle_menu_visibility,
        }

    def toggle_preview_state(self):
        """Centralized helper handler for the preview UI state."""
        current_state = self.main_window.cfg_show_preview.isChecked()
        self.main_window.cfg_show_preview.setChecked(not current_state)

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

    def _toggle_menu_visibility(self):
        """Handles widget polling toggles outside the main loop."""
        is_visible = self.main_window.custom_menu.isVisible()
        self.main_window.custom_menu.setVisible(not is_visible)

    def _handle_spinbox_navigation(self, current_focus, key):
        """Isolated structural helper to compute digit visual boundaries."""
        line_edit = current_focus.lineEdit()
        cursor_pos = line_edit.cursorPosition()

        # Compute exact boundary metrics
        num_start_boundary = len(current_focus.prefix())
        num_end_boundary = len(line_edit.text()) - len(current_focus.suffix())

        # Determine if we should punch a focus-hop event
        if key == Qt.Key.Key_Right and cursor_pos == num_end_boundary:
            self._synthesize_tab(current_focus, Qt.KeyboardModifier.NoModifier)
            return True
        elif key == Qt.Key.Key_Left and cursor_pos == num_start_boundary:
            self._synthesize_tab(current_focus, Qt.KeyboardModifier.ShiftModifier)
            return True

        return False  # Fall back to native character-by-character navigation

    def _synthesize_tab(self, target_widget, modifier):
        """Helper to safely post focus navigation events into the application loop."""
        tab_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Tab, modifier)
        QApplication.postEvent(target_widget, tab_event)

    def eventFilter(self, watched_obj, event):
        if event.type() != QEvent.Type.KeyPress:
            return super().eventFilter(watched_obj, event)

        key = event.key()

        # Step 1: Direct Lookup Strategy
        action = self.hotkeys.get(key)
        if action:
            action()
            return True

        # Step 2: Contextual Navigation Strategy
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            current_focus = self.main_window.focusWidget()
            if not current_focus:
                return super().eventFilter(watched_obj, event)

            # Route spinbox exceptions
            if isinstance(current_focus, QSpinBox):
                if self._handle_spinbox_navigation(current_focus, key):
                    return True
                return super().eventFilter(watched_obj, event)

            # Route global widget arrow-to-tab translations
            modifier = (
                Qt.KeyboardModifier.ShiftModifier
                if key == Qt.Key.Key_Left
                else Qt.KeyboardModifier.NoModifier
            )
            self._synthesize_tab(current_focus, modifier)
            return True

        return super().eventFilter(watched_obj, event)
