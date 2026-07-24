# =============================================================================
# CropGeometryEngine — single source of truth for screen<->source-pixel math
# =============================================================================
from dataclasses import dataclass

from PyQt6.QtCore import QRect

ASPECT_RATIOS = {
    "1:1 Square": 1.0,
    "16:9 Widescreen": 16.0 / 9.0,
    "4:3 Standard": 4.0 / 3.0,
    # "Freeform" intentionally absent -> resolve_aspect_ratio returns None
}


@dataclass(frozen=True)
class ViewportGeometry:
    """Immutable snapshot of the current label-to-pixmap-to-source mapping."""

    label_width: int
    label_height: int
    pixmap_width: int
    pixmap_height: int
    source_width: int
    source_height: int

    @property
    def offset_x(self) -> int:
        return (self.label_width - self.pixmap_width) // 2

    @property
    def offset_y(self) -> int:
        return (self.label_height - self.pixmap_height) // 2

    @property
    def scale_x(self) -> float:
        return self.source_width / self.pixmap_width if self.pixmap_width else 1.0

    @property
    def scale_y(self) -> float:
        return self.source_height / self.pixmap_height if self.pixmap_height else 1.0

    @property
    def screen_to_source_x(self) -> float:
        return self.pixmap_width / self.source_width if self.source_width else 1.0

    @property
    def screen_to_source_y(self) -> float:
        return self.pixmap_height / self.source_height if self.source_height else 1.0


class CropGeometryEngine:
    """Single source of truth for every screen<->source-pixel transform and
    16px JPEG MCU grid snap used by the crop tool. Stateless — every method
    takes a ViewportGeometry rather than reading widget state.
    """

    GRID_SIZE = 16

    @staticmethod
    def resolve_aspect_ratio(ratio_label: str) -> float | None:
        return ASPECT_RATIOS.get(ratio_label)

    @classmethod
    def snap_to_grid(cls, value: float, minimum: int = GRID_SIZE) -> int:
        return max(minimum, round(value / cls.GRID_SIZE) * cls.GRID_SIZE)

    @classmethod
    def screen_rect_to_source_rect(
        cls,
        screen_rect: QRect,
        viewport: ViewportGeometry,
        lossless: bool,
        ratio_label: str,
    ) -> QRect:
        """Maps a screen-space rubber-band rect onto true source-image pixel
        space. Grid snap and aspect-ratio lock are both applied in IMAGE
        space so repeated snap/unsnap cycles don't compound rounding error.
        """
        img_x = (screen_rect.x() - viewport.offset_x) * viewport.scale_x
        img_y = (screen_rect.y() - viewport.offset_y) * viewport.scale_y
        img_w = screen_rect.width() * viewport.scale_x
        img_h = screen_rect.height() * viewport.scale_y

        aspect = cls.resolve_aspect_ratio(ratio_label)

        if lossless:
            img_w = cls.snap_to_grid(img_w)
            img_h = (
                cls.snap_to_grid(img_w / aspect) if aspect else cls.snap_to_grid(img_h)
            )
            img_x = round(img_x / cls.GRID_SIZE) * cls.GRID_SIZE
            img_y = round(img_y / cls.GRID_SIZE) * cls.GRID_SIZE
        else:
            img_w = max(1, round(img_w))
            img_h = max(1, round(img_w / aspect)) if aspect else max(1, round(img_h))
            img_x = round(img_x)
            img_y = round(img_y)

        return QRect(int(img_x), int(img_y), int(img_w), int(img_h))

    @classmethod
    def source_rect_to_screen_rect(
        cls,
        source_rect: QRect,
        viewport: ViewportGeometry,
        ratio_label: str,
    ) -> QRect:
        """Inverse of screen_rect_to_source_rect: projects a source-pixel
        rect back onto label/screen coordinates for drawing the rubber band.
        Height is re-derived from the projected width (not independently
        rounded) whenever an aspect ratio is locked.
        """
        aspect = cls.resolve_aspect_ratio(ratio_label)

        screen_x = (
            int(source_rect.x() * viewport.screen_to_source_x) + viewport.offset_x
        )
        screen_y = (
            int(source_rect.y() * viewport.screen_to_source_y) + viewport.offset_y
        )
        screen_w = int(source_rect.width() * viewport.screen_to_source_x)
        screen_h = (
            max(1, round(screen_w / aspect))
            if aspect
            else int(source_rect.height() * viewport.screen_to_source_y)
        )
        return QRect(screen_x, screen_y, screen_w, screen_h)

    @staticmethod
    def clamp_screen_rect_to_pixmap(
        screen_rect: QRect, viewport: ViewportGeometry
    ) -> QRect:
        """Clamps a screen rect's origin/size so it never reads outside the
        pixmap bounds, in label-local (pixmap-offset) coordinates.
        """
        adj_x = max(0, min(screen_rect.x() - viewport.offset_x, viewport.pixmap_width))
        adj_y = max(0, min(screen_rect.y() - viewport.offset_y, viewport.pixmap_height))
        adj_w = min(screen_rect.width(), viewport.pixmap_width - adj_x)
        adj_h = min(screen_rect.height(), viewport.pixmap_height - adj_y)
        return QRect(adj_x, adj_y, max(0, adj_w), max(0, adj_h))

    @classmethod
    def apply_aspect_lock_to_width(
        cls, width: int, ratio_label: str, lossless: bool
    ) -> int | None:
        """Given a target width and the active ratio, returns the matching
        height, or None for Freeform (caller keeps whatever height it had).
        """
        aspect = cls.resolve_aspect_ratio(ratio_label)
        if aspect is None:
            return None
        if lossless:
            return cls.snap_to_grid(width / aspect)
        return max(1, round(width / aspect))

    @classmethod
    def snap_screen_rect_to_grid(
        cls,
        screen_rect: QRect,
        viewport: ViewportGeometry,
        lossless: bool,
        ratio_label: str,
    ) -> QRect:
        """Pure inverse matrix mapping to snap screen bounding fields!"""
        # Convert screen coordinate selection frame into true image pixel coordinates
        source_rect = cls.screen_rect_to_source_rect(
            screen_rect, viewport, lossless, ratio_label
        )

        # Backward-map image source pixels back onto precise on-screen UI pixels
        snapped_x = (source_rect.x() / viewport.scale_x) + viewport.offset_x
        snapped_y = (source_rect.y() / viewport.scale_y) + viewport.offset_y
        snapped_w = source_rect.width() / viewport.scale_x
        snapped_h = source_rect.height() / viewport.scale_y

        return QRect(int(snapped_x), int(snapped_y), int(snapped_w), int(snapped_h))
