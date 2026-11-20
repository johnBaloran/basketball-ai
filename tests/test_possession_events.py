from basketball_ai.possession_events import classify_changes
from basketball_ai.tracking import PossessionSegment

TEAMS: dict[str, str | None] = {"h1": "home", "h2": "home", "a1": "away", "x": None}


def seg(track: str, start: int, end: int) -> PossessionSegment:
    return PossessionSegment(track, start, end)


def test_pass_steal_and_rebound_candidates() -> None:
    segments = [seg("h1", 0, 20), seg("h2", 30, 60), seg("a1", 70, 90), seg("h1", 200, 230)]
    changes = classify_changes(segments, TEAMS, missed_shot_frames=[150])
    assert [c.kind for c in changes] == ["pass", "steal_candidate", "rebound_candidate"]
    assert changes[2].atFrame == 200


def test_unknown_team_is_not_guessed() -> None:
    (change,) = classify_changes([seg("h1", 0, 10), seg("x", 20, 30)], TEAMS)
    assert change.kind == "unknown"


def test_old_misses_dont_make_a_rebound() -> None:
    (change,) = classify_changes([seg("h1", 0, 500), seg("a1", 600, 650)], TEAMS, [100], rebound_window=90)
    assert change.kind == "steal_candidate"
