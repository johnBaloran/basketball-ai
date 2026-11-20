"""Detector classes and the YOLO label format shared by the frame picker, dataset builder and training.

YOLO format: one text file per image, one line per box: `class cx cy w h`, all normalised to 0..1.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Order = class index. Referees are labelled so the model learns to tell them apart from players.
CLASSES: tuple[str, ...] = ("player", "ball", "hoop", "referee")

_GAME = re.compile(r"(20\d\d-\d\d-\d\d)[_-](g[0-9A-Za-z]+)")


@dataclass(frozen=True)
class YoloBox:
    cls: int
    cx: float
    cy: float
    w: float
    h: float

    def line(self) -> str:
        return f"{self.cls} {self.cx:.6f} {self.cy:.6f} {self.w:.6f} {self.h:.6f}"


def to_yolo(cls: int, x1: float, y1: float, x2: float, y2: float, width: int, height: int) -> YoloBox | None:
    """Pixel corners -> normalised YOLO box, clipped to the image; None if nothing is left."""
    x1, x2 = max(0.0, min(x1, x2)), min(float(width), max(x1, x2))
    y1, y2 = max(0.0, min(y1, y2)), min(float(height), max(y1, y2))
    if x2 - x1 < 1 or y2 - y1 < 1:
        return None
    return YoloBox(cls, (x1 + x2) / 2 / width, (y1 + y2) / 2 / height, (x2 - x1) / width, (y2 - y1) / height)


def parse_label_file(text: str, num_classes: int = len(CLASSES)) -> tuple[list[YoloBox], list[str]]:
    """Boxes and a list of problems (bad lines, unknown classes, coordinates outside 0..1)."""
    boxes: list[YoloBox] = []
    problems: list[str] = []
    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            problems.append(f"line {n}: expected 5 values, got {len(parts)}")
            continue
        try:
            cls = int(parts[0])
            cx, cy, w, h = (float(p) for p in parts[1:])
        except ValueError:
            problems.append(f"line {n}: not numbers")
            continue
        if not 0 <= cls < num_classes:
            problems.append(f"line {n}: class {cls} not in 0..{num_classes - 1}")
            continue
        if not all(0.0 <= v <= 1.0 for v in (cx, cy, w, h)) or w <= 0 or h <= 0:
            problems.append(f"line {n}: coordinates must be in 0..1 with positive size")
            continue
        boxes.append(YoloBox(cls, cx, cy, w, h))
    return boxes, problems


def game_group(clip_name: str) -> str:
    """Which game a clip belongs to, for splitting by whole games.

    Uses the `YYYY-MM-DD_g<id>` part of the clip name (docs/DATA_HANDLING.md §3), else the clip name itself.
    """
    m = _GAME.search(clip_name)
    return f"{m.group(1)}_{m.group(2)}" if m else clip_name
