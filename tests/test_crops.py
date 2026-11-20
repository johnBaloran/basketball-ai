import json
from pathlib import Path

import numpy as np

from basketball_ai.crops import collect, crop, jersey_region, select_crops
from basketball_ai.tracking import Box
from tests.conftest import make_manifest, requires_ffmpeg


def _row(frame: int, *tracks: tuple[str, str, Box]) -> dict[str, object]:
    return {
        "frame": frame,
        "tracks": [
            {"id": i, "label": label, "box": {"x1": b.x1, "y1": b.y1, "x2": b.x2, "y2": b.y2}}
            for i, label, b in tracks
        ],
    }


def test_jersey_region_is_the_upper_body() -> None:
    assert jersey_region(Box(0, 0, 10, 100)) == Box(0, 10, 10, 60)


def test_select_crops_samples_tracks_and_skips_small_or_non_players() -> None:
    big, small = Box(0, 0, 40, 150), Box(0, 0, 10, 30)
    rows = [_row(f, ("p1", "player", big), ("p2", "player", small), ("b1", "ball", big)) for f in range(25)]
    picks = select_crops(rows, every=10, min_height=120)
    assert sorted(picks) == [0, 10, 20]
    assert all(track == "p1" for frame in picks.values() for track, _ in frame)


def test_crop_clips_to_the_image() -> None:
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    piece = crop(image, Box(40, 40, 80, 80))
    assert piece is not None and piece.shape == (10, 10, 3)
    assert crop(image, Box(60, 60, 80, 80)) is None


@requires_ffmpeg
def test_collect_writes_crops_and_index(synthetic_video: Path, tmp_path: Path) -> None:
    tracks = tmp_path / "tracks.jsonl"
    rows = [_row(f, ("p1", "player", Box(10, 0, 70, 120))) for f in range(0, 20)]
    tracks.write_text("".join(json.dumps(r) + "\n" for r in rows))
    crops = collect(tracks, synthetic_video, make_manifest(), tmp_path / "crops", every=5, min_height=100)
    assert [c.frame for c in crops] == [0, 5, 10, 15]
    assert (tmp_path / "crops" / crops[0].file).exists()
    assert len(json.loads((tmp_path / "crops" / "crops.json").read_text())["crops"]) == 4
