from PyQt6.QtCore import QObject, QTimer

from widgets.notifications import (
    CenterNotification,
    CommandsOverlay,
    SplashHUD,
    TelemetryHUD,
)


class StatusManager(QObject):
    def __init__(
        self, main_app, canvas_container, info_bar_widget, file_manager, ui_constants
    ):
        super().__init__()
        self.main_app = main_app
        self.canvas_container = canvas_container
        self.info_bar = info_bar_widget
        self.ui_constants = ui_constants

        # Instantiate floating canvas overlays directly inside the manager
        self.lbl_notification = CenterNotification(
            canvas_container, file_manager, ui_constants
        )
        self.lbl_commands_overlay = CommandsOverlay(
            canvas_container, file_manager, ui_constants
        )
        self.lbl_splash_hud = SplashHUD(canvas_container, file_manager, ui_constants)
        self.lbl_telemetry_hud = TelemetryHUD(
            canvas_container, file_manager, ui_constants
        )

        # 1-second auto-dismiss clock for cinematic center notifications
        self.notification_timer = QTimer()
        self.notification_timer.setInterval(1000)
        self.notification_timer.setSingleShot(True)
        self.notification_timer.timeout.connect(self.lbl_notification.hide)

        #  60 FPS LAZY ENGINE: Setup a throttling heartbeat timer
        self._is_dirty = False
        self.lazy_timer = QTimer(self)
        self.lazy_timer.setInterval(16)  # ~16ms matches roughly 60 Frames Per Second
        self.lazy_timer.timeout.connect(self._on_lazy_heartbeat_tick)
        self.lazy_timer.start()

    def invalidate_ui_state(self):
        """🚀 Mark the view state as dirty. High-frequency mouse events call this!"""
        self._is_dirty = True

    def _on_lazy_heartbeat_tick(self):
        """🚀 The Frame-Rate Gatekeeper: Executes heavy updates ONLY if a change actually occurred."""
        if not self._is_dirty:
            return  # The mouse hasn't moved; drop out immediately to save CPU cycles!

        # Reset flag state instantly to catch subsequent frames
        self._is_dirty = False

        #  Run heavy UI calculations exactly once per 16ms render window frame!
        self.main_app.update_resolution_metrics_display()
        self.main_app.update_zoom_hud_payload()

        self.update_status_and_telemetry()

    def show_center_notification(self, text: str):
        """Displays a cinematic floating alert in the exact middle of the image area."""
        if (
            hasattr(self.main_app, "settings")
            and not self.main_app.settings.show_toasts
        ):
            return

        self.notification_timer.stop()
        self.lbl_notification.display_message(text)
        self.reposition_center_notification()

        self.lbl_notification.show()
        self.lbl_notification.raise_()
        self.notification_timer.start()

    def set_empty_workspace_state(self):
        """Resets layout labels back to startup splash configurations."""
        self.info_bar.lbl_status.setText(self.ui_constants.TEXT_READY_STATUS)
        self.info_bar.lbl_metrics.setText("")
        self.lbl_telemetry_hud.hide()
        self.lbl_commands_overlay.hide()

        #  Ensure the splash layout panel is rendered visible and snapped perfectly to center
        self.lbl_splash_hud.show()
        self.lbl_splash_hud.raise_()
        self.reposition_splash_hud()

    # -------------------------------------------------------------
    # GEOMETRIC ALIGNMENT GRAPHICS MATH CORRECTIONS
    # -------------------------------------------------------------

    def reposition_splash_hud(self):
        """THE GEOMETRY FIX: Uses parent context boundaries to center perfectly."""
        canvas = self.lbl_splash_hud.parentWidget()
        if canvas:
            self.lbl_splash_hud.adjustSize()

            # Calculate centering math inside its true container parent coordinates
            cx = (canvas.width() - self.lbl_splash_hud.width()) // 2
            cy = (canvas.height() - self.lbl_splash_hud.height()) // 2

            # Bound height y-axis placement rules to prevent tucking under top toolbars
            self.lbl_splash_hud.move(cx, max(50, cy))

    # -------------------------------------------------------------
    # MOUSE INTERACTION ROUTERS (Prevents Cluttering Viewport Canvas)
    # -------------------------------------------------------------

    def hide_overlays_on_mouse_press(self):
        """Clears overlay cards out of sight instantly during active rectangle draws."""
        self.lbl_commands_overlay.hide()
        self.lbl_telemetry_hud.hide()

    def restore_overlays_on_mouse_release(self):
        """Restores shortcut and telemetry visibility smoothly once clicks release."""

        if self.main_app.image_session.has_active_image:
            if self.main_app.cfg_show_shortcuts.isChecked():
                self.lbl_commands_overlay.show()
                self.lbl_commands_overlay.raise_()

            if not self.main_app.cfg_show_infobar.isChecked():
                self.lbl_telemetry_hud.show()
                self.lbl_telemetry_hud.raise_()

        self.invalidate_ui_state()

    def sync_drawer_visibility_rules(self):
        """Handles drawer checkbox toggles instantly across fixed and floating items."""
        # 1. Shortcuts Checkbox
        if (
            self.main_app.cfg_show_shortcuts.isChecked()
            and self.main_app.image_session.has_active_image
        ):
            self.lbl_commands_overlay.show()
            self.lbl_commands_overlay.raise_()
        else:
            self.lbl_commands_overlay.hide()

        #  Check the live checkbox widget state instead of the static dataclass property!
        if self.main_app.cfg_show_infobar.isChecked():
            if (
                self.main_app.cfg_show_imgsize.isChecked()
                or self.main_app.cfg_show_filename.isChecked()
                or self.main_app.cfg_show_directory.isChecked()
            ):
                self.info_bar.show()
            else:
                self.info_bar.hide()
        else:
            self.info_bar.hide()

        # Force the main structural layout container to update its dimensions

        self.main_app.central_widget.layout().activate()

        # Instead of running heavy text distributions instantly,
        # mark it as dirty so the 60FPS heart-rate timer repaints it perfectly aligned!
        self.invalidate_ui_state()

        # Refresh the primary canvas rendering pass
        self.main_app.refresh_display_canvas()

    # -------------------------------------------------------------
    # GEOMETRIC ALIGNMENT GRAPHICS MATH
    # -------------------------------------------------------------

    def reposition_center_notification(self):
        canvas = self.lbl_notification.parentWidget()
        if canvas:
            x = (canvas.width() - self.lbl_notification.width()) // 2
            y = (canvas.height() - self.lbl_notification.height()) // 2
            self.lbl_notification.move(x, y)

    def reposition_commands_overlay(self):
        self.lbl_commands_overlay.adjustSize()
        padding = 15
        self.lbl_commands_overlay.move(padding, padding)

    def reposition_telemetry_hud(self):
        """Uses parent canvas container metrics to position perfectly."""
        # 1. Grab its true immediate drawing canvas wrapper container
        canvas = self.lbl_telemetry_hud.parentWidget()
        if canvas:
            # Force the label layout engine to compute its true text text bounding box length first
            self.lbl_telemetry_hud.adjustSize()
            padding = 15
            x = padding
            # 2. Calculate the height constraints using the canvas container's height instead of central_widget!
            y = canvas.height() - self.lbl_telemetry_hud.height() - padding
            # Snap the floating card smoothly to its perfect bottom-left boundary position
            self.lbl_telemetry_hud.move(x, y)

    def reposition_all_overlays(self):
        """Fires inside main app resizeEvents to prevent layout drift."""
        if self.lbl_notification.isVisible():
            self.reposition_center_notification()
        if self.lbl_splash_hud.isVisible():
            self.reposition_splash_hud()
        if self.lbl_commands_overlay.isVisible():
            self.reposition_commands_overlay()
        if self.lbl_telemetry_hud.isVisible():
            self.reposition_telemetry_hud()

    def update_status_and_telemetry(self):
        """Synchronize the status bar and floating HUD text labels based on configuration."""
        # 1. Guard Clause: Fast fallback to baseline empty state
        if not self.main_app.image_session.has_active_image:
            self.set_empty_workspace_state()
            return

        self.lbl_splash_hud.hide()

        # 2. Extract Data Aggregation Phase
        dir_str = self._compile_directory_string()
        file_str = self._compile_filename_string()
        metrics_str = self._compile_metrics_string()

        # 3. Separate Execution Pathways (Pipeline A vs Pipeline B)
        if self.main_app.cfg_show_infobar.isChecked():
            self._update_infobar_pipeline(dir_str, file_str, metrics_str)
        else:
            self._update_floating_hud_pipeline(dir_str, file_str, metrics_str)

    # --- Extracted Helper Methods ---

    def _compile_directory_string(self) -> str:
        """Evaluates session metrics and structural config flags to frame active directory strings."""
        if (
            self.main_app.cfg_show_directory.isChecked()
            and self.main_app.image_session.has_active_image
        ):
            return f"Directory: {self.main_app.image_session.folder_path.name}"
        return ""

    def _compile_filename_string(self) -> str:
        """Evaluates tracking parameters and checkboxes to generate structural file headings."""
        if (
            self.main_app.cfg_show_filename.isChecked()
            and self.main_app.image_session.has_active_image
        ):
            idx_str = self.main_app.image_session.index_string
            current_path = self.main_app.image_session.current_path
            return f"{idx_str} {current_path.name}"
        return ""

    def _compile_metrics_string(self) -> str:
        """Compiles physical pixel coordinates and configuration markers cleanly."""
        if (
            self.main_app.cfg_show_imgsize.isChecked()
            and self.main_app.image_session.has_active_image
        ):
            src_w = self.main_app.image_session.width
            src_h = self.main_app.image_session.height
            return f"IMG: {src_w}x{src_h}"
        return ""

    def _update_infobar_pipeline(self, dir_str: str, file_str: str, metrics_str: str):
        """PIPELINE A: Populates the integrated infobar widgets and completely masks floating text."""
        self.lbl_telemetry_hud.hide()

        # Fast inline ternary mapping reduces complex multi-line nested if visibility sets
        self.info_bar.lbl_directory.setText(dir_str)
        self.info_bar.lbl_directory.setVisible(bool(dir_str))

        self.info_bar.lbl_status.setText(file_str)
        self.info_bar.lbl_status.setVisible(bool(file_str))

        self.info_bar.lbl_metrics.setText(metrics_str)
        self.info_bar.lbl_metrics.setVisible(bool(metrics_str))

    def _update_floating_hud_pipeline(
        self, dir_str: str, file_str: str, metrics_str: str
    ):
        """PIPELINE B: Flushes inline status bars and routes strings to floating overlay panels."""
        # Reset embedded widgets seamlessly
        self.info_bar.lbl_directory.setText("")
        self.info_bar.lbl_status.setText("")
        self.info_bar.lbl_metrics.setText("")

        # Determine user mouse interactions state dynamically
        sm = self.main_app.selection_manager
        is_user_actively_editing = sm.is_moving_box or not sm.drag_start_origin.isNull()

        # Filter out empty entries automatically
        hud_lines = [text for text in (file_str, metrics_str, dir_str) if text]

        if hud_lines and not is_user_actively_editing:
            self.lbl_telemetry_hud.setText("\n".join(hud_lines))
            self.lbl_telemetry_hud.show()
            self.lbl_telemetry_hud.raise_()
            self.reposition_telemetry_hud()
        else:
            self.lbl_telemetry_hud.hide()
