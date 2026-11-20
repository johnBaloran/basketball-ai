from basketball_ai.labels import CLASSES, game_group, parse_label_file, to_yolo


def test_pixel_box_to_yolo_and_back_to_text() -> None:
    box = to_yolo(CLASSES.index("ball"), 90, 40, 110, 60, 200, 100)
    assert box is not None
    assert box.line() == "1 0.500000 0.500000 0.100000 0.200000"
    assert to_yolo(0, -50, -50, -10, -10, 200, 100) is None  # entirely outside the image


def test_label_file_problems_are_reported() -> None:
    boxes, problems = parse_label_file("0 0.5 0.5 0.1 0.2\n9 0.5 0.5 0.1 0.1\n0 1.5 0.5 0.1 0.1\nbad\n\n")
    assert len(boxes) == 1
    assert [p.split(":")[0] for p in problems] == ["line 2", "line 3", "line 4"]


def test_game_group_from_clip_names() -> None:
    assert game_group("2026-11-14_g123_0612-0655") == "2026-11-14_g123"
    assert game_group("2026-11-14_g123_0700-0745") == "2026-11-14_g123"
    assert game_group("random-clip") == "random-clip"
