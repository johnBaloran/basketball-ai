"""Roster-constrained player identity from jersey-number evidence (PROJECT_PLAN §5 "Identity model").

A temporary `trackId` is linked to a permanent roster `playerId` only when several confident jersey readings
agree and the number exists on that team's roster. Weak, conflicting or ambiguous evidence stays
**unresolved**. Never guess. No face recognition (DEC-001).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Literal

from basketball_ai.contracts import Manifest

IdentityStatus = Literal["resolved", "unresolved", "conflict"]


@dataclass(frozen=True)
class JerseyObservation:
    """One jersey reading for one track in one frame (from OCR / a number classifier)."""

    trackId: str
    frame: int
    number: int | None  # None = digits not readable in this frame
    confidence: float  # reader confidence, 0..1
    teamId: str | None = None  # from team classification, when known


@dataclass(frozen=True)
class TrackIdentity:
    trackId: str
    status: IdentityStatus
    playerId: str | None
    teamId: str | None
    jerseyNumber: int | None
    confidence: float  # identity confidence, 0..1 (0 when unresolved)
    observations: int  # confident readings used
    firstFrame: int
    lastFrame: int
    reason: str


@dataclass(frozen=True)
class IdentityConfig:
    min_reading_confidence: float = 0.5  # ignore readings below this
    min_readings: int = 3  # confident readings needed before crediting a player
    min_vote_share: float = 0.7  # share of (confidence-weighted) votes the winning number needs
    min_team_share: float = 0.7  # share of team labels that must agree


def resolve_tracks(
    observations: list[JerseyObservation], manifest: Manifest, config: IdentityConfig | None = None
) -> dict[str, TrackIdentity]:
    """Identity for every track seen, then cross-track contradiction checks."""
    cfg = config or IdentityConfig()
    by_track: dict[str, list[JerseyObservation]] = defaultdict(list)
    for o in observations:
        by_track[o.trackId].append(o)
    roster = {(r.teamId, r.jerseyNumber): r.playerId for r in manifest.roster if r.jerseyNumber is not None}
    resolved = {tid: _resolve_one(tid, obs, roster, cfg) for tid, obs in by_track.items()}
    return _mark_conflicts(resolved)


def _resolve_one(
    track_id: str,
    obs: list[JerseyObservation],
    roster: dict[tuple[str, int | None], str],
    cfg: IdentityConfig,
) -> TrackIdentity:
    first, last = min(o.frame for o in obs), max(o.frame for o in obs)

    def unresolved(
        reason: str, team: str | None = None, number: int | None = None, n: int = 0
    ) -> TrackIdentity:
        return TrackIdentity(track_id, "unresolved", None, team, number, 0.0, n, first, last, reason)

    team = _team_vote(obs, cfg.min_team_share)
    readings = [o for o in obs if o.number is not None and o.confidence >= cfg.min_reading_confidence]
    if len(readings) < cfg.min_readings:
        return unresolved(f"only {len(readings)} confident jersey readings (need {cfg.min_readings})", team)

    votes: dict[int, float] = defaultdict(float)
    for o in readings:
        assert o.number is not None  # filtered above
        votes[o.number] += o.confidence
    number, weight = max(votes.items(), key=lambda kv: kv[1])
    share = weight / sum(votes.values())
    if share < cfg.min_vote_share:
        return unresolved(
            f"readings disagree (#{number} has {share:.0%} of votes)", team, None, len(readings)
        )

    if team is not None:
        player = roster.get((team, number))
        if player is None:
            return unresolved(f"#{number} isn't on team {team}'s roster", team, number, len(readings))
    else:
        matches = [(t, p) for (t, n), p in roster.items() if n == number]
        if len(matches) != 1:
            why = "no roster player wears" if not matches else "more than one team has"
            return unresolved(f"team unknown and {why} #{number}", None, number, len(readings))
        team, player = matches[0]

    mean_conf = sum(o.confidence for o in readings if o.number == number) / sum(
        1 for o in readings if o.number == number
    )
    return TrackIdentity(
        track_id,
        "resolved",
        player,
        team,
        number,
        round(share * mean_conf, 4),
        len(readings),
        first,
        last,
        f"#{number} in {len(readings)} readings ({share:.0%} agreement)",
    )


def _team_vote(obs: list[JerseyObservation], min_share: float) -> str | None:
    labels = Counter(o.teamId for o in obs if o.teamId is not None)
    if not labels:
        return None
    team, n = labels.most_common(1)[0]
    return team if n / sum(labels.values()) >= min_share else None


def _mark_conflicts(ids: dict[str, TrackIdentity]) -> dict[str, TrackIdentity]:
    """One player can't be two tracks at the same time: overlapping tracks credited to one player conflict."""
    by_player: dict[str, list[TrackIdentity]] = defaultdict(list)
    for t in ids.values():
        if t.status == "resolved" and t.playerId is not None:
            by_player[t.playerId].append(t)
    out = dict(ids)
    for player, tracks in by_player.items():
        for a in tracks:
            clash = [
                b
                for b in tracks
                if b is not a and a.firstFrame <= b.lastFrame and b.firstFrame <= a.lastFrame
            ]
            if clash:
                others = ", ".join(sorted(b.trackId for b in clash))
                out[a.trackId] = TrackIdentity(
                    a.trackId,
                    "conflict",
                    None,
                    a.teamId,
                    a.jerseyNumber,
                    0.0,
                    a.observations,
                    a.firstFrame,
                    a.lastFrame,
                    f"also credited to {player} on overlapping track(s) {others}; needs review",
                )
    return out


def player_registry(ids: dict[str, TrackIdentity]) -> dict[str, list[str]]:
    """Permanent identity -> the temporary tracks linked to it (one player may have many tracks)."""
    registry: dict[str, list[str]] = defaultdict(list)
    for t in sorted(ids.values(), key=lambda t: t.firstFrame):
        if t.status == "resolved" and t.playerId is not None:
            registry[t.playerId].append(t.trackId)
    return dict(registry)
