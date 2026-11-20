import numpy as np

from basketball_ai.teams import fit_team_model, torso_color, vote_track_teams
from basketball_ai.tracking import Box


def test_torso_color_reads_the_shirt_not_the_shorts() -> None:
    frame = np.zeros((100, 40, 3), dtype=np.uint8)
    frame[20:50] = (250, 250, 250)  # white shirt
    frame[50:] = (10, 10, 10)  # dark shorts and floor
    color = torso_color(frame, Box(0, 0, 40, 100))
    assert color is not None and color.min() > 200


def test_two_colour_groups_are_named_from_hints() -> None:
    rng = np.random.default_rng(0)
    white = [np.array([235.0, 235, 235]) + rng.normal(0, 8, 3) for _ in range(6)]
    navy = [np.array([25.0, 35, 85]) + rng.normal(0, 8, 3) for _ in range(6)]
    model = fit_team_model(white + navy, ("home", "away"), hints=("dark blue", "white"))
    assert model.assign(np.array([230.0, 232, 228])) == "away"
    assert model.assign(np.array([20.0, 30, 90])) == "home"
    # A referee in bright orange is far from both teams
    assert model.assign(np.array([250.0, 120, 0])) is None


def test_track_team_is_a_vote() -> None:
    teams = vote_track_teams({"t1": ["home", "home", "home", None, "away"], "t2": ["home", "away"], "t3": [None]})
    assert teams == {"t1": "home", "t2": None, "t3": None}
