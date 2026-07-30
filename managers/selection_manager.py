# =============================================================================
# SelectionManager — owns crop-box / ghost-box QRubberBand state and every
# mouse- or spinbox-driven selection edit (draw, move, snap, resize).
# All screen<->source pixel math is delegated to CropGeometryEngine so this
# class stays a state machine, not a second copy of the transform logic.
#
# CHANGE FROM ORIGINAL: this class is no longer the source of truth for the
# selection. It's still the ONLY thing that touches self.selector /
# self.ghost_selector directly (that part didn't change), but the committed
# selection — the thing crop execution, spinbox sync, and image-swap
# preservation actually care about — now lives in CropModel, in source-pixel
# space. This class's job becomes: convert mouse/spinbox input into screen
# geometry (still exactly the same math as before), and push the resulting
# source-pixel rect into CropModel at every commit point.
# =============================================================================
from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import QPoint, QRect, QSize
from PyQt6.QtWidgets import QLabel, QRubberBand, QWidget

from config import ui_constants
from managers.crop_geometry_engine import CropGeometryEngine, ViewportGeometry
from models.crop_model import CropModel


@dataclass(frozen=True)
class _ScreenCommitContext:
    """Snapshot of the screen-space state a width/height was last committed
    to CropModel against: the selector's screen size, and the viewport it
    was measured under. As long as both stay identical, the box's SIZE
    hasn't actually changed — only its position might have — so
    re-deriving width/height from the screen would just re-run the same
    lossy round() a previous commit already went through, discarding
    whatever extra precision the model currently holds (e.g. an exact
    spinbox entry)."""

    screen_size: QSize
    viewport: ViewportGeometry

    def matches(self, screen_size: QSize, viewport: "ViewportGeometry | None") -> bool:
        return (
            viewport is not None
            and screen_size == self.screen_size
            and viewport == self.viewport
        )


class SelectionManager:
    """State owner for the crop rubber-band and its optional ghost overlay.

    LossLessCropApp still constructs and parents the QRubberBand widgets (that's
    a layout concern), but hands them here and from then on only calls into
    this class to mutate selection geometry. Nothing outside SelectionManager
    should call .setGeometry()/.show()/.hide() on `selector` or
    `ghost_selector` after construction.
    """

    def __init__(
        self,
        canvas: QLabel,
        selector: QRubberBand,
        ghost_parent: QWidget,
        image_session,
        crop_model: CropModel,
        ratio_combo,
        snap_combo,
        viewport_factory: Callable[[object], ViewportGeometry],
        lossless_check: Callable[[], bool],
        on_selection_changed: Callable[[], None] | None = None,
    ):
        self.canvas = canvas
        self.selector = selector
        self._ghost_parent = ghost_parent
        self.image_session = image_session
        self.crop_model = crop_model
        self.ratio_combo = ratio_combo
        self.snap_combo = snap_combo
        self._viewport_factory = viewport_factory
        self._lossless_check = lossless_check
        self._on_selection_changed = on_selection_changed

        self.ghost_selector: QRubberBand | None = None
        self.last_crop_geometry: QRect | None = None
        self.drag_start_origin = QPoint()
        self.is_moving_box = False
        self.box_start_pos = QPoint()
        self._commit_context: _ScreenCommitContext | None = None

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------
    def _current_ratio_label(self) -> str:
        return self.ratio_combo.currentText()

    def _current_viewport(self) -> ViewportGeometry | None:
        pixmap = self.canvas.pixmap()
        if not pixmap:
            return None
        return self._viewport_factory(pixmap)

    def _ensure_ghost_selector(self) -> QRubberBand:
        if self.ghost_selector is None:
            self.ghost_selector = QRubberBand(
                QRubberBand.Shape.Rectangle, self._ghost_parent
            )
            self.ghost_selector.setStyleSheet(
                "background-color: rgba(255, 165, 0, 30); border: 1px dashed orange;"
            )
        return self.ghost_selector

    def hide_ghost(self):
        if self.ghost_selector is not None:
            self.ghost_selector.hide()

    def _snap_rect(self, screen_rect: QRect) -> QRect:
        viewport = self._current_viewport()
        if viewport is None:
            return screen_rect
        return CropGeometryEngine.snap_screen_rect_to_grid(
            screen_rect,
            viewport,
            lossless=self._lossless_check(),
            ratio_label=self._current_ratio_label(),
        )

    def _notify_changed(self):
        """Every code path that changes the on-screen selector ends here.
        This is the single commit point into CropModel."""
        if self.selector.isHidden():
            self.crop_model.clear()
            self._commit_context = None
        else:
            viewport = self._current_viewport()
            current_size = self.selector.geometry().size()

            if (
                self.crop_model.has_selection
                and self._commit_context is not None
                and self._commit_context.matches(current_size, viewport)
            ):
                # Box hasn't been resized since the last commit -- only
                # moved. Keep the committed width/height exactly, only
                # re-project position.
                existing = self.crop_model.source_pixel_rect
                projected = CropGeometryEngine.screen_rect_to_source_rect(
                    self.selector.geometry(),
                    viewport,
                    lossless=self._lossless_check(),
                    ratio_label=self._current_ratio_label(),
                )
                self.crop_model.set_rect(
                    QRect(
                        projected.x(),
                        projected.y(),
                        existing.width(),
                        existing.height(),
                    )
                )
            else:
                source_rect = self.current_source_rect()
                if source_rect is not None:
                    self.crop_model.set_rect(source_rect)
                    self._commit_context = _ScreenCommitContext(current_size, viewport)

        if self._on_selection_changed:
            self._on_selection_changed()

    # -----------------------------------------------------------------
    # Mouse-press entry points (called from LossLessCropApp.on_mouse_press)
    # -----------------------------------------------------------------
    def begin_draw(self, start_point: QPoint):
        """Left-click press: start a fresh rubber-band draw."""
        self.drag_start_origin = start_point
        self.selector.setGeometry(QRect(start_point, QSize()))
        self.selector.show()
        self.is_moving_box = False

    def begin_move(self, click_point: QPoint) -> bool:
        """Right-click press: start a move IF click_point lands inside the
        current box. Returns whether a move actually started, so the caller
        can branch its cursor/side-effect logic the same way the old
        on_mouse_press did.
        """
        if self.selector.isHidden() or not self.selector.geometry().contains(
            click_point
        ):
            self.is_moving_box = False
            return False

        self.is_moving_box = True
        self.drag_start_origin = click_point
        self.box_start_pos = self.selector.geometry().topLeft()
        return True

    # -----------------------------------------------------------------
    # Mouse-move entry points (called from LossLessCropApp.on_mouse_move)
    # -----------------------------------------------------------------
    def update_move(self, current_point: QPoint):
        """Right-click drag: slide the box, clamped to canvas bounds, then
        re-snap it if lossless is active."""
        if self.drag_start_origin.isNull():
            return

        total_delta = current_point - self.drag_start_origin
        current_geometry = self.selector.geometry()

        target_x = self.box_start_pos.x() + total_delta.x()
        target_y = self.box_start_pos.y() + total_delta.y()

        target_x = max(0, min(target_x, self.canvas.width() - current_geometry.width()))
        target_y = max(
            0, min(target_y, self.canvas.height() - current_geometry.height())
        )

        self.selector.move(target_x, target_y)
        self.last_crop_geometry = self.selector.geometry()

        self.snap_selection()  # no-op in pixel-perfect mode; calls _notify_changed
        self._notify_changed()

    def update_draw(self, current_screen_pos: QPoint) -> QRect | None:
        """Left-click drag: grow/shrink the box from drag_start_origin,
        honoring aspect lock and the active snap mode. Returns the current
        selection projected into source-pixel space (so the caller can push
        it straight into the width/height spinboxes), or None if there's no
        active drag or pixmap to draw against.
        """
        if self.drag_start_origin.isNull() or not self.image_session.has_active_image:
            return None

        pixmap = self.canvas.pixmap()
        if not pixmap:
            return None

        lbl_w, lbl_h = self.canvas.width(), self.canvas.height()
        pix_w, pix_h = pixmap.width(), pixmap.height()
        offset_x, offset_y = (lbl_w - pix_w) // 2, (lbl_h - pix_h) // 2
        viewport = self._viewport_factory(pixmap)

        x1, y1 = self.drag_start_origin.x(), self.drag_start_origin.y()
        x2 = max(offset_x, min(current_screen_pos.x(), offset_x + pix_w))
        y2 = max(offset_y, min(current_screen_pos.y(), offset_y + pix_h))

        raw_w = x2 - x1
        raw_h = y2 - y1

        ratio_label = self._current_ratio_label()
        aspect = CropGeometryEngine.resolve_aspect_ratio(
            ratio_label, (viewport.source_width, viewport.source_height)
        )

        if aspect is not None:
            sign_w = 1 if raw_w >= 0 else -1
            sign_h = 1 if raw_h >= 0 else -1

            # 🚀 THE DOMINANT AXIS CORRECTION:
            # Check if the vertical movement is greater than the horizontal movement
            if abs(raw_h) * aspect > abs(raw_w):
                # Vertical drag is dominant: calculate width (raw_w) from height (raw_h)
                raw_w = sign_w * abs(int(raw_h * aspect))
            else:
                # Horizontal drag is dominant: calculate height (raw_h) from width (raw_w)
                raw_h = sign_h * abs(int(raw_w / aspect))

            # Strictly maintain your original safety boundaries against image edges
            if y1 + raw_h < offset_y:
                raw_h = offset_y - y1
                raw_w = sign_w * abs(int(raw_h * aspect))
            elif y1 + raw_h > offset_y + pix_h:
                raw_h = (offset_y + pix_h) - y1
                raw_w = sign_w * abs(int(raw_h * aspect))

        fluid_rect = QRect(x1, y1, raw_w, raw_h).normalized()
        snap_mode = self.snap_combo.currentText()
        use_lossless = self._lossless_check()

        snapped_rect = self._snap_rect(fluid_rect) if use_lossless else fluid_rect

        if snap_mode == ui_constants.SNAP_REAL_TIME:
            self.hide_ghost()
            active_rect = snapped_rect if use_lossless else fluid_rect
            self.selector.setGeometry(active_rect)
            self.last_crop_geometry = active_rect
            self.selector.show()
            self.selector.raise_()

        elif snap_mode == ui_constants.SNAP_POST_RELEASE:
            self.hide_ghost()
            self.selector.setGeometry(fluid_rect)
            self.selector.show()
            self.selector.raise_()
            self.last_crop_geometry = fluid_rect

        elif snap_mode == ui_constants.SNAP_GHOSTING:
            ghost = self._ensure_ghost_selector()
            self.selector.setGeometry(fluid_rect)
            self.selector.show()
            self.selector.raise_()
            self.last_crop_geometry = fluid_rect

            if use_lossless:
                ghost.setGeometry(snapped_rect)
                ghost.show()
                ghost.raise_()
            else:
                ghost.hide()

        self._notify_changed()

        # source_rect derivation mirrors calculate_snapped_rect /
        # update_resolution_metrics_display exactly, so all three stay in sync.
        return CropGeometryEngine.screen_rect_to_source_rect(
            snapped_rect if use_lossless else fluid_rect,
            viewport,
            lossless=use_lossless,
            ratio_label=ratio_label,
        )

    # -----------------------------------------------------------------
    # Mouse-release entry point (called from LossLessCropApp.on_mouse_release)
    # -----------------------------------------------------------------
    def finalize_draw(self):
        """Left-click release: apply the final snap per the active snap mode
        and clear drag tracking."""
        if self.drag_start_origin.isNull() or not self.last_crop_geometry:
            return

        snap_mode = self.snap_combo.currentText()

        if snap_mode in (ui_constants.SNAP_POST_RELEASE, ui_constants.SNAP_REAL_TIME):
            self.snap_selection()
        elif snap_mode == ui_constants.SNAP_GHOSTING:
            self.hide_ghost()
            snapped_rect = self._snap_rect(self.selector.geometry())
            self.selector.setGeometry(snapped_rect)
            self.last_crop_geometry = snapped_rect

        self.drag_start_origin = QPoint()
        self._notify_changed()

    def end_move(self):
        """Right-click release: just clears drag tracking (mirrors the old
        inline reset in on_mouse_release)."""
        self.is_moving_box = False
        self.drag_start_origin = QPoint()

    # -----------------------------------------------------------------
    # Shared snap primitive (was snap_selector_widget / calculate_snapped_rect)
    # -----------------------------------------------------------------
    def snap_selection(self):
        """Snaps the live selector to the grid if lossless is active.
        Idempotent no-op in pixel-perfect mode or while the selector is
        hidden. Used directly on aspect-ratio/engine-toggle changes, and
        internally after moves/releases."""
        if self.selector.isHidden():
            return
        if self._lossless_check():
            snapped = self._snap_rect(self.selector.geometry())
            self.selector.setGeometry(snapped)
            self.last_crop_geometry = snapped
        self._notify_changed()

    # -----------------------------------------------------------------
    # Spinbox-driven resize (was apply_spinbox_dimensions_to_canvas)
    # -----------------------------------------------------------------
    def apply_target_dimensions(
        self, target_w: int, target_h: int
    ) -> tuple[int, int, bool]:
        """Resizes/positions the selector to match spinbox-driven target
        source-pixel dimensions. Grid-snaps the target first when lossless
        is active. Returns (final_w, final_h, applied):
          - final_w/final_h are the (possibly snapped) target values — the
            caller pushes these back into the spinboxes itself.
          - applied is False when there's no active pixmap, or the target
            is too small to draw (selector gets hidden in that case).

        This stays here rather than moving onto CropModel because it needs
        the pixmap's on-screen scale factors (sx, sy below) — that's
        screen-space math CropModel deliberately doesn't know about. The
        *result* still goes through the normal _notify_changed() commit path.
        """
        pixmap = self.canvas.pixmap()
        if not self.image_session.has_active_image or not pixmap:
            return target_w, target_h, False

        src_w, src_h = self.image_session.width, self.image_session.height
        tw = min(target_w, src_w)
        th = min(target_h, src_h)

        if self._lossless_check():
            tw = CropGeometryEngine.snap_to_grid(tw)
            th = CropGeometryEngine.snap_to_grid(th)

        if tw <= 10 or th <= 10:
            self.selector.hide()
            self._notify_changed()
            return tw, th, False

        lw, lh = self.canvas.width(), self.canvas.height()
        pw, ph = pixmap.width(), pixmap.height()
        ox, oy = (lw - pw) // 2, (lh - ph) // 2
        sx, sy = pw / src_w, ph / src_h
        bw, bh = round(tw * sx), round(th * sy)

        if not self.selector.isHidden():
            geom = self.selector.geometry()
            bw = min(bw, pw - (geom.x() - ox))
            bh = min(bh, ph - (geom.y() - oy))
            self.selector.setGeometry(geom.x(), geom.y(), bw, bh)
        else:
            bx, by = ox + (pw - bw) // 2, oy + (ph - bh) // 2
            self.selector.setGeometry(bx, by, bw, bh)
            self.selector.show()

        self.last_crop_geometry = self.selector.geometry()

        # Commit tw/th to the model exactly as requested, instead of
        # letting _notify_changed() re-derive them from this box's
        # just-quantized screen size — that round trip isn't idempotent,
        # so it would silently replace the requested value with an
        # off-by-a-few-pixel one even in Pixel-Perfect mode.
        viewport = self._current_viewport()
        if viewport is not None:
            projected = CropGeometryEngine.screen_rect_to_source_rect(
                self.selector.geometry(),
                viewport,
                lossless=self._lossless_check(),
                ratio_label=self._current_ratio_label(),
            )
            self.crop_model.set_rect(QRect(projected.x(), projected.y(), tw, th))
            self._commit_context = _ScreenCommitContext(
                self.selector.geometry().size(), viewport
            )

        if self._on_selection_changed:
            self._on_selection_changed()

        return tw, th, True

    # -----------------------------------------------------------------
    # Read-only projection (usable by update_resolution_metrics_display)
    # -----------------------------------------------------------------
    def current_source_rect(self) -> QRect | None:
        """Projects the live selector geometry into source-pixel space.
        Returns None if there's nothing to project (hidden selector or no
        pixmap). Internal use is now mostly limited to _notify_changed();
        external callers (crop execution, spinbox sync) should prefer
        image_session.crop_model.source_pixel_rect, which is the same value
        already committed and doesn't re-derive from widget geometry."""
        if self.selector.isHidden():
            return None
        viewport = self._current_viewport()
        if viewport is None:
            return None
        return CropGeometryEngine.screen_rect_to_source_rect(
            self.selector.geometry(),
            viewport,
            lossless=self._lossless_check(),
            ratio_label=self._current_ratio_label(),
        )

    # -----------------------------------------------------------------
    # Model -> view sync after a crop or an image swap (replaces
    # restore_preserved_geometry as the thing LossLessCropApp calls)
    # -----------------------------------------------------------------
    def sync_view_from_model(self) -> None:
        """Called by LossLessCropApp right after refresh_display_canvas() — on
        every folder navigation, every crop (overwrite or not), any time
        the canvas just repainted. crop_model.has_selection tells us
        whether the box should still be showing at all (ImageSession's
        Sync Chain, or apply_post_crop_selection_policy(), already made
        that keep-vs-clear call) — but this method does NOT move or resize
        the selector to match crop_model's stored coordinates.

        That reprojection is exactly what caused a visible drift: it went
        crop_model.source_pixel_rect -> screen_rect via
        CropGeometryEngine.source_rect_to_screen_rect(), the reverse of the
        screen_rect_to_source_rect() call that produced source_pixel_rect
        in the first place. Those two directions aren't a clean inverse
        (the forward call takes a lossless flag; the reverse one doesn't),
        and each direction rounds to integer pixels — so on EVERY crop,
        not just ones that swap images, the box could shift by a pixel or
        two. Lossless mode never showed it because every touch of the box
        already re-snaps to the 8x8 grid, which happens to swallow that
        error; Pixel-Perfect has no snap, so the drift was the first thing
        visible.

        The actual invariant, matching the original app, is the screen
        rect — so this leaves the selector's geometry completely alone and
        instead refreshes crop_model FROM it, against the current
        viewport, via the same _notify_changed() path every other
        interaction uses. That's a one-way, idempotent refresh: if the
        viewport hasn't changed (a plain crop, no swap), it recomputes the
        exact same numbers and nothing visibly moves; if the viewport HAS
        changed (navigation, or an overwrite-crop reload), crop_model ends
        up correctly describing where the untouched screen box now sits
        relative to whatever image is currently displayed.
        """
        if not self.crop_model.has_selection:
            self.clear_selection()
            return

        if self._current_viewport() is None:
            self.clear_selection()
            return

        self.selector.show()
        self.selector.raise_()

        if self._lossless_check():
            # Re-snap only — never reposition beyond the grid — so a
            # lossless-mode box stays grid-aligned if the engine toggle
            # changed while it was preserved. This branch never runs in
            # Pixel-Perfect mode, which is exactly why that mode is (and
            # should be) pixel-identical across a preserved selection.
            snapped = self._snap_rect(self.selector.geometry())
            self.selector.setGeometry(snapped)

        self.last_crop_geometry = self.selector.geometry()
        if self._current_ratio_label() == ui_constants.RATIO_SOURCE:
            # Source Ratio's meaning is per-image. Lossless mode already
            # reshaped above via the grid re-snap (which re-derives height from
            # the live aspect); Pixel-Perfect mode leaves geometry untouched by
            # design, so force the same reshape apply_ratio_to_selector_widget()
            # already does for manual ratio-combo changes.
            self.apply_ratio_to_selector_widget()

        self._notify_changed()  # refreshes crop_model FROM this geometry

    def clear_selection(self):
        """Hides both the selector and any ghost overlay, and drops the
        remembered geometry — mirrors the 'else' branch of
        sync_workspace_after_loading_image when preservation is off."""
        self.selector.hide()
        self.last_crop_geometry = None
        self.hide_ghost()
        self._notify_changed()  # NEW: previously this fell through silently;
        # now it's needed so crop_model.clear() actually fires.

    def detect_grip_zone(self, mouse_point: QPoint) -> int:
        """Evaluates cursor position and returns a matching grip type identifier."""
        rect = self.last_crop_geometry
        if not rect or rect.isEmpty():
            return 0  # No selection active, no grip zone possible

        x, y = mouse_point.x(), mouse_point.y()
        t = 12  # Grip touch hitbox radius in canvas pixels

        # Check Corners (Returns numeric identifiers 1 through 4)
        if abs(x - rect.left()) <= t and abs(y - rect.top()) <= t:
            return 1  # Top-Left
        if abs(x - rect.right()) <= t and abs(y - rect.top()) <= t:
            return 2  # Top-Right
        if abs(x - rect.left()) <= t and abs(y - rect.bottom()) <= t:
            return 3  # Bottom-Left
        if abs(x - rect.right()) <= t and abs(y - rect.bottom()) <= t:
            return 4  # Bottom-Right

        return 0

    def get_opposite_corner_anchor(self, grip_zone: int) -> QPoint | None:
        """Returns the exact diagonal corner point of the active crop rect to freeze as an anchor."""
        rect = self.last_crop_geometry
        if not rect or rect.isEmpty():
            return None

        # Map the grabbed corner to its static diagonal anchor point
        if grip_zone == 1:
            return QPoint(
                rect.right(), rect.bottom()
            )  # Grabbing Top-Left anchors Bottom-Right
        if grip_zone == 2:
            return QPoint(
                rect.left(), rect.bottom()
            )  # Grabbing Top-Right anchors Bottom-Left
        if grip_zone == 3:
            return QPoint(
                rect.right(), rect.top()
            )  # Grabbing Bottom-Left anchors Top-Right
        if grip_zone == 4:
            return QPoint(
                rect.left(), rect.top()
            )  # Grabbing Bottom-Right anchors Top-Left

        return None

    # -----------------------------------------------------------------
    # Aspect ratio update on pixel-perfect
    # -----------------------------------------------------------------

    def apply_ratio_to_selector_widget(self):
        """Forces the on-screen selection box to recalculate its dimensions
        when: A. combo aspect ratio change under Pixel-Perfect (Pillow) mode.
              B. Ratio Source is selected and changing image
        """
        if self.selector.isHidden() or self._lossless_check():
            return

        viewport = self._current_viewport()
        current_source = self.current_source_rect()

        if viewport and current_source:
            # 2. Re-project the current backend source coordinates back into screen coordinates
            direct_rect = CropGeometryEngine.source_rect_to_screen_rect(
                current_source, viewport, self._current_ratio_label()
            )

            # 3. Clamp and translate to match the physical UI layout boundaries
            clamped = CropGeometryEngine.clamp_screen_rect_to_pixmap(
                direct_rect, viewport
            )
            final_rect = clamped.translated(viewport.offset_x, viewport.offset_y)

            # 4. Apply geometry to force an instant layout repaint
            self.selector.setGeometry(final_rect)
            self.last_crop_geometry = final_rect
            self._notify_changed()
