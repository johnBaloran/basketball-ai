import json
from pathlib import Path

from basketball_ai.pipeline import draw_boxes, run_clip
from basketball_ai.tracking import Box, Detection, TrackedBox
from basketball_ai.video import Frame, probe
from tests.conftest import make_manifest, requires_ffmpeg


class FakeDetector:
    """A player that keeps the ball for the whole clip (synthetic; no model)."""

    def detect(self, frame: Frame) -> list[Detection]:
        return [
            Detection("player", Box(10, 10, 60, 110), 0.9),
            Detection("ball", Box(50, 50, 58, 58), 0.8),
            Detection("player", Box(100, 10, 150, 110), 0.9),
        ]


def test_draw_boxes_outlines_without_touching_the_input() -> None:
    import numpy as np

    frame = np.zeros((40, 40, 3), dtype=np.uint8)
    out = draw_boxes(frame, [TrackedBox("p1", "player", Box(5, 5, 30, 30), 0.9)], thickness=1)
    assert frame.sum() == 0 and out[5, 10].tolist() == [0, 200, 255] and out[15, 15].sum() == 0


@requires_ffmpeg
def test_run_clip_writes_tracks_possession_and_video(synthetic_video: Path, tmp_path: Path) -> None:
    out = tmp_path / "outputs" / "g1"
    result = run_clip(make_manifest(), FakeDetector(), out, synthetic_video, every_n=2)
    assert result.framesProcessed == 10 and result.tracks == 3
    lines = (out / "tracks.jsonl").read_text().splitlines()
    assert len(lines) == 10 and len(json.loads(lines[0])["tracks"]) == 3
    possession = json.loads((out / "possession.json").read_text())
    assert [s["trackId"] for s in possession["segments"]] == ["p1"] and possession["changes"] == []
    assert probe(out / "annotated.mp4").width == 160
