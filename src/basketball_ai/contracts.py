"""Versioned file contracts between this project and the league app (DEC-007).

Inputs: a game/clip **manifest** (teams, roster with jersey numbers, gym, court, video range). Outputs: an
**events** file (the source of truth) and a derived **box score**. Field names mirror Recess: `playerId` is
the Recess `userId`, `gymId` the `Game.locationId`, team ids the `Game.homeTeamId` / `awayTeamId`.

JSON Schema copies live in `schemas/` (regenerate with `bball-schemas`); a test keeps them in sync.
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION: Literal["0.1"] = "0.1"

EventType = Literal[
    "fg2_made",
    "fg2_missed",
    "fg3_made",
    "fg3_missed",
    "ft_made",
    "ft_missed",
    "rebound_offensive",
    "rebound_defensive",
    "assist",
    "steal",
    "block",
]
EVENT_TYPES: tuple[EventType, ...] = (
    "fg2_made",
    "fg2_missed",
    "fg3_made",
    "fg3_missed",
    "ft_made",
    "ft_missed",
    "rebound_offensive",
    "rebound_defensive",
    "assist",
    "steal",
    "block",
)
SHOT_TYPES: frozenset[str] = frozenset(
    {"fg2_made", "fg2_missed", "fg3_made", "fg3_missed", "ft_made", "ft_missed"}
)
MADE_FIELD_GOALS: frozenset[str] = frozenset({"fg2_made", "fg3_made"})
MISSED_SHOTS: frozenset[str] = frozenset({"fg2_missed", "fg3_missed", "ft_missed"})
MISSED_FIELD_GOALS: frozenset[str] = frozenset({"fg2_missed", "fg3_missed"})

EventStatus = Literal["proposed", "pending_review", "confirmed", "rejected", "unresolved"]

# Box score keys, named for the Recess `PlayerStatLine.stats` map (DEC-007)
STAT_KEYS: tuple[str, ...] = (
    "pts",
    "fgm",
    "fga",
    "fg2m",
    "fg2a",
    "fg3m",
    "fg3a",
    "ftm",
    "fta",
    "oreb",
    "dreb",
    "reb",
    "ast",
    "stl",
    "blk",
)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ─── Manifest (input) ─────────────────────────────────────────────────────────


class TeamRef(_Model):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    colorHint: str | None = Field(
        default=None, description='Jersey colour words, e.g. "white" or "dark blue"'
    )


class RosterEntry(_Model):
    teamId: str = Field(min_length=1)
    playerId: str = Field(min_length=1, description="Recess userId (or a walk-in id)")
    jerseyNumber: int | None = Field(default=None, ge=0, le=99)
    displayName: str | None = None


class VideoRef(_Model):
    source: str = Field(min_length=1, description="Path relative to BBALL_DATA_DIR, or a storage reference")
    startSeconds: float = Field(default=0, ge=0)
    endSeconds: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _range(self) -> Self:
        if self.endSeconds is not None and self.endSeconds <= self.startSeconds:
            raise ValueError("endSeconds must be after startSeconds")
        return self


class Manifest(_Model):
    schemaVersion: Literal["0.1"] = SCHEMA_VERSION
    gameId: str = Field(min_length=1)
    homeTeam: TeamRef
    awayTeam: TeamRef
    roster: list[RosterEntry]
    gymId: str | None = None
    court: str | None = None
    video: VideoRef

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        teams = {self.homeTeam.id, self.awayTeam.id}
        if len(teams) != 2:
            raise ValueError("homeTeam and awayTeam must be different teams")
        seen_players: set[str] = set()
        seen_numbers: set[tuple[str, int]] = set()
        for r in self.roster:
            if r.teamId not in teams:
                raise ValueError(
                    f"roster player {r.playerId} has teamId {r.teamId}, which isn't in this game"
                )
            if r.playerId in seen_players:
                raise ValueError(f"player {r.playerId} appears more than once in the roster")
            seen_players.add(r.playerId)
            if r.jerseyNumber is not None:
                key = (r.teamId, r.jerseyNumber)
                if key in seen_numbers:
                    raise ValueError(f"jersey #{r.jerseyNumber} is used twice on team {r.teamId}")
                seen_numbers.add(key)
        return self

    def team_ids(self) -> tuple[str, str]:
        return (self.homeTeam.id, self.awayTeam.id)

    def player(self, player_id: str) -> RosterEntry | None:
        return next((r for r in self.roster if r.playerId == player_id), None)


# ─── Events (output; source of truth) ─────────────────────────────────────────


class CourtPoint(_Model):
    """Court coordinates in feet: x along the length (0 = left baseline), y across (0 = near sideline)."""

    x: float
    y: float


class Evidence(_Model):
    clipRef: str | None = None
    trackIds: list[str] = Field(default_factory=list)
    startFrame: int | None = Field(default=None, ge=0)
    endFrame: int | None = Field(default=None, ge=0)
    modelVersion: str | None = None
    notes: str | None = None


class Event(_Model):
    eventId: str = Field(min_length=1, description="Stable id: retries and re-imports must not double count")
    gameId: str = Field(min_length=1)
    eventType: EventType
    timestampSeconds: float = Field(ge=0)
    teamId: str = Field(min_length=1)
    playerId: str | None = Field(default=None, description="null when identity is uncertain")
    courtCoordinates: CourtPoint | None = None
    eventConfidence: float = Field(ge=0, le=1)
    identityConfidence: float | None = Field(default=None, ge=0, le=1)
    status: EventStatus
    relatedEventId: str | None = Field(
        default=None,
        description="assist -> the made field goal; rebound/block -> the missed shot",
    )
    evidence: Evidence = Field(default_factory=Evidence)


class EventsFile(_Model):
    schemaVersion: Literal["0.1"] = SCHEMA_VERSION
    gameId: str = Field(min_length=1)
    modelVersion: str | None = None
    events: list[Event]

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        ids: set[str] = set()
        for e in self.events:
            if e.gameId != self.gameId:
                raise ValueError(f"event {e.eventId} belongs to game {e.gameId}, not {self.gameId}")
            if e.eventId in ids:
                raise ValueError(f"duplicate eventId {e.eventId}")
            ids.add(e.eventId)
        return self


# ─── Box score (output; derived from confirmed events only) ───────────────────


class StatLine(_Model):
    pts: int = 0
    fgm: int = 0
    fga: int = 0
    fg2m: int = 0
    fg2a: int = 0
    fg3m: int = 0
    fg3a: int = 0
    ftm: int = 0
    fta: int = 0
    oreb: int = 0
    dreb: int = 0
    reb: int = 0
    ast: int = 0
    stl: int = 0
    blk: int = 0


class PlayerBox(_Model):
    playerId: str
    teamId: str
    stats: StatLine


class TeamBox(_Model):
    teamId: str
    stats: StatLine = Field(description="All confirmed events for the team, including unattributed ones")
    unattributed: StatLine = Field(description="Confirmed events whose player is unknown")


class BoxScore(_Model):
    schemaVersion: Literal["0.1"] = SCHEMA_VERSION
    gameId: str
    players: list[PlayerBox]
    teams: list[TeamBox]
    countedEventIds: list[str] = Field(description="Confirmed events included, for audit")


CONTRACTS: dict[str, type[BaseModel]] = {
    "manifest": Manifest,
    "events": EventsFile,
    "boxscore": BoxScore,
}
