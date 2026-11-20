"""Classify possession changes into event candidates (PROJECT_PLAN §6 principles).

Same team -> pass. Other team after a missed shot -> defensive rebound candidate; otherwise -> steal
candidate. Candidates are always `pending_review` here: thresholds for automatic confirmation come later.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Literal

from basketball_ai.tracking import PossessionSegment

ChangeKind = Literal["pass", "steal_candidate", "rebound_candidate", "unknown"]


@dataclass(frozen=True)
class PossessionChange:
    fromTrack: str
    toTrack: str
    atFrame: int
    kind: ChangeKind
    reason: str


def classify_changes(
    segments: Sequence[PossessionSegment],
    track_teams: dict[str, str | None],
    missed_shot_frames: Sequence[int] = (),
    rebound_window: int = 90,
) -> list[PossessionChange]:
    """`missed_shot_frames`: frames where a shot missed (from shot detection); `rebound_window` in frames."""
    out: list[PossessionChange] = []
    for a, b in pairwise(segments):
        if a.trackId == b.trackId:
            continue
        ta, tb = track_teams.get(a.trackId), track_teams.get(b.trackId)
        if ta is None or tb is None:
            out.append(PossessionChange(a.trackId, b.trackId, b.startFrame, "unknown", "team unknown for a track"))
            continue
        if ta == tb:
            out.append(PossessionChange(a.trackId, b.trackId, b.startFrame, "pass", "same team"))
            continue
        after_miss = any(a.startFrame <= f <= b.startFrame and b.startFrame - f <= rebound_window for f in missed_shot_frames)
        if after_miss:
            out.append(PossessionChange(a.trackId, b.trackId, b.startFrame, "rebound_candidate", "other team after a missed shot"))
        else:
            out.append(PossessionChange(a.trackId, b.trackId, b.startFrame, "steal_candidate", "other team, no shot before"))
    return out
