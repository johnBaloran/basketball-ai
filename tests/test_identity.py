from basketball_ai.identity import IdentityConfig, JerseyObservation, player_registry, resolve_tracks
from tests.conftest import AWAY, HOME, make_manifest


def obs(
    track: str, numbers: list[int | None], team: str | None = HOME, conf: float = 0.9, start: int = 0
) -> list[JerseyObservation]:
    return [JerseyObservation(track, start + i, n, conf, team) for i, n in enumerate(numbers)]


def test_consistent_readings_resolve_to_the_roster_player() -> None:
    ids = resolve_tracks(obs("t1", [23, 23, 23, None, 23]), make_manifest())
    t = ids["t1"]
    assert t.status == "resolved" and t.playerId == "h23" and t.jerseyNumber == 23
    assert 0 < t.confidence <= 1


def test_too_few_or_weak_readings_stay_unresolved() -> None:
    m = make_manifest()
    assert resolve_tracks(obs("t1", [23, 23]), m)["t1"].status == "unresolved"
    assert resolve_tracks(obs("t1", [23, 23, 23, 23], conf=0.3), m)["t1"].status == "unresolved"


def test_disagreeing_readings_stay_unresolved() -> None:
    t = resolve_tracks(obs("t1", [23, 28, 23, 28, 23, 28]), make_manifest())["t1"]
    assert t.status == "unresolved" and "disagree" in t.reason


def test_number_not_on_roster_is_never_guessed() -> None:
    t = resolve_tracks(obs("t1", [99, 99, 99, 99]), make_manifest())["t1"]
    assert t.status == "unresolved" and t.playerId is None and "isn't on team" in t.reason


def test_shared_number_needs_the_team() -> None:
    m = make_manifest()
    assert resolve_tracks(obs("t1", [7, 7, 7, 7], team=None), m)["t1"].status == "unresolved"
    assert resolve_tracks(obs("t1", [7, 7, 7, 7], team=AWAY), m)["t1"].playerId == "a7"
    # #11 exists on one team only, so the team isn't needed
    assert resolve_tracks(obs("t1", [11, 11, 11], team=None), m)["t1"].playerId == "a11"


def test_two_overlapping_tracks_for_one_player_conflict() -> None:
    o = obs("t1", [4, 4, 4, 4], start=0) + obs("t2", [4, 4, 4, 4], start=2)
    ids = resolve_tracks(o, make_manifest())
    assert ids["t1"].status == ids["t2"].status == "conflict"
    assert player_registry(ids) == {}


def test_one_player_can_have_several_tracks_over_time() -> None:
    o = obs("t1", [4, 4, 4], start=0) + obs("t2", [4, 4, 4], start=100)
    ids = resolve_tracks(o, make_manifest())
    assert player_registry(ids) == {"h4": ["t1", "t2"]}


def test_thresholds_are_configurable() -> None:
    strict = IdentityConfig(min_readings=10)
    assert resolve_tracks(obs("t1", [4, 4, 4, 4]), make_manifest(), strict)["t1"].status == "unresolved"
