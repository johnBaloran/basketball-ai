"""Court geometry: image -> court (feet) via a homography from court keypoints, and 2PT/3PT from location.

Keypoints come from a court-keypoint detector later (Phase 1/4). The 3-point line is per-gym configuration,
never a screen-space rectangle (PROJECT_PLAN §6).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt

Point = tuple[float, float]
Matrix = npt.NDArray[np.float64]


@dataclass(frozen=True)
class CourtSpec:
    """Dimensions in feet. Defaults are a full NBA-size court and line (PROPOSED; set per gym)."""

    length: float = 94.0
    width: float = 50.0
    basket_from_baseline: float = 5.25  # hoop centre
    three_point_radius: float = 23.75
    corner_three_distance: float = 22.0  # straight segment along the sidelines

    def baskets(self) -> tuple[Point, Point]:
        y = self.width / 2
        return (self.basket_from_baseline, y), (self.length - self.basket_from_baseline, y)


def homography(image_points: Sequence[Point], court_points: Sequence[Point]) -> Matrix:
    """3x3 matrix mapping image pixels to court feet, from 4+ matching points (DLT, least squares)."""
    if len(image_points) != len(court_points) or len(image_points) < 4:
        raise ValueError("need at least 4 matching image/court points")
    rows = []
    for (x, y), (u, v) in zip(image_points, court_points, strict=True):
        rows.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        rows.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _, _, vt = np.linalg.svd(np.asarray(rows, dtype=np.float64))
    h = vt[-1].reshape(3, 3)
    return np.asarray(h / h[2, 2], dtype=np.float64)


def to_court(h: Matrix, point: Point) -> Point:
    x, y, w = h @ np.array([point[0], point[1], 1.0])
    return (float(x / w), float(y / w))


def shot_value(spot: Point, spec: CourtSpec | None = None, tolerance: float = 0.0) -> Literal[2, 3]:
    """2 or 3 from the shooter's last ground contact (feet). On the line counts as 2.

    Uses the nearer basket; the corner segment is a straight line `corner_three_distance` from the basket.
    """
    spec = spec or CourtSpec()
    near = min(spec.baskets(), key=lambda b: math.dist(spot, b))
    dx_from_baseline = abs(spot[0] - (0 if near[0] < spec.length / 2 else spec.length))
    lateral = abs(spot[1] - near[1])
    # Where the arc meets the corner lines, measured from the baseline
    corner_end = spec.basket_from_baseline + math.sqrt(
        max(spec.three_point_radius**2 - spec.corner_three_distance**2, 0)
    )
    if dx_from_baseline <= corner_end:
        return 3 if lateral > spec.corner_three_distance + tolerance else 2
    return 3 if math.dist(spot, near) > spec.three_point_radius + tolerance else 2
