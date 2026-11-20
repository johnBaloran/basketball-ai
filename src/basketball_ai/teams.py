"""Team assignment from jersey colour (no model): cluster torso colours into two groups.

Each player crop's torso (upper-middle of the box) gives a mean colour; 2-means clustering splits the two
teams; clusters are named from the manifest's colour hints when they're given. Referees and odd crops are
left unassigned when they sit far from both cluster centres. A track's team is a vote over its frames.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from basketball_ai.tracking import Box
from basketball_ai.video import Frame

Color = npt.NDArray[np.float64]  # RGB, 0..255

# Rough RGB for common jersey colour words (manifest TeamRef.colorHint)
COLOR_WORDS: dict[str, tuple[int, int, int]] = {
    "white": (235, 235, 235),
    "black": (25, 25, 25),
    "grey": (128, 128, 128),
    "gray": (128, 128, 128),
    "red": (200, 30, 30),
    "maroon": (110, 20, 30),
    "orange": (240, 130, 20),
    "yellow": (240, 220, 40),
    "gold": (210, 170, 50),
    "green": (30, 140, 60),
    "blue": (30, 70, 200),
    "dark blue": (20, 30, 90),
    "navy": (20, 30, 80),
    "light blue": (120, 180, 235),
    "purple": (100, 40, 150),
    "pink": (240, 130, 180),
}


def torso_color(frame: Frame, box: Box) -> Color | None:
    """Mean colour of the torso region (rows 20-50%, middle 50% of columns) of a player box."""
    h, w = frame.shape[:2]
    x1, x2 = int(box.x1 + (box.x2 - box.x1) * 0.25), int(box.x1 + (box.x2 - box.x1) * 0.75)
    y1, y2 = int(box.y1 + (box.y2 - box.y1) * 0.2), int(box.y1 + (box.y2 - box.y1) * 0.5)
    x1, x2, y1, y2 = max(0, x1), min(w, x2), max(0, y1), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return None
    region = frame[y1:y2, x1:x2].reshape(-1, 3).astype(np.float64)
    return np.asarray(np.median(region, axis=0), dtype=np.float64)


@dataclass(frozen=True)
class TeamModel:
    centers: tuple[Color, Color]
    team_ids: tuple[str, str]
    max_distance: float  # beyond this from both centres -> unassigned (e.g. referees)

    def assign(self, color: Color) -> str | None:
        d = [float(np.linalg.norm(color - c)) for c in self.centers]
        best = int(np.argmin(d))
        return self.team_ids[best] if d[best] <= self.max_distance else None


def _kmeans2(points: npt.NDArray[np.float64], iterations: int = 20) -> tuple[Color, Color]:
    # Deterministic start: the two points farthest apart along the main colour axis
    order = np.argsort(points @ (points.max(axis=0) - points.min(axis=0)))
    a, b = points[order[0]].copy(), points[order[-1]].copy()
    for _ in range(iterations):
        near_a = np.linalg.norm(points - a, axis=1) <= np.linalg.norm(points - b, axis=1)
        if near_a.all() or (~near_a).all():
            break
        a, b = points[near_a].mean(axis=0), points[~near_a].mean(axis=0)
    return a, b


def fit_team_model(
    colors: Sequence[Color],
    team_ids: tuple[str, str],
    hints: tuple[str | None, str | None] = (None, None),
    max_distance: float = 90.0,
) -> TeamModel:
    """Two colour clusters, named by the colour hints (home, away) when given, else in cluster order."""
    if len(colors) < 2:
        raise ValueError("need at least two player colours to split teams")
    a, b = _kmeans2(np.stack(colors))
    hint_rgb = [
        np.array(COLOR_WORDS[h.lower()], dtype=np.float64) if h and h.lower() in COLOR_WORDS else None
        for h in hints
    ]
    ha, hb = hint_rgb
    if ha is not None and hb is not None:
        straight = np.linalg.norm(a - ha) + np.linalg.norm(b - hb)
        swapped = np.linalg.norm(a - hb) + np.linalg.norm(b - ha)
        if swapped < straight:
            a, b = b, a
    return TeamModel((a, b), team_ids, max_distance)


def vote_track_teams(labels: dict[str, list[str | None]], min_share: float = 0.7) -> dict[str, str | None]:
    """Team per track from per-frame labels; None when the votes are split."""
    out: dict[str, str | None] = {}
    for track, votes in labels.items():
        counts = Counter(v for v in votes if v is not None)
        if not counts:
            out[track] = None
            continue
        team, n = counts.most_common(1)[0]
        out[track] = team if n / sum(counts.values()) >= min_share else None
    return out
