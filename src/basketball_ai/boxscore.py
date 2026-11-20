"""Box scores derived from events (PROJECT_PLAN §5; ARCHITECTURE "Statistics source of truth").

Only **confirmed** events count. An event with no player still counts for its team ("unattributed"), so the
team score stays right when the shooter is unknown. Totals are always recomputed from events, never mutated.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from basketball_ai.contracts import (
    MADE_FIELD_GOALS,
    MISSED_FIELD_GOALS,
    MISSED_SHOTS,
    BoxScore,
    Event,
    EventsFile,
    Manifest,
    PlayerBox,
    StatLine,
    TeamBox,
)

# How each event type adds to a stat line
_INCREMENTS: dict[str, dict[str, int]] = {
    "fg2_made": {"pts": 2, "fgm": 1, "fga": 1, "fg2m": 1, "fg2a": 1},
    "fg2_missed": {"fga": 1, "fg2a": 1},
    "fg3_made": {"pts": 3, "fgm": 1, "fga": 1, "fg3m": 1, "fg3a": 1},
    "fg3_missed": {"fga": 1, "fg3a": 1},
    "ft_made": {"pts": 1, "ftm": 1, "fta": 1},
    "ft_missed": {"fta": 1},
    "rebound_offensive": {"oreb": 1, "reb": 1},
    "rebound_defensive": {"dreb": 1, "reb": 1},
    "assist": {"ast": 1},
    "steal": {"stl": 1},
    "block": {"blk": 1},
}


@dataclass
class _Acc:
    values: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def add(self, event_type: str) -> None:
        for key, n in _INCREMENTS[event_type].items():
            self.values[key] += n

    def line(self) -> StatLine:
        return StatLine(**dict(self.values))


def validate_events(events: EventsFile, manifest: Manifest) -> list[str]:
    """Problems that would make the stats wrong. Empty list = safe to aggregate."""
    problems: list[str] = []
    if events.gameId != manifest.gameId:
        problems.append(f"events are for game {events.gameId}, manifest is for {manifest.gameId}")
    teams = set(manifest.team_ids())
    by_id = {e.eventId: e for e in events.events}
    for e in events.events:
        if e.teamId not in teams:
            problems.append(f"{e.eventId}: team {e.teamId} isn't in this game")
        if e.playerId is not None:
            player = manifest.player(e.playerId)
            if player is None:
                problems.append(f"{e.eventId}: player {e.playerId} isn't on the game roster")
            elif player.teamId != e.teamId:
                problems.append(f"{e.eventId}: player {e.playerId} plays for {player.teamId}, not {e.teamId}")
        if e.status != "confirmed":
            continue
        problems.extend(_relation_problems(e, by_id))
    return problems


def _relation_problems(e: Event, by_id: dict[str, Event]) -> list[str]:
    needs = {
        "assist": (MADE_FIELD_GOALS, "same"),
        "rebound_offensive": (MISSED_SHOTS, "same"),
        "rebound_defensive": (MISSED_SHOTS, "other"),
        "block": (MISSED_FIELD_GOALS, "other"),
    }
    if e.eventType not in needs:
        return []
    allowed, team_rule = needs[e.eventType]
    if e.relatedEventId is None:
        return [f"{e.eventId}: {e.eventType} must reference the shot it belongs to (relatedEventId)"]
    shot = by_id.get(e.relatedEventId)
    if shot is None:
        return [f"{e.eventId}: related event {e.relatedEventId} not found"]
    problems: list[str] = []
    if shot.eventType not in allowed:
        problems.append(f"{e.eventId}: {e.eventType} can't relate to a {shot.eventType}")
    if shot.status != "confirmed":
        problems.append(f"{e.eventId}: its shot {shot.eventId} isn't confirmed")
    same_team = shot.teamId == e.teamId
    if team_rule == "same" and not same_team:
        problems.append(f"{e.eventId}: {e.eventType} must be by the shooting team")
    if team_rule == "other" and same_team:
        problems.append(f"{e.eventId}: {e.eventType} must be by the defending team")
    if e.eventType == "assist" and e.playerId is not None and e.playerId == shot.playerId:
        problems.append(f"{e.eventId}: a player can't assist their own basket")
    return problems


def compute_box_score(events: EventsFile, manifest: Manifest) -> BoxScore:
    """Aggregate confirmed events. Raises ValueError if the events fail validation."""
    problems = validate_events(events, manifest)
    if problems:
        raise ValueError("events failed validation:\n  " + "\n  ".join(problems))
    players: dict[str, _Acc] = defaultdict(_Acc)
    teams: dict[str, _Acc] = defaultdict(_Acc)
    unattributed: dict[str, _Acc] = defaultdict(_Acc)
    counted: list[str] = []
    for e in sorted(events.events, key=lambda ev: (ev.timestampSeconds, ev.eventId)):
        if e.status != "confirmed":
            continue
        counted.append(e.eventId)
        teams[e.teamId].add(e.eventType)
        if e.playerId is None:
            unattributed[e.teamId].add(e.eventType)
        else:
            players[e.playerId].add(e.eventType)
    team_of = {r.playerId: r.teamId for r in manifest.roster}
    return BoxScore(
        gameId=events.gameId,
        players=[
            PlayerBox(playerId=r.playerId, teamId=r.teamId, stats=players[r.playerId].line())
            for r in manifest.roster
            if r.playerId in players and r.playerId in team_of
        ],
        teams=[
            TeamBox(teamId=t, stats=teams[t].line(), unattributed=unattributed[t].line()) for t in manifest.team_ids()
        ],
        countedEventIds=counted,
    )


def check_invariants(box: BoxScore) -> list[str]:
    """Statistical invariants (ARCHITECTURE.md). Empty list = consistent."""
    problems: list[str] = []
    lines = [(f"player {p.playerId}", p.stats) for p in box.players] + [
        (f"team {t.teamId}", t.stats) for t in box.teams
    ]
    for who, s in lines:
        if s.fg3m > s.fg3a or s.fg2m > s.fg2a or s.ftm > s.fta:
            problems.append(f"{who}: more makes than attempts")
        if s.fgm != s.fg2m + s.fg3m or s.fga != s.fg2a + s.fg3a:
            problems.append(f"{who}: field goals don't add up")
        if s.pts != 2 * s.fg2m + 3 * s.fg3m + s.ftm:
            problems.append(f"{who}: points don't match made shots")
        if s.reb != s.oreb + s.dreb:
            problems.append(f"{who}: rebounds don't add up")
    for t in box.teams:
        players = [p.stats for p in box.players if p.teamId == t.teamId]
        for key in StatLine.model_fields:
            total = sum(getattr(s, key) for s in players) + getattr(t.unattributed, key)
            if total != getattr(t.stats, key):
                problems.append(f"team {t.teamId}: {key} players + unattributed != team total")
    return problems
