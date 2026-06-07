from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    """Pixel bounds for a host display."""

    x: int
    y: int
    width: int
    height: int

    def clamp(self, px: int, py: int) -> tuple[int, int]:
        max_x = self.x + self.width - 1
        max_y = self.y + self.height - 1
        return min(max(px, self.x), max_x), min(max(py, self.y), max_y)


@dataclass(frozen=True)
class TouchPoint:
    """A touch point reported by the tablet app."""

    x: float
    y: float
    source_width: float
    source_height: float


class CoordinateMapper:
    """Map tablet touch coordinates to the host virtual monitor rectangle."""

    def __init__(self, target: Rect) -> None:
        if target.width <= 0 or target.height <= 0:
            raise ValueError("target width and height must be positive")
        self.target = target

    def map_point(self, point: TouchPoint) -> tuple[int, int]:
        if point.source_width <= 0 or point.source_height <= 0:
            raise ValueError("source width and height must be positive")

        ratio_x = point.x / point.source_width
        ratio_y = point.y / point.source_height
        host_x = round(self.target.x + ratio_x * (self.target.width - 1))
        host_y = round(self.target.y + ratio_y * (self.target.height - 1))
        return self.target.clamp(host_x, host_y)
