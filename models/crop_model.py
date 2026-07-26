from __future__ import annotations

from PyQt6.QtCore import QObject, QRect, pyqtSignal


class CropModel(QObject):
    """Owns the active crop selection in SOURCE PIXEL SPACE — never screen or
    widget coordinates. This is the piece your architecture doc calls for but
    that doesn't exist yet: right now selection state lives inside
    SelectionManager next to the QRubberBand it draws, which mixes view state
    and model state in one object.

    Rule enforced by this class: it never imports anything from widgets/ and
    never touches a QLabel/QRubberBand. Screen<->source conversion stays in
    your existing CropGeometryEngine / ViewportGeometry, which is exactly
    where that view-dependent math belongs. SelectionManager should become a
    thin controller: it converts mouse events to source-space rects, calls
    crop_model.set_rect(...), and repositions the QRubberBand only in
    response to crop_model.selection_changed — it should stop being the
    source of truth itself.
    """

    selection_changed = pyqtSignal(QRect)  # emits the new source_pixel_rect
    selection_cleared = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._source_pixel_rect = QRect()

    # -- read-only state ---------------------------------------------------
    @property
    def source_pixel_rect(self) -> QRect:
        """Defensive copy — callers can't mutate our internal QRect by
        reference and silently desync us from our own signal."""
        return QRect(self._source_pixel_rect)

    @property
    def has_selection(self) -> bool:
        return not self._source_pixel_rect.isEmpty()

    # -- mutators ------------------------------------------------------------
    def set_rect(self, rect: QRect) -> None:
        """Called by SelectionManager at every commit point — end of a drag,
        a move, a snap, a spinbox-driven resize, a restored selection.
        Always source-pixel space; SelectionManager is responsible for the
        screen<->source conversion before calling this."""
        if rect == self._source_pixel_rect:
            return
        self._source_pixel_rect = QRect(rect)
        self.selection_changed.emit(self.source_pixel_rect)

    def clear(self) -> None:
        if self._source_pixel_rect.isNull():
            return
        self._source_pixel_rect = QRect()
        self.selection_cleared.emit()

    def clamp_to_bounds(self, max_width: int, max_height: int) -> None:
        """The re-clamp step from the Sync Chain: called by ImageSession when
        CropSettings.keep_selection_on_swap_enabled is True and a new file
        just loaded with different dimensions than the old one."""
        if self._source_pixel_rect.isNull():
            return

        r = self._source_pixel_rect
        left = max(0, min(max_width, r.x()))
        top = max(0, min(max_height, r.y()))
        right = max(0, min(max_width, r.x() + r.width()))
        bottom = max(0, min(max_height, r.y() + r.height()))
        clamped = QRect(left, top, right - left, bottom - top)

        if clamped.width() <= 0 or clamped.height() <= 0:
            self.clear()
        else:
            self.set_rect(clamped)

    # NOTE: no apply_target_dimensions() here. Turning a target width/height
    # into an on-screen QRubberBand geometry needs the pixmap's screen-space
    # scale factors (see SelectionManager.apply_target_dimensions) — that's
    # legitimately view/controller math, not something this model should
    # duplicate. SelectionManager keeps owning that computation and pushes
    # the *result*, in source-pixel space, into this model via set_rect()
    # the same way every other interaction does.
