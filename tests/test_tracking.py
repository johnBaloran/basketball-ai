from basketball_ai.tracking import (
    Box,
    Detection,
    IouTracker,
    TrackedBox,
    holder_in_frame,
    possession_changes,
    possession_segments,
)


def test_box_geometry() -> None:
    a, b = Box(0, 0, 10, 10), Box(5, 5, 15, 15)
    assert a.center == (5, 5) and a.area == 100
    assert round(a.iou(b), 4) == round(25 / 175, 4)
    assert a.expanded(0.1).contains((10.5, 10.5))


def test_tracker_keeps_ids_while_objects_move() -> None:
    tr = IouTracker()
    first = tr.update(
        [Detection("player", Box(0, 0, 10, 20), 0.9), Detection("ball", Box(50, 50, 54, 54), 0.8)]
    )
    moved = tr.update(
        [Detection("player", Box(1, 0, 11, 20), 0.9), Detection("ball", Box(51, 50, 55, 54), 0.8)]
    )
    assert {t.trackId for t in first} == {t.trackId for t in moved}


def test_tracker_starts_new_track_for_new_object_and_drops_lost_ones() -> None:
    tr = IouTracker(max_missed=1)
    (a,) = tr.update([Detection("player", Box(0, 0, 10, 20), 0.9)])
    tr.update([])
    tr.update([])
    (b,) = tr.update([Detection("player", Box(0, 0, 10, 20), 0.9)])
    assert a.trackId != b.trackId


def test_holder_is_the_player_with_the_ball() -> None:
    p1 = TrackedBox("p1", "player", Box(0, 0, 10, 20), 0.9)
    p2 = TrackedBox("p2", "player", Box(30, 0, 40, 20), 0.9)
    ball = TrackedBox("b1", "ball", Box(8, 8, 10, 10), 0.8)
    assert holder_in_frame([p1, p2], ball) == "p1"
    assert holder_in_frame([p1, p2], None) is None
    assert holder_in_frame([p1, p2], TrackedBox("b1", "ball", Box(20, 50, 22, 52), 0.8)) is None


def test_possession_ignores_flickers_and_reports_changes() -> None:
    holders: list[str | None] = ["p1"] * 6 + ["p2"] * 2 + ["p1"] * 3 + [None] * 4 + ["p3"] * 5
    segments = possession_segments(holders, min_frames=5)
    assert [(s.trackId, s.startFrame, s.endFrame) for s in segments] == [("p1", 0, 5), ("p3", 15, 19)]
    assert [(a.trackId, b.trackId) for a, b in possession_changes(segments)] == [("p1", "p3")]
