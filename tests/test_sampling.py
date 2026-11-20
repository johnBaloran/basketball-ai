import json
import shutil
import zipfile
from pathlib import Path

import numpy as np

from basketball_ai.sampling import find_clips, is_new, run, thumbnail
from basketball_ai.tracking import Box, Detection
from basketball_ai.video import Frame
from tests.conftest import requires_ffmpeg


class FakeDetector:
    def detect(self, frame: Frame) -> list[Detection]:
        return [Detection("player", Box(10, 10, 50, 100), 0.9), Detection("ball", Box(60, 60, 66, 66), 0.7)]


def test_near_duplicate_frames_are_skipped() -> None:
    a = np.zeros((90, 160, 3), dtype=np.uint8)
    b = a.copy()
    b[:, :80] = 200
    ta, tb = thumbnail(a), thumbnail(b)
    assert not is_new(ta, [ta], 6.0)
    assert is_new(tb, [ta], 6.0)


@requires_ffmpeg
def test_frames_are_picked_per_clip_with_prelabels(synthetic_video: Path, tmp_path: Path) -> None:
    clips = tmp_path / "clips"
    (clips / "gym-a").mkdir(parents=True)
    shutil.copy(synthetic_video, clips / "gym-a" / "2026-11-14_g1_0000-0002.mp4")
    out = tmp_path / "batch"
    frames = run(find_clips(clips), out, every_seconds=0.5, max_per_clip=3, detector=FakeDetector())
    assert 1 <= len(frames) <= 3
    f = frames[0]
    assert f.gym == "gym-a" and f.game == "2026-11-14_g1" and (out / "images" / f.file).exists()
    meta = json.loads((out / "frames.json").read_text())
    assert meta["classes"] == ["player", "ball", "hoop", "referee"] and len(meta["frames"]) == len(frames)
    with zipfile.ZipFile(out / "prelabels_yolo.zip") as z:
        names = set(z.namelist())
        assert {"obj.names", "obj.data", "train.txt"} <= names
        label = z.read(f"obj_train_data/{Path(f.file).stem}.txt").decode()
    assert [line.split()[0] for line in label.splitlines()] == ["0", "1"]
