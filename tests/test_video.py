from pathlib import Path

import pytest

from basketball_ai.inventory import fingerprint, scan, summarize
from basketball_ai.video import VideoError, cut_clip, iter_frames, probe
from tests.conftest import requires_ffmpeg


@requires_ffmpeg
def test_probe_reads_metadata(synthetic_video: Path) -> None:
    info = probe(synthetic_video)
    assert (info.width, info.height, info.fps, info.codec) == (160, 120, 10.0, "h264")
    assert 1.9 <= info.durationSeconds <= 2.1
    assert not info.hasAudio


@requires_ffmpeg
def test_frames_stream_with_sampling_and_ranges(synthetic_video: Path) -> None:
    frames = list(iter_frames(synthetic_video))
    assert len(frames) == 20 and frames[0].image.shape == (120, 160, 3)
    sampled = list(iter_frames(synthetic_video, every_n=5))
    assert [f.index for f in sampled] == [0, 5, 10, 15]
    window = list(iter_frames(synthetic_video, start_seconds=1.0, end_seconds=1.5))
    assert 4 <= len(window) <= 6 and window[0].timestampSeconds == 1.0


@requires_ffmpeg
def test_cut_clip(synthetic_video: Path, tmp_path: Path) -> None:
    info = cut_clip(synthetic_video, tmp_path / "out" / "clip.mp4", 0.5, 1.5)
    assert 0.9 <= info.durationSeconds <= 1.1 and not info.hasAudio
    with pytest.raises(ValueError):
        cut_clip(synthetic_video, tmp_path / "bad.mp4", 2, 1)


@requires_ffmpeg
def test_probe_rejects_non_video(tmp_path: Path) -> None:
    bad = tmp_path / "not-a-video.mp4"
    bad.write_bytes(b"nope")
    with pytest.raises(VideoError):
        probe(bad)


@requires_ffmpeg
def test_inventory_records_gym_date_and_issues(synthetic_video: Path, tmp_path: Path) -> None:
    root = tmp_path / "raw"
    (root / "gym-a").mkdir(parents=True)
    target = root / "gym-a" / "2026-11-14_game.mp4"
    target.write_bytes(synthetic_video.read_bytes())
    (root / "gym-a" / "broken.mp4").write_bytes(b"x")
    records = {r.source: r for r in scan(root)}
    good = records["gym-a/2026-11-14_game.mp4"]
    assert good.gymId == "gym-a" and good.recordingDate == "2026-11-14" and good.width == 160
    assert any("below 1080p" in i for i in good.knownIssues)
    assert any("unreadable" in i for i in records["gym-a/broken.mp4"].knownIssues)
    assert good.videoId == fingerprint(target) and good.videoId.startswith("vid_")
    assert summarize(list(records.values()))["gym-a"]["videos"] == 2
