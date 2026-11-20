import pytest

from basketball_ai.evaluation import evaluate
from tests.conftest import AWAY, HOME, ev


def test_precision_recall_and_attribution() -> None:
    truth = [
        ev("t1", "fg2_made", HOME, "h4", 10.0),
        ev("t2", "fg3_made", AWAY, "a7", 20.0),
        ev("t3", "rebound_defensive", HOME, "h23", 30.0),
    ]
    predicted = [
        ev("p1", "fg2_made", HOME, "h4", 10.4),  # right
        ev("p2", "fg3_made", AWAY, "a11", 20.2),  # right event, wrong player
        ev("p3", "fg2_made", HOME, None, 50.0),  # no such event (false positive)
        ev("p4", "rebound_defensive", HOME, None, 30.5),  # right event, player left unknown
        ev("p5", "fg2_made", HOME, "h4", 10.6, status="rejected"),  # rejected predictions don't count
    ]
    report = evaluate(predicted, truth, tolerance_seconds=1.0)
    fg2 = report.byType["fg2_made"]
    assert (fg2.truePositives, fg2.falsePositives, fg2.falseNegatives) == (1, 1, 0)
    assert fg2.precision == 0.5 and fg2.recall == 1.0
    assert report.byType["fg3_made"].f1 == 1.0
    assert report.matched == 3 and report.team_accuracy == 1.0
    assert report.playerAttributed == 2 and report.playerCorrect == 1 and report.player_precision == 0.5
    assert report.unattributedPredictions == 1


def test_events_outside_the_time_tolerance_dont_match() -> None:
    report = evaluate([ev("p", "steal", HOME, "h4", 12.0)], [ev("t", "steal", HOME, "h4", 10.0)], 1.0)
    s = report.byType["steal"]
    assert (s.truePositives, s.falsePositives, s.falseNegatives) == (0, 1, 1)
    assert s.f1 == pytest.approx(0.0)
