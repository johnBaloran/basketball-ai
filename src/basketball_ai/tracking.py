"""Detections, a dependency-free baseline tracker, and ball possession.

The tracker is a simple greedy IoU matcher. It's a baseline to measure against, not the final tracker
(ByteTrack or similar comes in Phase 1 evaluation). Track ids are temporary: identity.py links them to
roster players.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol

from basketball_ai.video import Frame

Label = Literal["player", "ball", "hoop"]


@dataclass(frozen=True)
class Box:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    @property
    def area(self) -> float:
        return max(0.0, self.x2 - self.x1) * max(0.0, self.y2 - self.y1)

    def iou(self, other: Box) -> float:
        ix = max(0.0, min(self.x2, other.x2) - max(self.x1, other.x1))
        iy = max(0.0, min(self.y2, other.y2) - max(self.y1, other.y1))
        inter = ix * iy
        union = self.area + other.area - inter
        return inter / union if union > 0 else 0.0

    def expanded(self, ratio: float) -> Box:
        dx, dy = (self.x2 - self.x1) * ratio, (self.y2 - self.y1) * ratio
        return Box(self.x1 - dx, self.y1 - dy, self.x2 + dx, self.y2 + dy)

    def contains(self, point: tuple[float, float]) -> bool:
        return self.x1 <= point[0] <= self.x2 and self.y1 <= point[1] <= self.y2


@dataclass(frozen=True)
class Detection:
    label: Label
    box: Box
    confidence: float


class Detector(Protocol):
    """Anything that turns a frame into detections (YOLO adapter in detectors.py, fakes in tests)."""

    def detect(self, frame: Frame) -> list[Detection]: ...


@dataclass(frozen=True)
class TrackedBox:
    trackId: str
    label: Label
    box: Box
    confidence: float


@dataclass
class _Track:
    track_id: str
    label: Label
    box: Box
    missed: int = 0


@dataclass
class IouTracker:
    """Greedy IoU matching per label. A track survives `max_missed` frames without a match."""

    iou_threshold: float = 0.3
    max_missed: int = 10
    _tracks: list[_Track] = field(default_factory=list)
    _next: int = 1

    def update(self, detections: Sequence[Detection]) -> list[TrackedBox]:
        out: list[TrackedBox] = []
        unmatched = set(range(len(self._tracks)))
        for det in sorted(detections, key=lambda d: d.confidence, reverse=True):
            best, best_iou = None, self.iou_threshold
            for i in unmatched:
                t = self._tracks[i]
                if t.label != det.label:
                    continue
                score = t.box.iou(det.box)
                if score >= best_iou:
                    best, best_iou = i, score
            if best is None:
                track = _Track(f"{det.label[0]}{self._next}", det.label, det.box)
                self._next += 1
                self._tracks.append(track)
            else:
                unmatched.discard(best)
                track = self._tracks[best]
                track.box, track.missed = det.box, 0
            out.append(TrackedBox(track.track_id, det.label, det.box, det.confidence))
        for i in unmatched:
            self._tracks[i].missed += 1
        self._tracks = [t for t in self._tracks if t.missed <= self.max_missed]
        return out


# ─── Possession ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PossessionSegment:
    trackId: str
    startFrame: int
    endFrame: int  # inclusive

    @property
    def frames(self) -> int:
        return self.endFrame - self.startFrame + 1


def holder_in_frame(players: Iterable[TrackedBox], ball: TrackedBox | None, reach: float = 0.15) -> str | None:
    """The player whose (slightly expanded) box holds the ball centre; the closest one if several."""
    if ball is None:
        return None
    point = ball.box.center
    candidates = [p for p in players if p.label == "player" and p.box.expanded(reach).contains(point)]
    if not candidates:
        return None

    def dist(p: TrackedBox) -> float:
        cx, cy = p.box.center
        return (cx - point[0]) ** 2 + (cy - point[1]) ** 2

    return min(candidates, key=dist).trackId


def possession_segments(holders: Sequence[str | None], min_frames: int = 5) -> list[PossessionSegment]:
    """Turn per-frame holders into possession segments lasting at least `min_frames` frames.

    Short flickers (the ball passing in front of a player) are dropped rather than credited.
    """
    segments: list[PossessionSegment] = []
    start = 0
    for i in range(1, len(holders) + 1):
        if i == len(holders) or holders[i] != holders[start]:
            who = holders[start]
            if who is not None and i - start >= min_frames:
                segments.append(PossessionSegment(who, start, i - 1))
            start = i
    return segments


def possession_changes(segments: Sequence[PossessionSegment]) -> list[tuple[PossessionSegment, PossessionSegment]]:
    """Consecutive segments with different holders: passes, steals or rebounds, classified downstream."""
    return [(a, b) for a, b in zip(segments, segments[1:], strict=False) if a.trackId != b.trackId]
