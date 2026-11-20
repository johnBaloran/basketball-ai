import json

import pytest
from pydantic import ValidationError

from basketball_ai.contracts import EventsFile, Manifest
from basketball_ai.schemas import SCHEMA_DIR, render
from tests.conftest import AWAY, HOME, ev, make_manifest


def test_valid_manifest_round_trips() -> None:
    m = make_manifest()
    assert Manifest.model_validate_json(m.model_dump_json()) == m
    player = m.player("h7")
    assert player is not None
    assert player.jerseyNumber == 7


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"roster": [{"teamId": "nope", "playerId": "x"}]}, "isn't in this game"),
        ({"roster": [{"teamId": HOME, "playerId": "x"}, {"teamId": AWAY, "playerId": "x"}]}, "more than once"),
        (
            {
                "roster": [
                    {"teamId": HOME, "playerId": "x", "jerseyNumber": 3},
                    {"teamId": HOME, "playerId": "y", "jerseyNumber": 3},
                ]
            },
            "used twice",
        ),
        ({"video": {"source": "c.mp4", "startSeconds": 5, "endSeconds": 4}}, "after startSeconds"),
        ({"awayTeam": {"id": HOME, "name": "Same"}}, "different teams"),
    ],
)
def test_bad_manifests_are_rejected(override: dict[str, object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        make_manifest(**override)


def test_same_number_on_different_teams_is_fine() -> None:
    assert make_manifest().player("a7") is not None


def test_unknown_fields_are_rejected() -> None:
    data = json.loads(make_manifest().model_dump_json())
    data["surprise"] = 1
    with pytest.raises(ValidationError):
        Manifest.model_validate(data)


def test_events_file_rejects_duplicates_and_other_games() -> None:
    e = ev("e1", "fg2_made", HOME, "h4")
    with pytest.raises(ValidationError, match="duplicate eventId"):
        EventsFile(gameId="g1", events=[e, e])
    with pytest.raises(ValidationError, match="belongs to game"):
        EventsFile(gameId="other", events=[e])


@pytest.mark.parametrize("name", ["manifest", "events", "boxscore"])
def test_committed_schemas_match_the_models(name: str) -> None:
    path = SCHEMA_DIR / f"{name}-0.1.json"
    assert path.exists(), f"run bball-schemas to create {path.name}"
    assert path.read_text(encoding="utf-8") == render(name), f"{path.name} is stale: run bball-schemas"
