from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QKeyEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication, QSpinBox


class KeyboardController(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self._last_focused_toolbar_widget = None
        self._shortcuts = []

        # 1. Track global focus shifts
        QApplication.instance().focusChanged.connect(self._track_toolbar_focus)
        QApplication.instance().installEventFilter(self)
        # 2. Monitor all actions happening inside the control toolbar
        if hasattr(self.main_window, "control_toolbar"):
            self.main_window.control_toolbar.installEventFilter(self)

        # 3. Setup shortcuts
        self._setup_navigation_shortcuts()
        self._setup_global_action_shortcuts()

    def _track_toolbar_focus(self, old_widget, new_widget):
        """Automatically bookmarks the last active widget inside the toolbar frame."""
        if (
            old_widget
            and hasattr(self.main_window, "control_toolbar")
            and self.main_window.control_toolbar.isAncestorOf(old_widget)
        ):
            self._last_focused_toolbar_widget = old_widget

    def _setup_navigation_shortcuts(self):
        """Focus shifting macros (Ctrl+Up / Ctrl+Down)."""
        # Ctrl + Down -> Escape back to main viewport workspace
        sc_exit = QShortcut(
            QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Down),
            self.main_window,
        )
        sc_exit.setContext(Qt.ShortcutContext.ApplicationShortcut)
        sc_exit.activated.connect(self.focus_main_workspace)
        self._shortcuts.append(sc_exit)

        # Ctrl + Up -> Step into toolbar controls tier
        sc_enter = QShortcut(
            QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_Up),
            self.main_window,
        )
        sc_enter.setContext(Qt.ShortcutContext.ApplicationShortcut)
        sc_enter.activated.connect(self.focus_toolbar)
        self._shortcuts.append(sc_enter)

    def _setup_global_action_shortcuts(self):
        """Keys that always override native widget behaviors globally."""
        actions = {
            Qt.Key.Key_Escape: self.main_window.close,
            Qt.Key.Key_P: self.toggle_preview_state,
            Qt.Key.Key_R: self.main_window.rotate_current_image,
            Qt.Key.Key_O: self.main_window.select_directory,
            Qt.Key.Key_I: self.main_window.select_individual_image_file,
            Qt.Key.Key_F: self.trigger_forward_navigation,
            Qt.Key.Key_B: self.trigger_backward_navigation,
        }

        for key, callback in actions.items():
            sc = QShortcut(QKeySequence(key), self.main_window)
            sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
            sc.activated.connect(callback)
            self._shortcuts.append(sc)

    def focus_main_workspace(self):
        """Drops focus out of the toolbar and explicitly hands it to the image canvas."""
        # 1. Forcefully pull focus out of whatever toolbar widget has it
        current_focus = self.main_window.focusWidget()
        if current_focus:
            current_focus.clearFocus()

        # 2. 🎯 THE FIX: Explicitly give keyboard focus to your canvas label
        if hasattr(self.main_window, "image_display_container"):
            self.main_window.image_display_container.setFocus()

        # 3. Keep your clean center notification
        self.main_window.status_manager.show_center_notification("Workspace Active")

    def focus_toolbar(self):
        """Restores focus to the last manipulated input slot, or defaults to the engine options dropdown."""
        # 1. Try to go back to exactly where the user left off
        if (
            self._last_focused_toolbar_widget
            and self._last_focused_toolbar_widget.isEnabled()
        ):
            self._last_focused_toolbar_widget.setFocus()
            self.main_window.status_manager.show_center_notification(
                "Toolbar Active (Restored Focus)"
            )
            return

        # 2. Fallback to the first interactive element (Engine ComboBox) if memory is empty
        if (
            hasattr(self.main_window, "combo_engine")
            and self.main_window.combo_engine.isEnabled()
        ):
            self.main_window.combo_engine.setFocus()
            self.main_window.status_manager.show_center_notification("Toolbar Active")

    def toggle_preview_state(self):
        """Centralized helper handler for the preview UI state."""
        current_state = self.main_window.cfg_show_preview.isChecked()
        self.main_window.cfg_show_preview.setChecked(not current_state)

    # --- Interfacing Core Engine Events (Spacebar, Arrows, Enter) ---
    def process_workflow_key(self, key):
        """Routes workflow keys ONLY when the workspace view has active focus."""
        if key == Qt.Key.Key_Space:
            self.main_window.process_and_execute_crop()
            self.trigger_forward_navigation()
            return True

        elif key in (Qt.Key.Key_S, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.main_window.process_and_execute_crop()
            return True

        # When the workspace is focused, arrows function normally as rapid turns
        elif key == Qt.Key.Key_Right:
            self.trigger_forward_navigation()
            return True

        elif key == Qt.Key.Key_Left:
            self.trigger_backward_navigation()
            return True

        return False

    def eventFilter(self, watched_obj, event):
        # Intercept keys originating from inside the toolbar row container
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()

            # Capture global workflow letters before the spinbox text cursor eats them
            if key in (
                Qt.Key.Key_F,
                Qt.Key.Key_B,
                Qt.Key.Key_P,
                Qt.Key.Key_R,
                Qt.Key.Key_O,
                Qt.Key.Key_I,
            ):
                if key == Qt.Key.Key_F:
                    self.trigger_forward_navigation()
                elif key == Qt.Key.Key_B:
                    self.trigger_backward_navigation()
                elif key == Qt.Key.Key_P:
                    self.toggle_preview_state()
                elif key == Qt.Key.Key_R:
                    self.main_window.rotate_current_image()
                elif key == Qt.Key.Key_O:
                    self.main_window.select_directory()
                elif key == Qt.Key.Key_I:
                    self.main_window.select_individual_image_file()
                return True  # Intercepted! Do not let the letter type inside the spinbox number box

            if key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
                current_focus = self.main_window.focusWidget()

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
