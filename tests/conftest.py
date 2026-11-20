"""Synthetic fixtures only. No real footage, rosters or names (docs/DATA_HANDLING.md)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from basketball_ai.contracts import Event, EventsFile, EventStatus, EventType, Manifest

HOME, AWAY = "team-home", "team-away"


def make_manifest(**overrides: object) -> Manifest:
    data: dict[str, object] = {
        "gameId": "g1",
        "homeTeam": {"id": HOME, "name": "Home", "colorHint": "white"},
        "awayTeam": {"id": AWAY, "name": "Away", "colorHint": "dark blue"},
        "roster": [
            {"teamId": HOME, "playerId": "h4", "jerseyNumber": 4},
            {"teamId": HOME, "playerId": "h7", "jerseyNumber": 7},
            {"teamId": HOME, "playerId": "h23", "jerseyNumber": 23},
            {"teamId": AWAY, "playerId": "a7", "jerseyNumber": 7},
            {"teamId": AWAY, "playerId": "a11", "jerseyNumber": 11},
            {"teamId": AWAY, "playerId": "a0"},
        ],
        "gymId": "gym-a",
        "court": "Court 1",
        "video": {"source": "clips/gym-a/test.mp4", "startSeconds": 0, "endSeconds": 2},
    }
    data.update(overrides)
    return Manifest.model_validate(data)


def ev(
    event_id: str,
    event_type: EventType,
    team: str,
    player: str | None,
    t: float = 1.0,
    status: EventStatus = "confirmed",
    related: str | None = None,
) -> Event:
    return Event(
        eventId=event_id,
        gameId="g1",
        eventType=event_type,
        timestampSeconds=t,
        teamId=team,
        playerId=player,
        eventConfidence=0.9,
        identityConfidence=0.9 if player else None,
        status=status,
        relatedEventId=related,
    )


def events_file(*events: Event) -> EventsFile:
    return EventsFile(gameId="g1", events=list(events))


requires_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None, reason="needs ffmpeg/ffprobe"
)


@pytest.fixture
def synthetic_video(tmp_path: Path) -> Path:
    """A 2-second 160x120 10 fps test pattern made by ffmpeg (no real footage)."""
    path = tmp_path / "test.mp4"
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=160x120:rate=10",
            "-t", "2", "-pix_fmt", "yuv420p", "-c:v", "libx264", str(path),
        ],
        check=True,
    )  # fmt: skip
    return path
