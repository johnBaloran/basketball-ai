import json
from pathlib import Path

from basketball_ai.dataset import assign_split, build, split_games


def _batch(tmp: Path, games: dict[str, str], per_game: int = 2) -> Path:
    """Synthetic batch: tiny fake image files and a frames.json (no real footage)."""
    batch = tmp / "batch"
    (batch / "images").mkdir(parents=True)
    frames = []
    for game, gym in games.items():
        for i in range(per_game):
            name = f"{gym}__{game}_c__{i:08d}.jpg"
            (batch / "images" / name).write_bytes(b"jpg")
            frames.append(
                {"file": name, "gym": gym, "clip": f"{game}_c.mp4", "game": game, "timestampSeconds": i}
            )
    (batch / "frames.json").write_text(
        json.dumps({"classes": ["player", "ball", "hoop", "referee"], "frames": frames})
    )
    return batch


def test_split_is_by_game_and_stable() -> None:
    assert assign_split("2026-11-14_g1") == assign_split("2026-11-14_g1")
    games = [f"2026-11-{d:02d}_g{d}" for d in range(1, 21)]
    splits = split_games(games)
    assert set(splits.values()) == {"train", "val", "test"}
    assert split_games([*games, "2026-12-01_g99"])["2026-11-01_g1"] == splits["2026-11-01_g1"]


def test_build_copies_by_split_and_writes_yaml_and_report(tmp_path: Path) -> None:
    games = {f"2026-11-{d:02d}_g{d}": ("gym-a" if d % 2 else "gym-b") for d in range(1, 11)}
    batch = _batch(tmp_path, games)
    labels = tmp_path / "export" / "obj_train_data"
    labels.mkdir(parents=True)
    for img in (batch / "images").iterdir():
        (labels / f"{img.stem}.txt").write_text(
            "0 0.5 0.5 0.1 0.3\n1 0.2 0.2 0.02 0.02\n2 0.9 0.2 0.05 0.05\n"
        )
    out = tmp_path / "datasets" / "v1"
    report = build([batch], tmp_path / "export", out)
    assert report.problems == []
    assert sum(report.frames.values()) == 20
    # Frames of one game never end up in two splits
    seen: dict[str, set[str]] = {}
    for split in ("train", "val", "test"):
        for img in (out / "images" / split).glob("*.jpg"):
            seen.setdefault(img.name.split("__")[1].rsplit("_c", 1)[0], set()).add(split)
    assert all(len(s) == 1 for s in seen.values())
    data = (out / "data.yaml").read_text()
    assert "train: images/train" in data and "  1: ball" in data
    assert json.loads((out / "report.json").read_text())["boxes"]["train"]["player"] > 0
    assert list(out.glob("data_test_*.yaml"))


def test_missing_and_bad_labels_are_problems(tmp_path: Path) -> None:
    batch = _batch(tmp_path, {"2026-11-01_g1": "gym-a"}, per_game=2)
    labels = tmp_path / "export"
    labels.mkdir()
    first = sorted((batch / "images").iterdir())[0]
    (labels / f"{first.stem}.txt").write_text("7 0.5 0.5 0.1 0.1\n")
    report = build([batch], labels, tmp_path / "out")
    assert any("no label file" in p for p in report.problems)
    assert any("class 7" in p for p in report.problems)
