import pytest

from basketball_ai.boxscore import check_invariants, compute_box_score, validate_events
from basketball_ai.contracts import Event, TeamBox
from tests.conftest import AWAY, HOME, ev, events_file, make_manifest


def _team(teams: list[TeamBox], team_id: str) -> TeamBox:
    return next(t for t in teams if t.teamId == team_id)


def test_points_rebounds_assists_and_unattributed_scores() -> None:
    m = make_manifest()
    events = events_file(
        ev("s1", "fg3_made", HOME, "h4", 1),
        ev("a1", "assist", HOME, "h7", 1, related="s1"),
        ev("s2", "fg2_missed", AWAY, "a11", 2),
        ev("r1", "rebound_defensive", HOME, "h23", 3, related="s2"),
        ev("s3", "ft_made", HOME, None, 4),  # shooter unknown: team still gets the point
        ev("s4", "fg2_made", AWAY, "a7", 5, status="pending_review"),  # not counted until confirmed
        ev("s5", "fg2_missed", AWAY, "a7", 6),
        ev("b1", "block", HOME, "h7", 6, related="s5"),
        ev("r2", "rebound_offensive", AWAY, "a11", 7, related="s5"),
    )
    box = compute_box_score(events, m)
    players = {p.playerId: p.stats for p in box.players}
    assert players["h4"].pts == 3 and players["h4"].fg3m == 1 and players["h4"].fg3a == 1
    assert players["h7"].ast == 1 and players["h7"].blk == 1
    assert players["h23"].dreb == 1 and players["h23"].reb == 1
    assert players["a11"].fga == 1 and players["a11"].oreb == 1
    home, away = _team(box.teams, HOME), _team(box.teams, AWAY)
    assert home.stats.pts == 4 and home.unattributed.pts == 1 and home.unattributed.ftm == 1
    assert away.stats.pts == 0 and away.stats.fga == 2
    assert "s4" not in box.countedEventIds
    assert check_invariants(box) == []


@pytest.mark.parametrize(
    ("events", "message"),
    [
        ([ev("x", "fg2_made", HOME, "ghost")], "isn't on the game roster"),
        ([ev("x", "fg2_made", AWAY, "h4")], "plays for"),
        ([ev("x", "fg2_made", "team-other", None)], "isn't in this game"),
        ([ev("a", "assist", HOME, "h7")], "must reference the shot"),
        ([ev("s", "fg2_missed", HOME, "h4"), ev("a", "assist", HOME, "h7", related="s")], "can't relate"),
        ([ev("s", "fg2_made", HOME, "h4"), ev("a", "assist", HOME, "h4", related="s")], "own basket"),
        ([ev("s", "fg2_made", HOME, "h4"), ev("a", "assist", AWAY, "a7", related="s")], "shooting team"),
        ([ev("s", "fg2_missed", HOME, "h4"), ev("b", "block", HOME, "h7", related="s")], "defending team"),
        (
            [ev("s", "fg3_missed", HOME, "h4"), ev("r", "rebound_defensive", HOME, "h7", related="s")],
            "defending team",
        ),
        (
            [
                ev("s", "fg2_made", HOME, "h4", status="pending_review"),
                ev("a", "assist", HOME, "h7", related="s"),
            ],
            "isn't confirmed",
        ),
    ],
)
def test_impossible_events_are_caught(events: list[Event], message: str) -> None:
    problems = validate_events(events_file(*events), make_manifest())
    assert any(message in p for p in problems), problems
    with pytest.raises(ValueError, match="failed validation"):
        compute_box_score(events_file(*events), make_manifest())


def test_rejected_and_unresolved_events_never_count() -> None:
    box = compute_box_score(
        events_file(
            ev("s1", "fg2_made", HOME, "h4", status="rejected"),
            ev("s2", "fg2_made", HOME, None, status="unresolved"),
        ),
        make_manifest(),
    )
    assert box.countedEventIds == []
    assert _team(box.teams, HOME).stats.pts == 0


def test_recomputing_is_idempotent() -> None:
    events = events_file(ev("s1", "fg2_made", HOME, "h4"), ev("s2", "ft_made", HOME, "h4", 2))
    assert compute_box_score(events, make_manifest()) == compute_box_score(events, make_manifest())
