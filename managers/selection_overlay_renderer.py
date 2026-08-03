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
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen, QPixmap
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

    def render(self, selection_rect_in_pixmap_space: QRect | None) -> QPixmap | None:
        """Returns the pixmap that should be shown on the canvas label."""
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

        # 1. Initialize composite canvas layers
        composite = QPixmap(self._sharp.size())
        composite.fill(Qt.GlobalColor.transparent)

        painter = QPainter(composite)

        # 2. Composition Pipeline
        self._paint_base_backdrop(painter)
        self._paint_sharp_clipped_selection(painter, clipped)
        self._paint_predictive_ghost_layer(painter)
        self._paint_asymmetric_gradient_brackets(painter, clipped)

        painter.end()
        return composite

    # --- Extracted Composition Steps ---

    def _paint_base_backdrop(self, painter: QPainter):
        """Draws the primary blurred or sharp background frame with dim overlay."""
        background = self._blurred if self._blurred is not None else self._sharp
        painter.drawPixmap(0, 0, background)

        if DIM_OVERLAY_ALPHA:
            painter.fillRect(self._sharp.rect(), QColor(0, 0, 0, DIM_OVERLAY_ALPHA))

    def _paint_sharp_clipped_selection(self, painter: QPainter, clipped: QRect):
        """Restores the original sharp image visibility within active bounding box."""
        painter.setClipRect(clipped)
        painter.drawPixmap(0, 0, self._sharp)
        painter.setClipping(False)

    def _paint_predictive_ghost_layer(self, painter: QPainter):
        """PART A: Projects and draws the neon-teal predictive snap bounds if active."""
        mgr = self.selection_manager
        if mgr is None:
            return

        ghost_geom = getattr(mgr, "ghost_crop_geometry", None)
        if not ghost_geom or ghost_geom.isEmpty():
            return

        # Extract centering label offset matrix parameters natively
        lbl_w, lbl_h = mgr.canvas.width(), mgr.canvas.height()
        pix_w, pix_h = self._sharp.width(), self._sharp.height()
        ox, oy = (lbl_w - pix_w) // 2, (lbl_h - pix_h) // 2

        # Project coordinates directly into raw pixmap space bounds
        ghost_clipped = ghost_geom.translated(-ox, -oy).intersected(self._sharp.rect())
        if ghost_clipped.isEmpty():
            return

        snap_pen = QPen(QColor(0, 243, 255, 130), 1, Qt.PenStyle.DashLine)
        painter.setPen(snap_pen)
        painter.drawRect(ghost_clipped.adjusted(0, 0, -1, -1))

    def _paint_asymmetric_gradient_brackets(self, painter: QPainter, clipped: QRect):
        """PART B: Creates and applies asymmetric corner crop boundaries."""
        # Build diagonal brush profile mapping
        gradient = QLinearGradient(
            clipped.left(), clipped.top(), clipped.right(), clipped.bottom()
        )
        gradient.setColorAt(0.0, QColor(255, 255, 255, 240))
        gradient.setColorAt(0.5, QColor(140, 235, 255, 200))
        gradient.setColorAt(1.0, QColor(0, 243, 255, 255))

        gradient_brush = QBrush(gradient)
        thick_pen = QPen(gradient_brush, 2, Qt.PenStyle.SolidLine)
        thin_pen = QPen(gradient_brush, 1, Qt.PenStyle.SolidLine)

        overflow, length = 12, 24

        # 1. Overflowing Thick Corners (Top-Left & Bottom-Right)
        painter.setPen(thick_pen)

        # Top-Left
        painter.drawLine(
            clipped.left() - overflow,
            clipped.top(),
            clipped.left() + (length - overflow),
            clipped.top(),
        )
        painter.drawLine(
            clipped.left(),
            clipped.top() - overflow,
            clipped.left(),
            clipped.top() + (length - overflow),
        )
        # Bottom-Right
        painter.drawLine(
            clipped.right() + overflow,
            clipped.bottom(),
            clipped.right() - (length - overflow),
            clipped.bottom(),
        )
        painter.drawLine(
            clipped.right(),
            clipped.bottom() + overflow,
            clipped.right(),
            clipped.bottom() - (length - overflow),
        )

        # 2. Clean Closed Thin Corners (Top-Right & Bottom-Left)
        painter.setPen(thin_pen)

        # Top-Right
        painter.drawLine(
            clipped.right(), clipped.top(), clipped.right() - length, clipped.top()
        )
        painter.drawLine(
            clipped.right(), clipped.top(), clipped.right(), clipped.top() + length
        )
        # Bottom-Left
        painter.drawLine(
            clipped.left(), clipped.bottom(), clipped.left() + length, clipped.bottom()
        )
        painter.drawLine(
            clipped.left(), clipped.bottom(), clipped.left(), clipped.bottom() - length
        )
