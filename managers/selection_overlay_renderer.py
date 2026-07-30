# =============================================================================
# SelectionOverlayRenderer -- turns the flat "draw a rectangle" crop-box look
# into an inverse ("spotlight") selection: the picked region stays sharp,
# everything else is blurred/dimmed. This module owns ONLY the compositing
# math (blur + cutout). It never touches mouse events, QRubberBand state, or
# CropModel -- it's handed a rect (already computed the same way every other
# screen<->source conversion in this app is) and a base pixmap, and returns
# the pixmap that should be shown.
# =============================================================================
from __future__ import annotations

from PyQt6.QtCore import QRect, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QGraphicsBlurEffect, QGraphicsPixmapItem, QGraphicsScene

# Tunables -- move to config/ui_constants.py if these should be user-facing.
BLUR_RADIUS = 4.0
DIM_OVERLAY_ALPHA = 145  # extra darkening over the blurred area, 0-255, 0 disables it
SELECTION_BORDER_COLOR = QColor(255, 255, 255, 235)
SELECTION_BORDER_WIDTH = 1


def _blur_pixmap(source: QPixmap, radius: float) -> QPixmap:
    """Bakes a QGraphicsBlurEffect onto a QPixmap. QGraphicsBlurEffect can only
    be applied to a QGraphicsItem, so we render a throwaway scene containing
    just this one pixmap item into a fresh QPixmap of the same size. This runs
    once per canvas refresh (image load/resize/rotate) -- never per mouse-move."""
    if source is None or source.isNull():
        return source

    scene = QGraphicsScene()
    item = QGraphicsPixmapItem(source)
    effect = QGraphicsBlurEffect()
    effect.setBlurRadius(radius)
    effect.setBlurHints(QGraphicsBlurEffect.BlurHint.QualityHint)
    item.setGraphicsEffect(effect)
    scene.addItem(item)

    result = QPixmap(source.size())
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    scene.render(painter, QRectF(result.rect()), QRectF(source.rect()))
    painter.end()
    return result


class SelectionOverlayRenderer:
    """Caches a sharp/blurred pair for the currently displayed canvas pixmap
    and composites them against a selection rect on demand."""

    def __init__(self, selection_manager=None, blur_radius: float = BLUR_RADIUS):
        self._blur_radius = blur_radius
        self._sharp: QPixmap | None = None
        self._blurred: QPixmap | None = None
        self.selection_manager = selection_manager

    def set_base_pixmap(self, pixmap: QPixmap | None) -> None:
        """Call whenever the underlying canvas image changes: new image
        loaded, window resized, rotation applied. Recomputing the blur is the
        only non-trivial cost in this class, so it's isolated here instead of
        running on every selection update."""
        self._sharp = pixmap
        self._blurred = (
            _blur_pixmap(pixmap, self._blur_radius)
            if pixmap is not None and not pixmap.isNull()
            else None
        )

    # 🚀 FIXED: We add `selection_manager=None` directly to the method parameters
    def render(self, selection_rect_in_pixmap_space: QRect | None) -> QPixmap | None:
        """Returns the pixmap that should be shown on the canvas label.
        `selection_rect_in_pixmap_space` must already be translated into the
        base pixmap's own (0,0)-origin coordinate space -- i.e. with the
        label's centering offset subtracted out, exactly like every other
        screen<->source conversion in this app. Pass None (or an empty rect)
        to get the plain sharp image back, unchanged."""
        if self._sharp is None:
            return None

        if (
            selection_rect_in_pixmap_space is None
            or selection_rect_in_pixmap_space.isEmpty()
        ):
            return self._sharp

        clipped = selection_rect_in_pixmap_space.intersected(self._sharp.rect())
        if clipped.isEmpty():
            return self._sharp

        composite = QPixmap(self._sharp.size())
        composite.fill(Qt.GlobalColor.transparent)

        painter = QPainter(composite)
        painter.drawPixmap(
            0, 0, self._blurred if self._blurred is not None else self._sharp
        )

        if DIM_OVERLAY_ALPHA:
            painter.fillRect(composite.rect(), QColor(0, 0, 0, DIM_OVERLAY_ALPHA))

        painter.setClipRect(clipped)
        painter.drawPixmap(0, 0, self._sharp)
        painter.setClipping(False)

        # -----------------------------------------------------------------
        # 🚀 PART A: PREDICTIVE DUAL-BOX SNAP FEEDBACK LAYER
        # -----------------------------------------------------------------
        # Use the passed manager directly instead of guessing with __main__
        mgr = self.selection_manager

        if mgr is not None:
            ghost_geom = getattr(mgr, "ghost_crop_geometry", None)

            # If ghosting coordinates are active, map them to pixmap space and paint them
            if ghost_geom and not ghost_geom.isEmpty():
                # Extract the centering labels offset matrix parameters natively
                lbl_w, lbl_h = mgr.canvas.width(), mgr.canvas.height()
                pix_w, pix_h = self._sharp.width(), self._sharp.height()
                ox, oy = (lbl_w - pix_w) // 2, (lbl_h - pix_h) // 2

                # Project the screen coordinates directly into raw pixmap space bounds
                ghost_clipped = ghost_geom.translated(-ox, -oy).intersected(
                    self._sharp.rect()
                )

                if not ghost_clipped.isEmpty():
                    # Draw a subtle, professional dashed neon-teal frame showing the snap landing
                    snap_pen = QPen(QColor(0, 243, 255, 130), 1, Qt.PenStyle.DashLine)
                    painter.setPen(snap_pen)
                    painter.drawRect(ghost_clipped.adjusted(0, 0, -1, -1))

        # -----------------------------------------------------------------
        # 🚀 PART B: ASYMMETRIC GRADIENT CROP BRACKETS (Fluid Mouse Position)
        # -----------------------------------------------------------------
        from PyQt6.QtGui import QBrush, QLinearGradient

        r = clipped  # The active selection bounding box reference matrix

        # Map out a diagonal gradient line spanning from top-left to bottom-right
        gradient = QLinearGradient(r.left(), r.top(), r.right(), r.bottom())

        # Configure the color stops to match your app icon layout perfectly
        gradient.setColorAt(0.0, QColor(255, 255, 255, 240))  # Brilliant white at start
        gradient.setColorAt(0.5, QColor(140, 235, 255, 200))  # Ice-blue color in middle
        gradient.setColorAt(1.0, QColor(0, 243, 255, 255))  # Electric teal at end

        gradient_brush = QBrush(gradient)
        thick_pen = QPen(gradient_brush, 2, Qt.PenStyle.SolidLine)
        thin_pen = QPen(gradient_brush, 1, Qt.PenStyle.SolidLine)

        overflow = 12  # How many pixels lines shoot outward past the corner
        length = 24  # The total length of each bracket arm

        # --- 1. OVERFLOWING CORNERS (Top-Left and Bottom-Right: Uses THICK pen) ---
        painter.setPen(thick_pen)

        # Top-Left Corner
        painter.drawLine(
            r.left() - overflow, r.top(), r.left() + (length - overflow), r.top()
        )
        painter.drawLine(
            r.left(), r.top() - overflow, r.left(), r.top() + (length - overflow)
        )

        # Bottom-Right Corner
        painter.drawLine(
            r.right() + overflow,
            r.bottom(),
            r.right() - (length - overflow),
            r.bottom(),
        )
        painter.drawLine(
            r.right(),
            r.bottom() + overflow,
            r.right(),
            r.bottom() - (length - overflow),
        )

        # --- 2. CLEAN CLOSED CORNERS (Top-Right and Bottom-Left: Uses THIN pen) ---
        painter.setPen(thin_pen)

        # Top-Right Corner
        painter.drawLine(r.right(), r.top(), r.right() - length, r.top())
        painter.drawLine(r.right(), r.top(), r.right(), r.top() + length)

        # Bottom-Left Corner
        painter.drawLine(r.left(), r.bottom(), r.left() + length, r.bottom())
        painter.drawLine(r.left(), r.bottom(), r.left(), r.bottom() - length)
        # -----------------------------------------------------------------

        painter.end()
        return composite
